def build_qubo(network_state, weights, emergency_corridor=None, A=1000.0):
    """
    Builds the QUBO matrix for the traffic optimization problem.
    
    network_state: dict mapping node_id to node state dict
    weights: dict with keys 'lambda_1'..'lambda_6' or a list of 6 floats
    emergency_corridor: dict mapping node_id -> required phase (integer 1, 2, or 3)
                        or None if no emergency.
    A: penalty weight for the one-hot constraint
    
    Returns:
        Q: a dictionary mapping (i, j) to the QUBO coefficient.
           Indices are from 0 to 3*N - 1.
    """
    if isinstance(weights, dict):
        w1 = weights.get('lambda_1', 1.0)
        w2 = weights.get('lambda_2', 1.0)
        w3 = weights.get('lambda_3', 1.0)
        w4 = weights.get('lambda_4', 1.0)
        w5 = weights.get('lambda_5', 1.0)
        w6 = weights.get('lambda_6', 1.0)
    else:
        w1, w2, w3, w4, w5, w6 = weights

    N = len(network_state)
    Q = {}
    
    def get_var_idx(node, phase):
        return node * 3 + phase

    # 1. One-hot constraint: A * sum_i (sum_p x_{i,p} - 1)^2
    for node in network_state.keys():
        for p in range(3):
            idx_p = get_var_idx(node, p)
            Q[(idx_p, idx_p)] = Q.get((idx_p, idx_p), 0.0) - A
            for q in range(p + 1, 3):
                idx_q = get_var_idx(node, q)
                Q[(idx_p, idx_q)] = Q.get((idx_p, idx_q), 0.0) + 2 * A

    # Objectives
    for node, state in network_state.items():
        q_len = state['queue_length']
        density = state['traffic_density']
        capacity = state['road_capacity']
        curr_phase = state['current_signal_phase'].value - 1
        
        idx_ns = get_var_idx(node, 0)
        idx_ew = get_var_idx(node, 1)
        idx_red = get_var_idx(node, 2)
        
        # Obj 1: Minimize waiting time (Penalize ALL_RED phase based on queue length)
        Q[(idx_red, idx_red)] = Q.get((idx_red, idx_red), 0.0) + w1 * q_len
        
        # Obj 2: Minimize queue length (Reward GREEN phases based on queue length)
        Q[(idx_ns, idx_ns)] = Q.get((idx_ns, idx_ns), 0.0) - w2 * q_len
        Q[(idx_ew, idx_ew)] = Q.get((idx_ew, idx_ew), 0.0) - w2 * q_len
        
        # Obj 3: Reduce congestion (Reward GREEN phases based on density)
        Q[(idx_ns, idx_ns)] = Q.get((idx_ns, idx_ns), 0.0) - w3 * density
        Q[(idx_ew, idx_ew)] = Q.get((idx_ew, idx_ew), 0.0) - w3 * density
        
        # Obj 4: Reduce emergency vehicle travel time
        if emergency_corridor and node in emergency_corridor:
            req_phase = emergency_corridor[node] - 1
            idx_emg = get_var_idx(node, req_phase)
            Q[(idx_emg, idx_emg)] = Q.get((idx_emg, idx_emg), 0.0) - w4 * 100.0
            
        # Obj 5: Reduce fuel usage and emissions (Reward maintaining current phase)
        idx_curr = get_var_idx(node, curr_phase)
        Q[(idx_curr, idx_curr)] = Q.get((idx_curr, idx_curr), 0.0) - w5 * 10.0
        
        # Obj 6: Maximize traffic throughput (Reward GREEN phases based on capacity)
        Q[(idx_ns, idx_ns)] = Q.get((idx_ns, idx_ns), 0.0) - w6 * (capacity / 100.0) # Normalized roughly
        Q[(idx_ew, idx_ew)] = Q.get((idx_ew, idx_ew), 0.0) - w6 * (capacity / 100.0)

    # Clean up zero entries
    return {k: v for k, v in Q.items() if v != 0.0}

def qubo_to_ising(qubo_matrix):
    """
    Converts a QUBO matrix to an Ising Hamiltonian (standard x -> (1-z)/2 substitution).
    
    Returns:
        J: dict of off-diagonal couplings J_{i,j} for i < j
        h: dict of local fields h_i
        offset: scalar constant offset
    """
    J = {}
    h = {}
    offset = 0.0
    
    # Initialize h for all variables
    max_idx = -1
    for (i, j) in qubo_matrix.keys():
        max_idx = max(max_idx, i, j)
        
    for i in range(max_idx + 1):
        h[i] = 0.0

    for (i, j), weight in qubo_matrix.items():
        if i == j:
            offset += weight / 2.0
            h[i] -= weight / 2.0
        else:
            # Ensure i < j
            if i > j:
                i, j = j, i
            offset += weight / 4.0
            h[i] -= weight / 4.0
            h[j] -= weight / 4.0
            J[(i, j)] = J.get((i, j), 0.0) + weight / 4.0
            
    # Clean up zeros
    h = {k: v for k, v in h.items() if v != 0.0}
    J = {k: v for k, v in J.items() if v != 0.0}
            
    return J, h, offset
