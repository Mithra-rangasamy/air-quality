import networkx as nx
import numpy as np
from enum import Enum

class SignalPhase(Enum):
    NS_GREEN = 1
    EW_GREEN = 2
    ALL_RED_PEDESTRIAN = 3

class TrafficNetwork:
    def __init__(self):
        self.graph = nx.Graph()
        self.current_time = 0
        self._initialize_network()

    def _initialize_network(self):
        # Create 6 connected intersections
        nodes = range(6)
        
        # Simple grid-like topology
        # 0 -- 1 -- 2
        # |    |    |
        # 3 -- 4 -- 5
        edges = [
            (0, 1, {'capacity': 100}), (1, 2, {'capacity': 100}),
            (3, 4, {'capacity': 100}), (4, 5, {'capacity': 100}),
            (0, 3, {'capacity': 80}),  (1, 4, {'capacity': 120}),
            (2, 5, {'capacity': 80})
        ]
        
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
        
        for node in self.graph.nodes:
            self.graph.nodes[node]['traffic_density'] = 0.0
            self.graph.nodes[node]['queue_length'] = 0.0
            self.graph.nodes[node]['queue_length_ns'] = 0.0
            self.graph.nodes[node]['queue_length_ew'] = 0.0
            self.graph.nodes[node]['road_capacity'] = 100.0 
            self.graph.nodes[node]['current_signal_phase'] = SignalPhase.NS_GREEN
            self.graph.nodes[node]['pedestrian_flag'] = False
            
    def generate_rush_hour_curve(self, t, peak_time=30, spread=10, max_density=50):
        """
        Generates a realistic rush-hour-shaped density curve over a simulated time window.
        Uses a Gaussian curve to represent peaking traffic (e.g., vehicles arriving per hour).
        """
        baseline = 10.0
        return baseline + max_density * np.exp(-0.5 * ((t - peak_time) / spread) ** 2)
        
    def get_network_state(self, t):
        """Returns the full state of all intersections at simulated time t."""
        state = {}
        for node in self.graph.nodes:
            node_data = self.graph.nodes[node]
            state[node] = {
                'traffic_density': node_data['traffic_density'],
                'queue_length': node_data['queue_length'],
                'road_capacity': node_data['road_capacity'],
                'current_signal_phase': node_data['current_signal_phase'],
                'pedestrian_flag': node_data['pedestrian_flag']
            }
        return state

    def apply_signal_plan(self, plan, dt=1.0):
        """
        Updates each intersection's current_signal_phase and updates queue_length/density accordingly.
        
        plan: dict mapping node_id to SignalPhase
        dt: time step duration
        """
        self.current_time += dt
        
        # Calculate incoming traffic for this time step using the rush-hour curve
        base_incoming_traffic_rate = self.generate_rush_hour_curve(self.current_time)
        inflow = (base_incoming_traffic_rate / 60.0) * dt 
        
        for node in self.graph.nodes:
            if node in plan:
                self.graph.nodes[node]['current_signal_phase'] = plan[node]
                
            phase = self.graph.nodes[node]['current_signal_phase']
            outflow = (self.graph.nodes[node]['road_capacity'] / 60.0) * dt
            
            ns_queue = self.graph.nodes[node]['queue_length_ns']
            ew_queue = self.graph.nodes[node]['queue_length_ew']
            
            if phase == SignalPhase.NS_GREEN:
                # Green phase reduces queue on served direction (NS), red phase increases it (EW)
                ns_queue = max(0, ns_queue + inflow - outflow)
                ew_queue += inflow
            elif phase == SignalPhase.EW_GREEN:
                # Green phase reduces queue on served direction (EW), red phase increases it (NS)
                ns_queue += inflow
                ew_queue = max(0, ew_queue + inflow - outflow)
            elif phase == SignalPhase.ALL_RED_PEDESTRIAN:
                # Both directions are red
                ns_queue += inflow
                ew_queue += inflow
                self.graph.nodes[node]['pedestrian_flag'] = True
                
            if phase != SignalPhase.ALL_RED_PEDESTRIAN:
                self.graph.nodes[node]['pedestrian_flag'] = False
                
            self.graph.nodes[node]['queue_length_ns'] = ns_queue
            self.graph.nodes[node]['queue_length_ew'] = ew_queue
            
            total_queue = ns_queue + ew_queue
            self.graph.nodes[node]['queue_length'] = total_queue
            self.graph.nodes[node]['traffic_density'] = total_queue / max(1.0, self.graph.nodes[node]['road_capacity'])
