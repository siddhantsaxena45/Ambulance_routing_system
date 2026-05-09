from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx

from data_loader import get_or_create_graph, get_hospitals
from ga import AmbulanceGA

app = FastAPI(title="Ambulance Routing API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
G = None
hospitals = []

class RouteRequest(BaseModel):
    start_node: int
    urgency: int # 0-10

@app.get("/nearest_node")
def nearest_node(lat: float, lon: float):
    global G
    if G is None:
        return {"error": "Map not loaded"}
    
    import osmnx as ox
    node_id = ox.nearest_nodes(G, X=lon, Y=lat)
    node_data = G.nodes[node_id]
    
    return {
        "status": "success",
        "node": int(node_id),
        "coords": {"lat": node_data['y'], "lon": node_data['x']}
    }

@app.get("/load_map")
def load_map():
    global G, hospitals
    G = get_or_create_graph()
    hospitals = get_hospitals(G, num_hospitals=300)
    
    # Calculate visual center of the map
    lats = [data['y'] for node, data in G.nodes(data=True)]
    lons = [data['x'] for node, data in G.nodes(data=True)]
    center_lat = (max(lats) + min(lats)) / 2
    center_lon = (max(lons) + min(lons)) / 2
    
    sample_start = list(G.nodes())[0]
    
    return {
        "status": "success",
        "map_center": {"lat": center_lat, "lon": center_lon},
        "sample_start_node": sample_start,
        "sample_coords": {"lat": G.nodes[sample_start]['y'], "lon": G.nodes[sample_start]['x']},
        "hospitals": hospitals
    }

@app.get("/simulate_data")
def simulate_data():
    global G, hospitals
    if G is None:
        return {"error": "Map not loaded"}
    
    # Re-randomize traffic based on realistic baselines
    for u, v, k, data in G.edges(keys=True, data=True):
        # Base density from road rank
        rank = data.get('road_rank', 6)
        base = 0.6 if rank <= 2 else 0.2
        data['traffic_density'] = min(1.0, base + random.uniform(-0.2, 0.4))
        data['blocked'] = random.random() < 0.02
        
    for h in hospitals:
        h['capacity_load'] = random.choice([0, 1, 2])
        
    return {"status": "success", "hospitals": hospitals}

@app.post("/run_ga")
def run_ga(req: RouteRequest):
    global G, hospitals
    if G is None:
        return {"error": "Map not loaded"}
        
    ga = AmbulanceGA(G, hospitals, req.start_node, req.urgency, pop_size=60, generations=40, mutation_rate=0.2)
    best_route, convergence = ga.run()
    
    if not best_route:
        return {"error": "No valid route found"}
        
    # Extract coordinates for frontend
    coords = []
    for node in best_route['path']:
        node_data = G.nodes[node]
        coords.append([node_data['y'], node_data['x']]) # Lat, Lon for Leaflet
        
    return {
        "path": best_route['path'],
        "coords": coords,
        "hospital": best_route['hospital'],
        "cost": best_route['cost'],
        "time_seconds": best_route['time'],
        "congestion_score": best_route['congestion'],
        "distance": best_route.get('distance', 0),
        "convergence": convergence,
        "breakdown": best_route.get('breakdown')
    }

@app.post("/baseline_route")
def baseline_route(req: RouteRequest):
    global G, hospitals
    if G is None:
        return {"error": "Map not loaded"}
        
    # Baseline uses simple shortest path by length (Dijkstra)
    best_path = None
    best_dist = float('inf')
    best_h = None
    
    for h in hospitals:
        try:
            length, path = nx.single_source_dijkstra(G, source=req.start_node, target=h['node'], weight='length')
            if length < best_dist:
                best_dist = length
                best_path = path
                best_h = h
        except nx.NetworkXNoPath:
            continue
            
    if not best_path:
        return {"error": "No valid route found"}
        
    # Calculate simulated time and congestion for the baseline
    from ann import ann_model
    total_time = 0
    total_congestion = 0
    for i in range(len(best_path) - 1):
        u = best_path[i]
        v = best_path[i+1]
        edge_data = G.get_edge_data(u, v)
        k = list(edge_data.keys())[0]
        data = edge_data[k]
        
        l = data.get('length', 10.0)
        s = data.get('speed_kph', 40)
        ln = data.get('lanes_count', 1)
        r = data.get('road_rank', 6)
        d = data.get('traffic_density', 0.2)

        if data.get('blocked', False):
            total_time += 600
        else:
            time, cong = ann_model.predict(l, s, ln, r, d)
            total_time += time
            total_congestion += cong
            
    avg_congestion = total_congestion / max(1, len(best_path)-1)
    
    # Calculate Breakdown for Baseline
    from fuzzy import fuzzy_system
    baseline_raw_time = 0
    baseline_blocked_count = 0
    for i in range(len(best_path) - 1):
        u = best_path[i]
        v = best_path[i+1]
        d = G.get_edge_data(u, v)
        k = list(d.keys())[0]
        l = d[k].get('length', 10.0)
        s = d[k].get('speed_kph', 40)
        baseline_raw_time += (l / (s / 3.6))
        if d[k].get('blocked', False):
            baseline_blocked_count += 1
        
    penalty_val = fuzzy_system.compute_penalty(avg_congestion, req.urgency, best_h['capacity_load'])
    penalty_seconds = total_time * (penalty_val / 100.0)
    total_effective_cost = total_time + penalty_seconds
    
    baseline_avg_speed = (best_dist / max(1, total_time)) * 3.6
    baseline_survival = 100 - (max(0, (total_effective_cost/60) - 10) * (req.urgency / 2.0))
    baseline_survival = max(5, min(99, baseline_survival))

    breakdown = {
        "raw_time_min": baseline_raw_time / 60.0,
        "traffic_delay_min": (total_time - baseline_raw_time) / 60.0,
        "hospital_penalty_min": penalty_seconds / 60.0,
        "total_effective_time": total_effective_cost / 60.0,
        "blocked_incidents": baseline_blocked_count,
        "avg_speed_kph": baseline_avg_speed,
        "survival_probability": baseline_survival,
        "patient_condition": "Critical" if req.urgency > 7 else "Urgent" if req.urgency > 4 else "Stable"
    }
    
    coords = []
    for node in best_path:
        node_data = G.nodes[node]
        coords.append([node_data['y'], node_data['x']])
        
    return {
        "status": "success",
        "coords": coords,
        "time_seconds": total_time,
        "congestion_score": avg_congestion,
        "distance": best_dist,
        "hospital": best_h,
        "breakdown": breakdown
    }
