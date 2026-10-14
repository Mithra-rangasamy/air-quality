import qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

def run_test():
    # Create a simple quantum circuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    
    # Use AerSimulator
    simulator = AerSimulator()
    job = simulator.run(qc, shots=100)
    result = job.result()
    counts = result.get_counts()
    
    print("Qiskit Aer import and test successful!")
    print(f"Test circuit measurement results: {counts}")

if __name__ == "__main__":
    run_test()
