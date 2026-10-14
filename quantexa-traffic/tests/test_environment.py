import unittest
from network.model import SignalPhase
from environment.metrics import (
    estimate_waiting_time,
    estimate_throughput,
    estimate_fuel_consumption,
    estimate_co2_emissions,
    compare_before_after,
    FUEL_RATE_K,
    CO2_RATE_C
)

class TestEnvironmentMetrics(unittest.TestCase):
    def setUp(self):
        # Setup a sample network state with a heavy NS queue
        self.state = {
            0: {
                'queue_length_ns': 100.0,
                'queue_length_ew': 10.0,
                'road_capacity': 60.0, # 1 vehicle per second (60 per min)
                'current_signal_phase': SignalPhase.NS_GREEN
            }
        }
        
    def test_impact_correlations(self):
        """
        Verify that a plan with lower total queue length (i.e. clears more queue)
        produces lower waiting-time, fuel, and CO2 estimates than a plan with 
        higher queue length, holding everything else constant.
        """
        # Plan 1 (Optimized): NS_GREEN - serves the heavy queue of 100
        plan_opt = {0: SignalPhase.NS_GREEN}
        
        # Plan 2 (Poor Baseline): ALL_RED - serves 0 queue
        plan_base = {0: SignalPhase.ALL_RED_PEDESTRIAN}
        
        # dt=60 seconds means 1 minute.
        # Outflow for NS_GREEN will be (60 / 60) * 60 = 60 vehicles cleared.
        dt = 60.0
        
        comp = compare_before_after(plan_base, plan_opt, self.state, dt)
        
        # Throughput
        self.assertGreater(comp['throughput']['optimized'], comp['throughput']['baseline'])
        
        # Waiting Time
        w_opt = comp['waiting_time']['optimized']
        w_base = comp['waiting_time']['baseline']
        self.assertLess(w_opt, w_base)
        
        # Fuel
        f_opt = comp['fuel_consumption']['optimized']
        f_base = comp['fuel_consumption']['baseline']
        self.assertLess(f_opt, f_base)
        
        # CO2
        c_opt = comp['co2_emissions']['optimized']
        c_base = comp['co2_emissions']['baseline']
        self.assertLess(c_opt, c_base)

        # Exact value checks based on our linear proxy to ensure constants are used
        expected_w_base = (100.0 + 10.0) * dt # 110 * 60 = 6600 vehicle-seconds wait
        self.assertAlmostEqual(w_base, expected_w_base)
        self.assertAlmostEqual(f_base, expected_w_base * FUEL_RATE_K)
        self.assertAlmostEqual(c_base, expected_w_base * FUEL_RATE_K * CO2_RATE_C)
        
if __name__ == '__main__':
    unittest.main()
