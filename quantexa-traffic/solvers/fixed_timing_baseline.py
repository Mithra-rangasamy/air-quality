from network.model import SignalPhase
from qubo.formulation import build_qubo

def solve(network_state, weights=None, emergency_corridor=None, **kwargs):
    """
    Fixed-timing baseline solver.
    Cycles through NS_GREEN -> EW_GREEN -> ALL_RED on a fixed timer.
    """
    if weights is None:
        weights = [1.0] * 6
        
    N = len(network_state)
    plan = {}
    
    for node, state in network_state.items():
        curr_phase = state['current_signal_phase']
        
        if curr_phase == SignalPhase.NS_GREEN:
            next_phase = SignalPhase.EW_GREEN
        elif curr_phase == SignalPhase.EW_GREEN:
            next_phase = SignalPhase.ALL_RED_PEDESTRIAN
        else:
            next_phase = SignalPhase.NS_GREEN
            
        plan[node] = next_phase

    # Calculate QUBO cost of this plan for comparison
    A = 100000.0
    Q = build_qubo(network_state, weights, emergency_corridor, A=A)
    
    # Encode plan to x vector to evaluate cost
    x = [0] * (N * 3)
    for node in range(N):
        p = plan[node].value - 1
        x[node*3 + p] = 1
        
    cost = 0.0
    for (i, j), w in Q.items():
        if x[i] == 1 and x[j] == 1:
            cost += w
            
    return plan, cost, {"method": "fixed_timing"}
