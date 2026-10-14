import unittest
from qubo.formulation import build_qubo, qubo_to_ising
from network.model import SignalPhase

class TestQUBO(unittest.TestCase):
    def setUp(self):
        self.dummy_state = {
            0: {
                'queue_length': 10.0,
                'traffic_density': 0.5,
                'road_capacity': 100.0,
                'current_signal_phase': SignalPhase.NS_GREEN,
                'pedestrian_flag': False
            }
        }
        self.zero_weights = [0.0]*6

    def eval_qubo(self, Q, x):
        """Helper to evaluate energy of an assignment."""
        energy = 0.0
        for (i, j), w in Q.items():
            energy += w * x[i] * x[j]
        return energy

    def test_constraint_term(self):
        """Verify the constraint term penalizes non-one-hot assignments."""
        A = 1000.0
        Q = build_qubo(self.dummy_state, self.zero_weights, A=A)
        
        # Valid: sum = 1 (e.g. x=[1, 0, 0])
        # Energy = -A
        valid_energy = self.eval_qubo(Q, [1, 0, 0])
        self.assertEqual(valid_energy, -A)
        
        # Invalid: sum = 0 (e.g. x=[0, 0, 0])
        # Energy = 0 (higher than -A)
        invalid_0_energy = self.eval_qubo(Q, [0, 0, 0])
        self.assertGreater(invalid_0_energy, valid_energy)
        
        # Invalid: sum = 2 (e.g. x=[1, 1, 0])
        # Energy = -2A + 2A = 0 (higher than -A)
        invalid_2_energy = self.eval_qubo(Q, [1, 1, 0])
        self.assertGreater(invalid_2_energy, valid_energy)
        
    def test_objective_1_wait_time(self):
        """Higher queue length increases the wait-time term's contribution (Obj 1)."""
        w = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        state1 = {0: {**self.dummy_state[0], 'queue_length': 10.0}}
        state2 = {0: {**self.dummy_state[0], 'queue_length': 20.0}}
        
        Q1 = build_qubo(state1, w, A=0.0)
        Q2 = build_qubo(state2, w, A=0.0)
        
        # Obj 1 penalizes ALL_RED phase (index 2)
        penalty1 = Q1.get((2, 2), 0.0)
        penalty2 = Q2.get((2, 2), 0.0)
        
        self.assertGreater(penalty2, penalty1)
        self.assertGreater(penalty1, 0.0)

    def test_objective_2_queue_length(self):
        """Obj 2 rewards GREEN phases proportional to queue length."""
        w = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
        state = {0: {**self.dummy_state[0], 'queue_length': 10.0}}
        Q = build_qubo(state, w, A=0.0)
        # Should be a negative term on diagonal for NS (0) and EW (1)
        self.assertLess(Q.get((0, 0), 0.0), 0.0)
        self.assertLess(Q.get((1, 1), 0.0), 0.0)
        self.assertEqual(Q.get((2, 2), 0.0), 0.0)

    def test_objective_3_congestion(self):
        """Obj 3 rewards GREEN phases based on density."""
        w = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
        Q = build_qubo(self.dummy_state, w, A=0.0)
        self.assertLess(Q.get((0, 0), 0.0), 0.0)
        self.assertLess(Q.get((1, 1), 0.0), 0.0)

    def test_objective_4_emergency_zero_when_none(self):
        """Emergency term is exactly zero when no corridor is passed in."""
        w = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        Q = build_qubo(self.dummy_state, w, emergency_corridor=None, A=0.0)
        # Without corridor, Q should be empty since all other weights are 0
        self.assertEqual(len(Q), 0)

    def test_objective_4_emergency_reward(self):
        """Emergency term correctly rewards specified corridor."""
        w = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        # Emergency requires NS_GREEN (phase 1) at node 0
        Q = build_qubo(self.dummy_state, w, emergency_corridor={0: 1}, A=0.0)
        # Phase 1 corresponds to index 0. It should have a negative (reward) weight
        self.assertLess(Q.get((0, 0), 0.0), 0.0)

    def test_objective_5_fuel_emissions(self):
        """Obj 5 rewards maintaining the current phase."""
        w = [0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        Q = build_qubo(self.dummy_state, w, A=0.0)
        # Current phase is NS_GREEN (index 0)
        self.assertLess(Q.get((0, 0), 0.0), 0.0)
        self.assertEqual(Q.get((1, 1), 0.0), 0.0)

    def test_objective_6_throughput(self):
        """Obj 6 rewards GREEN phases based on capacity."""
        w = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
        Q = build_qubo(self.dummy_state, w, A=0.0)
        self.assertLess(Q.get((0, 0), 0.0), 0.0)
        self.assertLess(Q.get((1, 1), 0.0), 0.0)

    def test_qubo_to_ising(self):
        """Verify QUBO to Ising mapping is correct."""
        Q = {(0, 0): -2.0, (1, 1): 4.0, (0, 1): 8.0}
        J, h, offset = qubo_to_ising(Q)
        # Q_00 = -2, Q_11 = 4, Q_01 = 8
        # offset = -2/2 + 4/2 + 8/4 = -1 + 2 + 2 = 3
        # h_0 = -(-2)/2 - 8/4 = 1 - 2 = -1
        # h_1 = -(4)/2 - 8/4 = -2 - 2 = -4
        # J_01 = 8/4 = 2
        self.assertEqual(offset, 3.0)
        self.assertEqual(h[0], -1.0)
        self.assertEqual(h[1], -4.0)
        self.assertEqual(J[(0, 1)], 2.0)

if __name__ == '__main__':
    unittest.main()
