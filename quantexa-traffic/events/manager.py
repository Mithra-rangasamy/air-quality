import networkx as nx
from network.model import SignalPhase

class EmergencyVehicleEvent:
    """
    Primary Event: Emergency Vehicle Arrival.
    Computes shortest path (corridor) and requires appropriate signal phases 
    for the nodes along the path to reduce emergency travel time.
    """
    def __init__(self, start_node, dest_node, network, time_per_edge=1.0):
        self.start_node = start_node
        self.dest_node = dest_node
        self.network = network
        
        # Compute the shortest path (the corridor)
        self.path = nx.shortest_path(self.network.graph, start_node, dest_node)
        self.time_per_edge = time_per_edge
        self.elapsed = 0.0
        self.current_index = 0
        self.active = True
        
        # Determine the required signal phases for the corridor
        self.corridor_phases = self._compute_corridor_phases()
        print(f"[Event Computed] Emergency Vehicle Corridor Path: {self.path}")

    def _compute_corridor_phases(self):
        corridor = {}
        # Define edge orientations based on grid topology
        # Horizontal (EW): (0,1), (1,2), (3,4), (4,5)
        # Vertical (NS): (0,3), (1,4), (2,5)
        ew_edges = [set([0, 1]), set([1, 2]), set([3, 4]), set([4, 5])]
        
        for i in range(len(self.path) - 1):
            u = self.path[i]
            v = self.path[i+1]
            edge_set = set([u, v])
            
            if edge_set in ew_edges:
                phase = SignalPhase.EW_GREEN.value
            else:
                phase = SignalPhase.NS_GREEN.value
            
            # Require the phase for both nodes connected by this path segment
            corridor[u] = phase
            corridor[v] = phase
            
        return corridor

    def step(self, dt=1.0):
        if not self.active:
            return
            
        self.elapsed += dt
        self.current_index = int(self.elapsed // self.time_per_edge)
        
        if self.current_index >= len(self.path) - 1:
            self.active = False
            print(f"[Event Completed] Emergency vehicle reached destination {self.dest_node}! Normal operation restored.")
            
    def get_active_corridor(self):
        if not self.active:
            return None
        # Return the required phases for the current and upcoming nodes on the path
        rem_corridor = {}
        for i in range(self.current_index, len(self.path)):
            node = self.path[i]
            if node in self.corridor_phases:
                rem_corridor[node] = self.corridor_phases[node]
        return rem_corridor


class SuddenCongestionEvent:
    """
    Secondary Event: Sudden Congestion.
    Injects a density/queue spike into target intersections. 
    The spike then decays naturally as the baseline solver processes the traffic.
    """
    def __init__(self, target_nodes, intensity, duration, network):
        self.target_nodes = target_nodes
        self.intensity = intensity # e.g. number of vehicles added over duration
        self.duration = duration
        self.network = network
        self.elapsed = 0.0
        self.active = True
        print(f"[Event Registered] Sudden Congestion Event at {self.target_nodes} for {self.duration}s.")
        
    def step(self, dt=1.0):
        if not self.active:
            return
            
        inflow = (self.intensity / self.duration) * dt
        for node in self.target_nodes:
            self.network.graph.nodes[node]['queue_length_ns'] += inflow / 2.0
            self.network.graph.nodes[node]['queue_length_ew'] += inflow / 2.0
            
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            print(f"[Event Completed] Sudden Congestion Event at {self.target_nodes} ended.")


class EventScheduler:
    """
    Schedules and manages dynamic events on a fixed scripted timeline.
    """
    def __init__(self, network):
        self.network = network
        self.scheduled_events = {} # dict mapping trigger_time -> list of events
        self.active_events = []
        
    def schedule(self, trigger_time, event):
        if trigger_time not in self.scheduled_events:
            self.scheduled_events[trigger_time] = []
        self.scheduled_events[trigger_time].append(event)
        
    def step(self, current_time, dt=1.0):
        # Trigger new events scheduled exactly at or before current_time (simplification for exact float match)
        if current_time in self.scheduled_events:
            for ev in self.scheduled_events[current_time]:
                self.active_events.append(ev)
                print(f"[Time {current_time}] EVENT TRIGGERED: {type(ev).__name__}")
            # Remove to prevent re-triggering
            del self.scheduled_events[current_time]
                
        # Step all active events
        for ev in self.active_events:
            ev.step(dt)
            
        # Clean up finished events
        self.active_events = [ev for ev in self.active_events if ev.active]

    def get_current_emergency_corridor(self):
        # Merge active emergency corridors
        merged_corridor = {}
        for ev in self.active_events:
            if isinstance(ev, EmergencyVehicleEvent):
                corr = ev.get_active_corridor()
                if corr:
                    merged_corridor.update(corr)
        return merged_corridor if merged_corridor else None
