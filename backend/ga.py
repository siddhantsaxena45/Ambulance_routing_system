import random
import networkx as nx
from ann import ann_model
from fuzzy import fuzzy_system

class AmbulanceGA:
    def __init__(self, G, hospitals, start_node, urgency, pop_size=20, generations=50, mutation_rate=0.2):
        self.G = G
        self.hospitals = hospitals # List of dicts: {'node': id, 'capacity_load': 0/1/2}
        self.start_node = start_node
        self.urgency = urgency
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        
        self.population = []
        
    def _generate_random_path(self, target_node):
        try:
            # We use A* to find a base path, then introduce random deviations (not truly random walk to avoid infinite loops)
            # A simpler way to generate diverse paths is to randomly perturb edge weights and run shortest_path
            temp_G = self.G.copy()
            for u, v, k, d in temp_G.edges(keys=True, data=True):
                d['temp_weight'] = d.get('length', 10) * random.uniform(0.5, 2.0)
            
            path = nx.shortest_path(temp_G, source=self.start_node, target=target_node, weight='temp_weight')
            return path
        except nx.NetworkXNoPath:
            return None

    def initialize_population(self):
        self.population = []
        hospital_nodes = [h['node'] for h in self.hospitals]
        
        while len(self.population) < self.pop_size:
            target = random.choice(self.hospitals)
            path = self._generate_random_path(target['node'])
            if path:
                self.population.append({
                    'path': path,
                    'hospital': target
                })

    def evaluate_fitness(self, chromosome):
        path = chromosome['path']
        hospital = chromosome['hospital']
        
        total_time = 0
        total_congestion = 0
        total_distance = 0
        
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            # Get edge data (taking first parallel edge if multigraph)
            edge_data = self.G.get_edge_data(u, v)
            if edge_data:
                k = list(edge_data.keys())[0]
                data = edge_data[k]
                
                length = data.get('length', 10.0)
                traffic = data.get('traffic', 1)
                
                total_distance += length
                
                # If road is blocked, heavy penalty (10 mins)
                if data.get('blocked', False):
                    total_time += 600
                else:
                    time, congestion = ann_model.predict(length, traffic)
                    total_time += time
                    total_congestion += congestion
                    
        avg_congestion = total_congestion / max(1, len(path)-1)
        
        # Fuzzy Logic Penalty based on average congestion, urgency, and hospital load
        fuzzy_penalty = fuzzy_system.compute_penalty(avg_congestion, self.urgency, hospital['capacity_load'])
        
        # Cost function: we want to minimize time and penalty
        # Combine them into a single cost. (Time is in seconds, Penalty is 0-100)
        # Assuming penalty scales time proportionally
        cost = total_time * (1 + fuzzy_penalty / 100.0)
        
        # Fitness is inverse of cost
        return 1.0 / (cost + 1e-6), cost, total_time, avg_congestion, total_distance

    def crossover(self, parent1, parent2):
        path1 = parent1['path']
        path2 = parent2['path']
        
        # Find common nodes (excluding start node)
        common_nodes = set(path1[1:]) & set(path2[1:])
        
        if not common_nodes:
            return parent1, parent2 # No crossover possible, return parents
            
        cross_point = random.choice(list(common_nodes))
        
        idx1 = path1.index(cross_point)
        idx2 = path2.index(cross_point)
        
        child1_path = path1[:idx1] + path2[idx2:]
        child2_path = path2[:idx2] + path1[idx1:]
        
        child1 = {'path': child1_path, 'hospital': parent2['hospital']}
        child2 = {'path': child2_path, 'hospital': parent1['hospital']}
        
        return child1, child2

    def mutate(self, chromosome):
        if random.random() > self.mutation_rate:
            return chromosome
            
        path = chromosome['path']
        hospital = chromosome['hospital']
        
        if len(path) <= 2:
            return chromosome
            
        # Pick a random intermediate node to mutate from
        mutate_idx = random.randint(1, len(path)-2)
        mutate_node = path[mutate_idx]
        
        # Find a new sub-path from mutate_node to hospital
        try:
            temp_G = self.G.copy()
            for u, v, k, d in temp_G.edges(keys=True, data=True):
                d['temp_weight'] = d.get('length', 10) * random.uniform(0.5, 3.0)
            
            sub_path = nx.shortest_path(temp_G, source=mutate_node, target=hospital['node'], weight='temp_weight')
            
            new_path = path[:mutate_idx] + sub_path
            return {'path': new_path, 'hospital': hospital}
        except nx.NetworkXNoPath:
            return chromosome

    def run(self):
        self.initialize_population()
        
        best_overall = None
        best_cost = float('inf')
        convergence_data = []
        
        for gen in range(self.generations):
            # Evaluate fitness
            evaluated = []
            for chromo in self.population:
                fitness, cost, time, cong, dist = self.evaluate_fitness(chromo)
                evaluated.append((chromo, fitness, cost, time, cong, dist))
                
                if cost < best_cost:
                    best_cost = cost
                    best_overall = {
                        'path': chromo['path'],
                        'hospital': chromo['hospital'],
                        'cost': cost,
                        'time': time,
                        'congestion': cong,
                        'distance': dist
                    }
                    
            convergence_data.append(best_cost)
            
            # Selection (Tournament)
            new_population = []
            while len(new_population) < self.pop_size:
                # Select 2 participants
                p1 = random.choice(evaluated)
                p2 = random.choice(evaluated)
                parent1 = p1[0] if p1[1] > p2[1] else p2[0]
                
                p3 = random.choice(evaluated)
                p4 = random.choice(evaluated)
                parent2 = p3[0] if p3[1] > p4[1] else p4[0]
                
                # Crossover
                if random.random() < 0.8:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                    
                # Mutation
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                new_population.extend([child1, child2])
                
            # Keep population size constant
            self.population = new_population[:self.pop_size]
            
        return best_overall, convergence_data
