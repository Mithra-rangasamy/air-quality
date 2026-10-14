from network.model import SignalPhase
from qubo.formulation import build_qubo

def solve(network_state, weights=None, emergency_corridor=None, **kwargs):
    """
    Rule-based baseline solver.
    Simple greedy heuristic: at each intersection, select the phase serving 
    the direction with the highest current queue length.
    """
    if weights is None:
        weights = [1.0] * 6
        
    N = len(network_state)
    plan = {}
    
    for node, state in network_state.items():
        # Check emergency corridor first (rules often prioritize emergencies)
        if emergency_corridor and node in emergency_corridor:
            plan[node] = SignalPhase(emergency_corridor[node])
            continue
            
        ns_queue = state.get('queue_length_ns', 0)
        ew_queue = state.get('queue_length_ew', 0)
        
        if ns_queue > ew_queue:
            plan[node] = SignalPhase.NS_GREEN
        elif ew_queue > ns_queue:
            plan[node] = SignalPhase.EW_GREEN
        else:
            # If queues are equal, maintain current phase (or default to NS)
            curr_phase = state['current_signal_phase']
            if curr_phase in [SignalPhase.NS_GREEN, SignalPhase.EW_GREEN]:
                plan[node] = curr_phase
            else:
                plan[node] = SignalPhase.NS_GREEN

    # Calculate QUBO cost of this plan for comparison
    A = 100000.0
    Q = build_qubo(network_state, weights, emergency_corridor, A=A)
    
    x = [0] * (N * 3)
    for node in range(N):
        p = plan[node].value - 1
        x[node*3 + p] = 1
        
    cost = 0.0
    for (i, j), w in Q.items():
        if x[i] == 1 and x[j] == 1:
            cost += w
            
    return plan, cost, {"method": "rule_based"}
