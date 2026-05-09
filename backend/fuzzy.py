import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class FuzzyRouter:
    def __init__(self):
        # Antecedents (Inputs)
        self.congestion = ctrl.Antecedent(np.arange(0, 11, 1), 'congestion')
        self.urgency = ctrl.Antecedent(np.arange(0, 11, 1), 'urgency')
        self.hospital_load = ctrl.Antecedent(np.arange(0, 3, 0.5), 'hospital_load')

        # Consequent (Output) - Routing Penalty (0 to 100)
        self.penalty = ctrl.Consequent(np.arange(0, 101, 1), 'penalty')

        # Membership Functions
        self.congestion.automf(3, names=['low', 'medium', 'high'])
        self.urgency.automf(3, names=['low', 'medium', 'high'])
        self.hospital_load.automf(3, names=['low', 'medium', 'high'])

        self.penalty['low'] = fuzz.trimf(self.penalty.universe, [0, 0, 50])
        self.penalty['medium'] = fuzz.trimf(self.penalty.universe, [0, 50, 100])
        self.penalty['high'] = fuzz.trimf(self.penalty.universe, [50, 100, 100])

        # Comprehensive Rules
        # Urgency & Congestion
        rule1 = ctrl.Rule(self.urgency['high'] & self.congestion['high'], self.penalty['high'])
        rule2 = ctrl.Rule(self.urgency['high'] & self.congestion['low'], self.penalty['low'])
        rule3 = ctrl.Rule(self.urgency['low'] & self.congestion['low'], self.penalty['low'])
        rule4 = ctrl.Rule(self.urgency['medium'], self.penalty['medium'])
        
        # Hospital Load Impact (Primary Driver)
        rule5 = ctrl.Rule(self.hospital_load['high'], self.penalty['high'])
        rule6 = ctrl.Rule(self.hospital_load['medium'], self.penalty['medium'])
        rule7 = ctrl.Rule(self.hospital_load['low'], self.penalty['low'])
        
        # Critical Override
        rule8 = ctrl.Rule(self.urgency['high'] & self.hospital_load['high'], self.penalty['high'])

        self.routing_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8])
        self.routing_sim = ctrl.ControlSystemSimulation(self.routing_ctrl)

    def compute_penalty(self, congestion_score, urgency_level, hospital_load_level):
        """
        congestion_score: 0-10
        urgency_level: 0-10 (0=normal, 10=critical)
        hospital_load_level: 0-2 (0=low, 2=high)
        """
        self.routing_sim.input['congestion'] = max(0, min(10, congestion_score))
        self.routing_sim.input['urgency'] = max(0, min(10, urgency_level))
        self.routing_sim.input['hospital_load'] = max(0, min(2, hospital_load_level))

        try:
            self.routing_sim.compute()
            if 'penalty' in self.routing_sim.output:
                return self.routing_sim.output['penalty']
            return 50.0 # Default if computation is ambiguous
        except (ValueError, KeyError):
            # Fallback if rules don't cover a specific point or computation fails
            return 50.0

fuzzy_system = FuzzyRouter()
