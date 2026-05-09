import random
import networkx as nx
from ann import ann_model
from fuzzy import fuzzy_system

class AmbulanceGA:
    def __init__(self, G, hospitals, start_node, urgency, pop_size=50, generations=30, mutation_rate=0.3):
        self.G = G
        self.hospitals = hospitals 
        self.start_node = start_node
        self.urgency = urgency
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.base_mutation_rate = mutation_rate
        
        self.population = []
        
    def _generate_random_path(self, target_node):
        try:
            # Efficiently generate a "randomized" shortest path by using a weight function
            # instead of copying the whole graph.
            def noisy_weight(u, v, d):
                return d.get('length', 10.0) * random.uniform(0.5, 2.5)
            
            path = nx.shortest_path(self.G, source=self.start_node, target=target_node, weight=noisy_weight)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def initialize_population(self):
        self.population = []
        
        # 1. Always include the absolute shortest path to a few nearby hospitals
        # Sort hospitals by distance roughly (optional, but let's keep it simple)
        # For now, just pick 10 random hospitals and include their shortest paths
        initial_targets = random.sample(self.hospitals, min(len(self.hospitals), 10))
        for h in initial_targets:
            try:
                path = nx.shortest_path(self.G, source=self.start_node, target=h['node'], weight='length')
                self.population.append({'path': path, 'hospital': h})
            except:
                continue

        # 2. Fill remaining with random paths to random hospitals
        # This ensures wide spatial coverage
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
        
        is_valid = True
        total_time = 0
        total_congestion = 0
        total_distance = 0
        raw_time = 0 
        blocked_count = 0
        
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            
            try:
                edge_data = self.G.get_edge_data(u, v)
                if not edge_data:
                    total_time += 1000
                    is_valid = False
                    continue
                
                if 'length' in edge_data:
                    data = edge_data
                else:
                    data = next(iter(edge_data.values()))
            except:
                total_time += 1000
                is_valid = False
                continue
            
            length = data.get('length', 10.0)
            max_speed = data.get('speed_kph', 40)
            lanes = data.get('lanes_count', 1)
            road_rank = data.get('road_rank', 6)
            traffic_density = data.get('traffic_density', 0.2)
            
            total_distance += length
            raw_time += (length / (max_speed / 3.6))
            
            if data.get('blocked', False):
                total_time += 600
                blocked_count += 1
            else:
                time, congestion = ann_model.predict(length, max_speed, lanes, road_rank, traffic_density)
                total_time += time
                total_congestion += congestion
                    
        avg_congestion = total_congestion / max(1, len(path)-1)
        fuzzy_penalty = fuzzy_system.compute_penalty(avg_congestion, self.urgency, hospital['capacity_load'])
        
        penalty_seconds = total_time * (fuzzy_penalty / 100.0)
        cost = total_time + penalty_seconds
        
        fitness = 1.0 / (cost + 1e-6)
        if not is_valid:
            fitness *= 0.1
            
        avg_speed = (total_distance / max(1, total_time)) * 3.6
        
        # Survival Score: 100% - (penalty based on time and urgency)
        # For a critical patient (urgency 10), every minute over 10 mins drops survival by 5%
        survival_score = 100 - (max(0, (cost/60) - 10) * (self.urgency / 2.0))
        survival_score = max(5, min(99, survival_score))

        breakdown = {
            "raw_time_min": raw_time / 60.0,
            "traffic_delay_min": (total_time - raw_time) / 60.0,
            "hospital_penalty_min": penalty_seconds / 60.0,
            "total_effective_time": cost / 60.0,
            "blocked_incidents": blocked_count,
            "avg_speed_kph": avg_speed,
            "survival_probability": survival_score,
            "patient_condition": "Critical" if self.urgency > 7 else "Urgent" if self.urgency > 4 else "Stable"
        }
            
        return (fitness ** 2), cost, total_time, avg_congestion, total_distance, breakdown

    def crossover(self, parent1, parent2):
        path1 = parent1['path']
        path2 = parent2['path']
        
        # Find common nodes for intersection
        common_nodes = list(set(path1[1:-1]) & set(path2[1:-1]))
        
        if not common_nodes or random.random() < 0.2:
            # If no common nodes, or 20% of the time, try hospital swap
            if parent1['hospital'] != parent2['hospital']:
                child1 = {'path': parent1['path'], 'hospital': parent2['hospital']}
                child2 = {'path': parent2['path'], 'hospital': parent1['hospital']}
                # We need to fix the paths if hospitals changed
                child1['path'] = self._fix_path(child1)
                child2['path'] = self._fix_path(child2)
                return child1, child2
            return parent1, parent2
            
        cross_point = random.choice(common_nodes)
        idx1 = path1.index(cross_point)
        idx2 = path2.index(cross_point)
        
        child1_path = path1[:idx1] + path2[idx2:]
        child2_path = path2[:idx2] + path1[idx1:]
        
        return {'path': child1_path, 'hospital': parent2['hospital']}, \
               {'path': child2_path, 'hospital': parent1['hospital']}

    def _fix_path(self, chromosome):
        # If the path doesn't end at the hospital node, find a sub-path
        if chromosome['path'][-1] != chromosome['hospital']['node']:
            try:
                # Try to connect from the last node to the hospital
                sub = nx.shortest_path(self.G, chromosome['path'][-1], chromosome['hospital']['node'], weight='length')
                fixed_path = chromosome['path'] + sub[1:]
                
                # Simple loop removal
                new_path = []
                seen = set()
                for node in fixed_path:
                    if node in seen:
                        # Find index of first occurrence and truncate
                        idx = new_path.index(node)
                        new_path = new_path[:idx+1]
                        # Don't reset seen, just keep it as is
                    else:
                        new_path.append(node)
                        seen.add(node)
                return new_path
            except:
                return self._generate_random_path(chromosome['hospital']['node'])
        return chromosome['path']

    def mutate(self, chromosome):
        if random.random() > self.mutation_rate:
            return chromosome
            
        path = chromosome['path']
        hospital = chromosome['hospital']
        
        # Hospital mutation
        if random.random() < 0.3:
            new_hospital = random.choice(self.hospitals)
            new_path = self._generate_random_path(new_hospital['node'])
            if new_path:
                return {'path': new_path, 'hospital': new_hospital}
                
        if len(path) < 3:
            return chromosome
            
        # Path segment mutation
        mutate_idx = random.randint(1, len(path)-2)
        mutate_node = path[mutate_idx]
        
        try:
            def noisy_weight(u, v, d):
                return d.get('length', 10.0) * random.uniform(0.5, 3.0)
            
            sub_path = nx.shortest_path(self.G, source=mutate_node, target=hospital['node'], weight=noisy_weight)
            return {'path': path[:mutate_idx] + sub_path, 'hospital': hospital}
        except:
            return chromosome

    def run(self):
        self.initialize_population()
        
        best_overall_chromo = None
        best_overall_data = None
        best_cost = float('inf')
        convergence_data = []
        
        stagnation_counter = 0
        
        for gen in range(self.generations):
            evaluated = []
            for chromo in self.population:
                fitness, cost, time, cong, dist, breakdown = self.evaluate_fitness(chromo)
                evaluated.append({'chromo': chromo, 'fitness': fitness, 'cost': cost, 'time': time, 'cong': cong, 'dist': dist})
                
                if cost < best_cost:
                    best_cost = cost
                    best_overall_chromo = chromo
                    best_overall_data = {
                        'path': chromo['path'],
                        'hospital': chromo['hospital'],
                        'cost': cost,
                        'time': time,
                        'congestion': cong,
                        'distance': dist,
                        'breakdown': breakdown
                    }
                    stagnation_counter = 0 # Reset if we find improvement
                
            convergence_data.append(best_cost)
            stagnation_counter += 1
            
            # Smoother Adaptive Mutation: if no improvement for 4 generations, increase mutation slowly
            if stagnation_counter > 4:
                self.mutation_rate = min(0.6, self.mutation_rate + 0.05)
            elif stagnation_counter == 0:
                # Gradual recovery to base rate
                self.mutation_rate = max(self.base_mutation_rate, self.mutation_rate - 0.05)
            
            # Sort by fitness (descending)
            evaluated.sort(key=lambda x: x['fitness'], reverse=True)
            
            # Selection & Elitism
            new_population = []
            
            # Elitism: carry over the top 2 individuals
            new_population.append(evaluated[0]['chromo'])
            if len(evaluated) > 1:
                new_population.append(evaluated[1]['chromo'])
            
            while len(new_population) < self.pop_size:
                # Tournament Selection
                parents = []
                for _ in range(2):
                    p1, p2 = random.sample(evaluated, 2)
                    parents.append(p1['chromo'] if p1['fitness'] > p2['fitness'] else p2['chromo'])
                
                parent1, parent2 = parents
                
                # Crossover
                if random.random() < 0.8:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                    
                # Mutation
                new_population.append(self.mutate(child1))
                if len(new_population) < self.pop_size:
                    new_population.append(self.mutate(child2))
                
            self.population = new_population[:self.pop_size]
            
        return best_overall_data, convergence_data
