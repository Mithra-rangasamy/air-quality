from network.model import TrafficNetwork, SignalPhase
from solvers import qaoa_solver, fixed_timing_baseline, rule_based_baseline

def run_solver_tests():
    # 1. Initialize a sample network state
    net = TrafficNetwork()
    
    # Artificially set some varying queue lengths to make the rule-based solver pick different phases
    net.graph.nodes[0]['queue_length_ns'] = 50.0
    net.graph.nodes[0]['queue_length_ew'] = 10.0
    net.graph.nodes[0]['queue_length'] = 60.0
    
    net.graph.nodes[1]['queue_length_ns'] = 5.0
    net.graph.nodes[1]['queue_length_ew'] = 45.0
    net.graph.nodes[1]['queue_length'] = 50.0
    
    # Set an emergency corridor at node 2 requiring EW_GREEN
    net.graph.nodes[2]['queue_length_ns'] = 10.0
    net.graph.nodes[2]['queue_length_ew'] = 10.0
    net.graph.nodes[2]['queue_length'] = 20.0
    emergency_corridor = {2: SignalPhase.EW_GREEN.value}
    
    state = net.get_network_state(0)
    
    # We didn't expose queue_length_ns/ew directly in get_network_state in Phase 1
    # But rule_based baseline reads them from the state if available, so we inject them for testing
    for node in state:
        state[node]['queue_length_ns'] = net.graph.nodes[node]['queue_length_ns']
        state[node]['queue_length_ew'] = net.graph.nodes[node]['queue_length_ew']
        
    weights = [1.0, 2.0, 1.0, 5.0, 1.0, 1.0]
    
    print("=== SAMPLE NETWORK STATE ===")
    print(f"Node 0: NS={state[0]['queue_length_ns']}, EW={state[0]['queue_length_ew']}")
    print(f"Node 1: NS={state[1]['queue_length_ns']}, EW={state[1]['queue_length_ew']}")
    print(f"Node 2: NS={state[2]['queue_length_ns']}, EW={state[2]['queue_length_ew']} (Emergency EW_GREEN)")
    print("============================\n")

    # 2. Run solvers
    print("Running Fixed Timing Baseline...")
    plan_ft, cost_ft, _ = fixed_timing_baseline.solve(state, weights, emergency_corridor)
    
    print("Running Rule-Based Baseline...")
    plan_rb, cost_rb, _ = rule_based_baseline.solve(state, weights, emergency_corridor)
    
    print("Running QAOA Solver (this may take a few seconds)...")
    plan_qaoa, cost_qaoa, meta_qaoa = qaoa_solver.solve(state, weights, emergency_corridor, shots=1000)
    
    # 3. Print side-by-side comparison
    print("\n" + "="*70)
    print(f"{'Node':<10} | {'Fixed Timing':<20} | {'Rule-Based':<20} | {'QAOA':<20}")
    print("-" * 70)
    
    for node in range(len(state)):
        p_ft = plan_ft[node].name
        p_rb = plan_rb[node].name
        p_qaoa = plan_qaoa[node].name
        print(f"{node:<10} | {p_ft:<20} | {p_rb:<20} | {p_qaoa:<20}")
        
    print("-" * 70)
    print(f"{'QUBO Cost':<10} | {cost_ft:<20.2f} | {cost_rb:<20.2f} | {cost_qaoa:<20.2f}")
    print("="*70)
    
    print("\nQAOA Metadata:")
    print(f"Optimized Parameters (gamma, beta): {meta_qaoa['opt_params']}")

if __name__ == "__main__":
    run_solver_tests()
