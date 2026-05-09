import numpy as np
from sklearn.neural_network import MLPRegressor

class TrafficANN:
    def __init__(self):
        # Features: [length (m), max_speed (km/h), lanes, road_rank (0-6), traffic_density (0-1)]
        self.model = MLPRegressor(hidden_layer_sizes=(32, 16), max_iter=1000, random_state=42)
        self._train_realistic_model()
        self.cache = {}

    def _scale_features(self, length, max_speed, lanes, road_rank, traffic_density):
        # Manual normalization to [0, 1] range
        return [
            length / 5000.0,      # Assume max path segment 5km
            max_speed / 120.0,   # Max speed 120km/h
            lanes / 6.0,         # Max lanes 6
            road_rank / 6.0,     # Max rank 6
            traffic_density      # Already 0-1
        ]
        
    def _train_realistic_model(self):
        np.random.seed(42)
        X = []
        y = []
        for _ in range(3000):
            length = np.random.uniform(10, 5000)
            max_speed = np.random.choice([20, 30, 40, 50, 60, 80, 100, 120])
            lanes = np.random.choice([1, 2, 3, 4, 5, 6])
            road_rank = np.random.choice([0, 1, 2, 3, 4, 5, 6])
            traffic_density = np.random.uniform(0, 1)
            
            speed_mps = (max_speed * 1000) / 3600
            base_time = length / speed_mps
            
            # Congestion factor: exponential growth
            congestion_factor = 1 + (np.exp(traffic_density * 2.2) - 1)
            # Rank factor: lower hierarchy is slower
            rank_factor = 1 + (road_rank * 0.2)
            # Lane benefit: more lanes = better flow
            lane_factor = 1 / (1 + (lanes - 1) * 0.05)
            
            travel_time = base_time * congestion_factor * rank_factor * lane_factor
            congestion_score = (traffic_density * 8) + (road_rank * 0.3)
            
            X.append(self._scale_features(length, max_speed, lanes, road_rank, traffic_density))
            y.append([travel_time, min(10, congestion_score)])
            
        self.model.fit(X, y)
        print("Realistic Traffic ANN (with scaling) trained successfully.")
        
    def predict(self, length, max_speed, lanes, road_rank, traffic_density):
        """
        Returns (predicted_travel_time, predicted_congestion_score)
        """
        cache_key = (round(length, 0), max_speed, lanes, road_rank, round(traffic_density, 2))
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        scaled_x = self._scale_features(length, max_speed, lanes, road_rank, traffic_density)
        pred = self.model.predict([scaled_x])[0]
        res = (max(0.1, float(pred[0])), max(0, min(10, float(pred[1]))))
        self.cache[cache_key] = res
        return res

# Singleton instance
ann_model = TrafficANN()
