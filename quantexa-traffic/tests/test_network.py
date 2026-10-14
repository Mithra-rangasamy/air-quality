import unittest
from network.model import TrafficNetwork, SignalPhase

class TestTrafficNetwork(unittest.TestCase):
    def test_network_initialization(self):
        """Test that the network initializes correctly with required properties."""
        net = TrafficNetwork()
        self.assertEqual(len(net.graph.nodes), 6)
        self.assertGreater(len(net.graph.edges), 0)
        
        # Check that each intersection has the required attributes
        for node in net.graph.nodes:
            attrs = net.graph.nodes[node]
            self.assertIn('traffic_density', attrs)
            self.assertIn('queue_length', attrs)
            self.assertIn('road_capacity', attrs)
            self.assertIn('current_signal_phase', attrs)
            self.assertIn('pedestrian_flag', attrs)
            self.assertIsInstance(attrs['current_signal_phase'], SignalPhase)

    def test_rush_hour_curve(self):
        """Test that the rush-hour curve produces sensible values."""
        net = TrafficNetwork()
        val_0 = net.generate_rush_hour_curve(0, peak_time=30, spread=10, max_density=50)
        val_30 = net.generate_rush_hour_curve(30, peak_time=30, spread=10, max_density=50)
        val_60 = net.generate_rush_hour_curve(60, peak_time=30, spread=10, max_density=50)
        
        # Peak density (t=30) should be higher than edges (t=0 and t=60)
        self.assertGreater(val_30, val_0)
        self.assertGreater(val_30, val_60)
        
        # Values should be sensible and non-negative
        self.assertTrue(val_30 > 0)
        self.assertTrue(val_0 > 0)
        
        # Peak should roughly equal baseline + max_density
        self.assertAlmostEqual(val_30, 60.0)

    def test_apply_signal_plan(self):
        """Test that apply_signal_plan correctly updates queue lengths."""
        net = TrafficNetwork()
        
        # Set initial queues high enough so we can observe a clear reduction
        for node in net.graph.nodes:
            net.graph.nodes[node]['queue_length_ns'] = 50.0
            net.graph.nodes[node]['queue_length_ew'] = 50.0
            net.graph.nodes[node]['queue_length'] = 100.0
            net.graph.nodes[node]['traffic_density'] = 1.0
        
        # Apply a plan with different phases for different nodes
        plan = {
            0: SignalPhase.NS_GREEN,
            1: SignalPhase.EW_GREEN,
            2: SignalPhase.ALL_RED_PEDESTRIAN
        }
        
        # Step the simulation by dt=10 to see noticeable changes
        net.apply_signal_plan(plan, dt=10)
        
        # Node 0 (NS_GREEN): NS queue should decrease, EW queue should increase
        node0_ns = net.graph.nodes[0]['queue_length_ns']
        node0_ew = net.graph.nodes[0]['queue_length_ew']
        self.assertLess(node0_ns, 50.0)
        self.assertGreater(node0_ew, 50.0)
        
        # Node 1 (EW_GREEN): EW queue should decrease, NS queue should increase
        node1_ns = net.graph.nodes[1]['queue_length_ns']
        node1_ew = net.graph.nodes[1]['queue_length_ew']
        self.assertGreater(node1_ns, 50.0)
        self.assertLess(node1_ew, 50.0)
        
        # Node 2 (ALL_RED_PEDESTRIAN): Both queues should increase equally
        node2_ns = net.graph.nodes[2]['queue_length_ns']
        node2_ew = net.graph.nodes[2]['queue_length_ew']
        self.assertGreater(node2_ns, 50.0)
        self.assertGreater(node2_ew, 50.0)
        self.assertEqual(node2_ns, node2_ew)
        
        # Check pedestrian flag update
        self.assertTrue(net.graph.nodes[2]['pedestrian_flag'])
        self.assertFalse(net.graph.nodes[0]['pedestrian_flag'])
        
        # Test get_network_state function
        state = net.get_network_state(net.current_time)
        self.assertEqual(len(state), 6)
        self.assertEqual(state[0]['current_signal_phase'], SignalPhase.NS_GREEN)
        self.assertEqual(state[1]['current_signal_phase'], SignalPhase.EW_GREEN)

if __name__ == '__main__':
    unittest.main()
