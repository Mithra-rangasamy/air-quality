# Hybrid Quantum-Classical Traffic Optimization Platform

This project is a hackathon prototype for a Hybrid Quantum-Classical Traffic Optimization Platform. It simulates a 6-intersection urban road network and uses a Quantum Approximate Optimization Algorithm (QAOA) simulated via Qiskit Aer to optimize traffic light phases. The system balances multiple conflicting objectives—such as minimizing wait times, reducing congestion, maximizing throughput, and minimizing emissions—while dynamically reacting to live events like emergency vehicle corridors and sudden congestion. 

## Setup and Run Instructions

1. **Create and activate the virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install the dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run the Streamlit Dashboard:**
   ```powershell
   .\venv\Scripts\streamlit run dashboard/app.py
   ```

## QUBO Formulation

The traffic optimization problem is formulated as a Quadratic Unconstrained Binary Optimization (QUBO) problem. The decision variables represent the signal phases assigned to each intersection. A heavy penalty enforces a strict "one-hot" constraint so that exactly one phase is active per intersection. The objective function minimizes six distinct, tunable terms based on real-time network state:

1. **Minimize Waiting Time:** Penalizes assigning a red phase to directions with high existing queue lengths.
2. **Minimize Queue Length:** Rewards assigning a green phase proportional to the current queue length.
3. **Reduce Congestion:** Rewards assigning a green phase proportional to the intersection's traffic density.
4. **Reduce Emergency Vehicle Travel Time:** Applies a massive reward to the specific phases required to clear a dynamically updated "emergency corridor" path.
5. **Reduce Fuel Usage and Emissions:** Rewards maintaining the current signal phase to reduce stop-and-go fuel penalties.
6. **Maximize Traffic Throughput:** Rewards green phases proportional to the road's physical capacity.

## Quantum Hardware Disclaimer

**Explicit Statement:** This project is a hybrid quantum-classical simulation running entirely on classical hardware using the `qiskit-aer` simulator. It is not currently executed on real quantum processing units (QPUs). Furthermore, due to the small problem size (18 qubits for 6 intersections), no quantum advantage is claimed or expected over classical solvers (like the implemented rule-based heuristic). The platform serves as a proof-of-concept for how quantum formulations (QUBO/Ising) can be applied to complex, multi-objective urban routing problems as QPU scale increases.

## Scope

**Implemented:**
- 6-intersection adaptive traffic network simulation.
- QUBO formulation mapped to Ising Hamiltonians.
- Three solvers: Fixed-Timing, Rule-Based (Heuristic), and QAOA (Quantum Simulation).
- Dynamic Emergency Vehicle routing (shortest path corridor overlay).
- Sudden Congestion event injection (queue spikes).
- Environmental impact estimation (fuel/CO2) derived from idle times.
- Fully offline interactive Streamlit dashboard.

**Explicitly Out of Scope:**
- Accident events and road closures (re-routing traffic dynamically around blocked edges).
- Real-world sensor data integration (e.g. SUMO).
- Execution on real quantum hardware.
