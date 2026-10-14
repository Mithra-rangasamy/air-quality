from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from scipy.optimize import minimize
from network.model import SignalPhase
from qubo.formulation import build_qubo, qubo_to_ising

def create_qaoa_circ(gamma, beta, J, h, num_qubits):
    qc = QuantumCircuit(num_qubits)
    qc.h(range(num_qubits))
    
    # Cost Hamiltonian H_C
    for i, hi in h.items():
        qc.rz(2 * gamma * hi, i)
    for (i, j), Jij in J.items():
        qc.cx(i, j)
        qc.rz(2 * gamma * Jij, j)
        qc.cx(i, j)
        
    # Mixer Hamiltonian H_M
    for i in range(num_qubits):
        qc.rx(2 * beta, i)
        
    qc.measure_all()
    return qc

def eval_qubo(Q, x):
    energy = 0.0
    for (i, j), w in Q.items():
        if x[i] == 1 and x[j] == 1:
            energy += w
    return energy

def is_feasible(x, N):
    for node in range(N):
        if sum(x[node*3 : node*3+3]) != 1:
            return False
    return True

def solve(network_state, weights=None, emergency_corridor=None, shots=1000):
    if weights is None:
        weights = [1.0] * 6
        
    N = len(network_state)
    num_qubits = N * 3
    
    # Large penalty A to heavily discourage infeasible states
    A = 100000.0
    Q = build_qubo(network_state, weights, emergency_corridor, A=A)
    J, h, offset = qubo_to_ising(Q)
    
    simulator = AerSimulator()
    
    def objective_function(params):
        gamma, beta = params
        qc = create_qaoa_circ(gamma, beta, J, h, num_qubits)
        result = simulator.run(qc, shots=shots).result()
        counts = result.get_counts()
        
        expected_energy = 0
        for bitstring, count in counts.items():
            z = [1 if b == '0' else -1 for b in reversed(bitstring)]
            energy = offset
            for i, hi in h.items():
                energy += hi * z[i]
            for (i, j), Jij in J.items():
                energy += Jij * z[i] * z[j]
            expected_energy += energy * (count / shots)
        return expected_energy

    # Optimize QAOA parameters (p=1 layer)
    res = minimize(objective_function, [1.0, 1.0], method='COBYLA', options={'maxiter': 50})
    opt_gamma, opt_beta = res.x
    
    # Sample final circuit
    final_qc = create_qaoa_circ(opt_gamma, opt_beta, J, h, num_qubits)
    result = simulator.run(final_qc, shots=shots).result()
    counts = result.get_counts()
    
    # Evaluate and post-select
    bitstrings = []
    for bs_str in counts.keys():
        x = [1 if b == '1' else 0 for b in reversed(bs_str)]
        cost = eval_qubo(Q, x)
        bitstrings.append((cost, x, bs_str))
        
    bitstrings.sort(key=lambda item: item[0])
    
    best_feasible_x = None
    best_cost = None
    infeasible_skipped = 0
    
    for cost, x, bs_str in bitstrings:
        if is_feasible(x, N):
            best_feasible_x = x
            best_cost = cost
            break
        else:
            infeasible_skipped += 1
            
    if infeasible_skipped > 0:
        print(f"QAOA: Skipped {infeasible_skipped} lower-cost but infeasible bitstrings.")
        
    if best_feasible_x is None:
        print("QAOA WARNING: No feasible bitstrings found. Returning fallback (all RED).")
        best_feasible_x = [0, 0, 1] * N
        best_cost = eval_qubo(Q, best_feasible_x)

    # Decode bitstring to plan
    plan = {}
    for node in range(N):
        for p in range(3):
            if best_feasible_x[node*3 + p] == 1:
                plan[node] = SignalPhase(p + 1)
                
    return plan, best_cost, {"counts": counts, "opt_params": [opt_gamma, opt_beta]}
