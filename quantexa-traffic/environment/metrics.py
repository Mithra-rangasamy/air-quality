"""
ENVIRONMENTAL IMPACT ESTIMATION
-------------------------------
NOTE: All values calculated in this module are derived from the 
simulation state and solver outputs. They are NOT from real sensor data.
These functions use documented linear proxies to demonstrate capability, 
and all resulting metrics should be clearly labeled as "estimates" in the UI.
"""

from network.model import SignalPhase

# k: illustrative fuel consumption rate per unit of idle time 
# (e.g. gallons per vehicle-minute of waiting).
# NOT MEASURED DATA. Illustrative assumption for demo purposes.
FUEL_RATE_K = 0.005 

# c: illustrative CO2 conversion rate from fuel consumed 
# (e.g. kg CO2 per gallon).
# NOT MEASURED DATA. Illustrative assumption for demo purposes.
CO2_RATE_C = 2.31 

def estimate_waiting_time(network_state, plan, dt=1.0):
    """
    Estimates total waiting time across all intersections over the simulated time window (dt).
    Calculated as the sum of remaining queue lengths (vehicles) multiplied by dt.
    """
    total_wait = 0.0
    for node, state in network_state.items():
        ns_queue = state.get('queue_length_ns', 0.0)
        ew_queue = state.get('queue_length_ew', 0.0)
        
        phase = plan.get(node, state['current_signal_phase'])
        
        # Calculate how much queue is cleared by this phase during dt
        outflow = (state['road_capacity'] / 60.0) * dt
        
        if phase == SignalPhase.NS_GREEN:
            ns_queue = max(0, ns_queue - outflow)
        elif phase == SignalPhase.EW_GREEN:
            ew_queue = max(0, ew_queue - outflow)
            
        # The remaining vehicles idle for the duration of the time step
        total_wait += (ns_queue + ew_queue) * dt
        
    return total_wait

def estimate_throughput(network_state, plan, dt=1.0):
    """
    Estimates total vehicles cleared per cycle (derived from capacity and selected green phases).
    """
    total_cleared = 0.0
    for node, state in network_state.items():
        ns_queue = state.get('queue_length_ns', 0.0)
        ew_queue = state.get('queue_length_ew', 0.0)
        
        phase = plan.get(node, state['current_signal_phase'])
        outflow = (state['road_capacity'] / 60.0) * dt
        
        if phase == SignalPhase.NS_GREEN:
            total_cleared += min(ns_queue, outflow)
        elif phase == SignalPhase.EW_GREEN:
            total_cleared += min(ew_queue, outflow)
            
    return total_cleared

def estimate_fuel_consumption(waiting_time):
    """
    fuel_estimate = k * idle_time
    Idle time is equivalent to the waiting time calculated above.
    """
    return FUEL_RATE_K * waiting_time

def estimate_co2_emissions(fuel_estimate):
    """
    co2_estimate = c * fuel_estimate
    """
    return CO2_RATE_C * fuel_estimate

def compare_before_after(baseline_plan, optimized_plan, network_state, dt=1.0):
    """
    Returns all four metrics for both plans so the dashboard can show deltas.
    """
    # Baseline Metrics
    w_base = estimate_waiting_time(network_state, baseline_plan, dt)
    t_base = estimate_throughput(network_state, baseline_plan, dt)
    f_base = estimate_fuel_consumption(w_base)
    c_base = estimate_co2_emissions(f_base)
    
    # Optimized Metrics
    w_opt = estimate_waiting_time(network_state, optimized_plan, dt)
    t_opt = estimate_throughput(network_state, optimized_plan, dt)
    f_opt = estimate_fuel_consumption(w_opt)
    c_opt = estimate_co2_emissions(f_opt)
    
    return {
        'waiting_time': {'baseline': w_base, 'optimized': w_opt},
        'throughput': {'baseline': t_base, 'optimized': t_opt},
        'fuel_consumption': {'baseline': f_base, 'optimized': f_opt},
        'co2_emissions': {'baseline': c_base, 'optimized': c_opt}
    }
