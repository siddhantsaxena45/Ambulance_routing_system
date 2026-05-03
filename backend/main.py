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
    hospitals = get_hospitals(G, num_hospitals=100)
    
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
    
    import random
    # Randomize traffic and blockages
    for u, v, k, data in G.edges(keys=True, data=True):
        data['traffic'] = random.choice([0, 1, 2])
        data['blocked'] = random.random() < 0.05
        
    for h in hospitals:
        h['capacity_load'] = random.choice([0, 1, 2])
        
    return {"status": "success", "hospitals": hospitals}

@app.post("/run_ga")
def run_ga(req: RouteRequest):
    global G, hospitals
    if G is None:
        return {"error": "Map not loaded"}
        
    ga = AmbulanceGA(G, hospitals, req.start_node, req.urgency, pop_size=20, generations=30, mutation_rate=0.2)
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
        "convergence": convergence
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
        t = data.get('traffic', 1)
        if data.get('blocked', False):
            total_time += 600
        else:
            time, cong = ann_model.predict(l, t)
            total_time += time
            total_congestion += cong
            
    avg_congestion = total_congestion / max(1, len(best_path)-1)
    
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
        "hospital": best_h
    }
