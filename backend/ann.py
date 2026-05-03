import numpy as np
from sklearn.neural_network import MLPRegressor

class TrafficANN:
    def __init__(self):
        # We predict 2 values: travel_time and congestion_score
        # Features: length (meters), traffic_level (0, 1, 2)
        self.model = MLPRegressor(hidden_layer_sizes=(10, 5), max_iter=1000, random_state=42)
        self._train_dummy_model()
        
    def _train_dummy_model(self):
        # Generate some logical dummy data
        # length ranging from 10 to 500 meters
        # traffic 0, 1, 2
        np.random.seed(42)
        X = []
        y = []
        for _ in range(500):
            length = np.random.uniform(10, 500)
            traffic = np.random.choice([0, 1, 2])
            
            # Base speed: low traffic = 15m/s (~54km/h), med = 8m/s, high = 3m/s
            speed = 15 if traffic == 0 else (8 if traffic == 1 else 3)
            # Add some noise
            speed = max(1, speed + np.random.normal(0, 1))
            
            travel_time = length / speed
            congestion_score = traffic * 3.33 + np.random.normal(0, 0.5) # 0 to 10 scale approx
            
            X.append([length, traffic])
            y.append([travel_time, congestion_score])
            
        self.model.fit(X, y)
        print("ANN Model trained successfully on simulated data.")
        
    def predict(self, length, traffic_level):
        """
        Returns (predicted_travel_time, predicted_congestion_score)
        """
        # reshape for single sample
        pred = self.model.predict([[length, traffic_level]])[0]
        # ensure no negative values
        return max(0.1, pred[0]), max(0, min(10, pred[1]))

# Singleton instance
ann_model = TrafficANN()
