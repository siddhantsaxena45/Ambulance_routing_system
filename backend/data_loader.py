import osmnx as ox
import networkx as nx
import random
import os

GRAPH_FILE = "noida_10km_graph.graphml"
CITY_QUERY = "Noida Sector 62, UP, India"

def get_or_create_graph():
    if os.path.exists(GRAPH_FILE):
        print("Loading graph from disk...")
        G = ox.load_graphml(GRAPH_FILE)
    else:
        print(f"Downloading graph for {CITY_QUERY}...")
        G = ox.graph_from_address(CITY_QUERY, dist=10000, network_type="drive")
        G = ox.truncate.largest_component(G, strongly=True)
        ox.save_graphml(G, GRAPH_FILE)
    
    # ROAD HIERARCHY MAPPING (for ANN features)
    # 0=Motorway, 1=Trunk, 2=Primary, 3=Secondary, 4=Tertiary, 5=Residential, 6=Others
    hierarchy = {
        'motorway': 0, 'trunk': 1, 'primary': 2, 'secondary': 3,
        'tertiary': 4, 'residential': 5, 'living_street': 5, 'service': 6
    }

    # Normalize Metadata and Add realistic traffic
    for u, v, k, data in G.edges(keys=True, data=True):
        # 1. Parse Max Speed
        raw_speed = data.get('maxspeed', '40')
        if isinstance(raw_speed, list): raw_speed = raw_speed[0]
        try:
            # Extract numeric part (handles "40 km/h" or "30 mph")
            speed = int(''.join(filter(str.isdigit, str(raw_speed))))
        except:
            speed = 40
        data['speed_kph'] = speed
        
        # 2. Parse Lanes
        raw_lanes = data.get('lanes', '1')
        if isinstance(raw_lanes, list): raw_lanes = raw_lanes[0]
        try:
            lanes = int(raw_lanes)
        except:
            lanes = 1
        data['lanes_count'] = lanes
        
        # 3. Road Rank
        h_type = data.get('highway', 'unclassified')
        if isinstance(h_type, list): h_type = h_type[0]
        data['road_rank'] = hierarchy.get(h_type, 6)
        
        # 4. Realistic Traffic Density (Deterministic based on rank + some time-of-day simulation)
        # Major roads (rank 0-2) have higher base density (0.4-0.8)
        # Minor roads have lower base density (0.1-0.3)
        base_density = 0.6 if data['road_rank'] <= 2 else 0.2
        data['traffic_density'] = min(1.0, base_density + random.uniform(-0.2, 0.2))
        
        # 5. Blockages (Real-world incidents are rare but high impact)
        data['blocked'] = random.random() < 0.02 # 2% chance of blockage
        
        if 'length' not in data:
            data['length'] = 10.0
            
    return G

def get_hospitals(G, num_hospitals=5):
    import osmnx as ox
    import json
    
    HOSPITALS_CACHE_FILE = "hospitals_10km_cache.json"
    
    # Try loading from cache first
    if os.path.exists(HOSPITALS_CACHE_FILE):
        print("Loading hospitals from local cache (FAST)...")
        with open(HOSPITALS_CACHE_FILE, 'r') as f:
            cached_hospitals = json.load(f)
            # Assign fresh random loads
            for h in cached_hospitals:
                h['capacity_load'] = random.choice([0, 1, 2])
            return cached_hospitals[:num_hospitals]

    try:
        print("Fetching real hospitals from OSM (takes a minute)...")
        tags = {'amenity': 'hospital'}
        hospitals_gdf = ox.features_from_address(CITY_QUERY, tags=tags, dist=10000)
        hospitals_gdf = hospitals_gdf.to_crs(epsg=4326)
        
        hospitals = []
        count = 0
        for idx, row in hospitals_gdf.iterrows():
            if count >= num_hospitals:
                break
                
            name = row.get('name', f"Unnamed Hospital {count+1}")
            if not isinstance(name, str):
                name = f"Unnamed Hospital {count+1}"
                
            centroid = row.geometry.centroid if hasattr(row.geometry, 'centroid') else row.geometry
            node_id = ox.nearest_nodes(G, X=centroid.x, Y=centroid.y)
            node_data = G.nodes[node_id]
            
            hospitals.append({
                'id': f"H{count+1}",
                'node': int(node_id),
                'capacity_load': random.choice([0, 1, 2]),
                'name': name,
                'coords': {'lat': float(node_data['y']), 'lon': float(node_data['x'])}
            })
            count += 1
            
        if len(hospitals) == 0:
            raise ValueError("No hospitals found.")
            
        # Save to cache so next restart is instant
        with open(HOSPITALS_CACHE_FILE, 'w') as f:
            json.dump(hospitals, f)
            
        return hospitals
    except Exception as e:
        print(f"Error fetching OSM hospitals: {e}. Falling back to random nodes.")
        nodes = list(G.nodes())
        random.seed(101)
        hospital_nodes = random.sample(nodes, num_hospitals)
        hospital_names = ["Fortis Hospital", "Kailash Hospital", "Max Super Speciality", "Apollo Spectra", "Jaypee Hospital"]
        
        hospitals = []
        for idx, h_node in enumerate(hospital_nodes):
            node_data = G.nodes[h_node]
            hospitals.append({
                'id': f"H{idx+1}",
                'node': h_node,
                'capacity_load': random.choice([0, 1, 2]),
                'name': hospital_names[idx % len(hospital_names)],
                'coords': {'lat': node_data['y'], 'lon': node_data['x']}
            })
        return hospitals
