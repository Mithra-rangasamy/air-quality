import os
from network.model import TrafficNetwork
from events.manager import EventScheduler, EmergencyVehicleEvent
from solvers import qaoa_solver, fixed_timing_baseline, rule_based_baseline

def format_plan(plan):
    return [plan[n].name.replace("_GREEN", "").replace("ALL_RED_PEDESTRIAN", "RED") for n in range(6)]

def run_event_test():
    net = TrafficNetwork()
    
    # Setup highly biased queues: NS direction has 50 vehicles, EW has 0 vehicles.
    # Baseline solver should heavily favor NS_GREEN.
    for node in net.graph.nodes:
        net.graph.nodes[node]['queue_length_ns'] = 50.0
        net.graph.nodes[node]['queue_length_ew'] = 0.0
        net.graph.nodes[node]['queue_length'] = 50.0
        net.graph.nodes[node]['road_capacity'] = 100.0
        
    scheduler = EventScheduler(net)
    
    # We want a path that uses horizontal edges so the emergency corridor forces EW_GREEN.
    # Path 0 -> 1 -> 2 is pure horizontal.
    ev_event = EmergencyVehicleEvent(0, 2, net, time_per_edge=1.0)
    
    # Schedule the emergency to trigger at t=1.0
    scheduler.schedule(1.0, ev_event)
    
    # High weight for emergency (lambda_4)
    weights = [1.0, 2.0, 1.0, 50.0, 1.0, 1.0]
    
    for t in range(4):
        t = float(t)
        print(f"\n{'='*80}")
        print(f"--- SIMULATION TIME t={t} ---")
        
        was_active = bool(scheduler.active_events)
        
        scheduler.step(t, dt=1.0)
        
        is_active = bool(scheduler.active_events)
        corridor = scheduler.get_current_emergency_corridor()
        
        print(f"Active Emergency Corridor: {corridor}")
        
        state = net.get_network_state(t)
        # Inject queue components for solvers
        for node in state:
            state[node]['queue_length_ns'] = net.graph.nodes[node]['queue_length_ns']
            state[node]['queue_length_ew'] = net.graph.nodes[node]['queue_length_ew']
            
        print("\nSolving network...")
        plan_ft, c_ft, _ = fixed_timing_baseline.solve(state, weights, corridor)
        plan_rb, c_rb, _ = rule_based_baseline.solve(state, weights, corridor)
        plan_qa, c_qa, _ = qaoa_solver.solve(state, weights, corridor, shots=1000)
        
        print(f"Fixed Timing : {format_plan(plan_ft)} | Cost: {c_ft:.2f}")
        print(f"Rule-Based   : {format_plan(plan_rb)} | Cost: {c_rb:.2f}")
        print(f"QAOA Solver  : {format_plan(plan_qa)} | Cost: {c_qa:.2f}")
        
        if not was_active and is_active:
            print("\n>>> HIGHLIGHT: EVENT TRIGGERED! Corridor computed and QUBO re-solved.")
            print(">>> Notice how Rule-Based and QAOA switch nodes 0, 1, 2 to EW (phase 2) despite heavy NS queues!")
        elif was_active and not is_active:
            print("\n>>> HIGHLIGHT: EVENT COMPLETED! Emergency term deactivated.")
            print(">>> Re-solve confirms return to baseline plan (favoring NS due to queues).")
            
        # Apply the rule-based plan to the network to simulate physical progress
        net.apply_signal_plan(plan_rb, dt=1.0)

if __name__ == "__main__":
    run_event_test()
