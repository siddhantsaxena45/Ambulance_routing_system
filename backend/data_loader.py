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
        # Ensure graph is strongly connected for routing
        G = ox.truncate.largest_component(G, strongly=True)
        ox.save_graphml(G, GRAPH_FILE)
    
    # Add base traffic data (simulated)
    # Traffic levels: 0 (low), 1 (medium), 2 (high)
    for u, v, k, data in G.edges(keys=True, data=True):
        data['traffic'] = random.choice([0, 1, 2])
        data['blocked'] = random.random() < 0.05 # 5% chance of blockage
        if 'length' not in data:
            data['length'] = 10.0 # default 10m if missing
            
    return G

def get_hospitals(G, num_hospitals=5):
    import osmnx as ox
    try:
        print("Fetching real hospitals from OSM...")
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
                'node': node_id,
                'capacity_load': random.choice([0, 1, 2]),
                'name': name,
                'coords': {'lat': node_data['y'], 'lon': node_data['x']}
            })
            count += 1
            
        if len(hospitals) == 0:
            raise ValueError("No hospitals found.")
            
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
