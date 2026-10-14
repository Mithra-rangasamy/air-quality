import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
import sys
import os

# Add the project root to the Python path so we can import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from network.model import TrafficNetwork, SignalPhase
from events.manager import EventScheduler, EmergencyVehicleEvent
from solvers import qaoa_solver, fixed_timing_baseline, rule_based_baseline
from environment.metrics import (
    estimate_waiting_time, 
    estimate_throughput, 
    estimate_fuel_consumption, 
    estimate_co2_emissions
)

def draw_network(net, state, plan, emergency_corridor):
    # node positions in a simple grid
    pos = {
        0: (0, 1), 1: (1, 1), 2: (2, 1),
        3: (0, 0), 4: (1, 0), 5: (2, 0)
    }
    
    # normal edges
    edge_x = []
    edge_y = []
    for edge in net.graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines')

    # emergency corridor edges
    emg_edge_x = []
    emg_edge_y = []
    if emergency_corridor:
        active_nodes = list(emergency_corridor.keys())
        for u in active_nodes:
            for v in active_nodes:
                if u < v and net.graph.has_edge(u, v):
                    x0, y0 = pos[u]
                    x1, y1 = pos[v]
                    emg_edge_x.extend([x0, x1, None])
                    emg_edge_y.extend([y0, y1, None])
                    
    emg_edge_trace = go.Scatter(
        x=emg_edge_x, y=emg_edge_y,
        line=dict(width=8, color='rgba(255, 0, 0, 0.6)'),
        hoverinfo='none',
        mode='lines',
        name='Emergency Corridor'
    )

    # nodes
    node_x = []
    node_y = []
    node_color = []
    node_text = []
    
    for node in net.graph.nodes():
        node_x.append(pos[node][0])
        node_y.append(pos[node][1])
        density = state[node]['traffic_density']
        node_color.append(density)
        ns_q = state[node].get('queue_length_ns', 0)
        ew_q = state[node].get('queue_length_ew', 0)
        phase_str = plan[node].name if plan and node in plan else "N/A"
        node_text.append(
            f"Node {node}<br>Density: {density:.2f}<br>"
            f"NS Queue: {ns_q:.1f}, EW Queue: {ew_q:.1f}<br>"
            f"Assigned Phase: {phase_str}"
        )
        
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=[str(n) for n in net.graph.nodes()],
        textposition="middle center",
        textfont=dict(color="white"),
        hovertext=node_text,
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
            reversescale=False,
            color=node_color,
            size=40,
            colorbar=dict(
                thickness=15,
                title='Traffic Density',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
            
    traces = [edge_trace, node_trace]
    if emergency_corridor:
        traces.insert(1, emg_edge_trace)

    fig = go.Figure(data=traces,
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0,l=0,r=0,t=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=300
             )
    )
    return fig

def generate_why_text(state, plan, emergency_corridor):
    reasons = []
    for node, p in plan.items():
        if emergency_corridor and node in emergency_corridor:
            reasons.append(f"**Node {node}** held `{p.name}` because the **emergency corridor** forced priority on this direction.")
            continue
            
        ns_q = state[node].get('queue_length_ns', 0)
        ew_q = state[node].get('queue_length_ew', 0)
        
        if p == SignalPhase.NS_GREEN and ns_q >= ew_q:
            reasons.append(f"**Node {node}** chose `{p.name}` because its NS queue ({ns_q:.1f}) was higher/equal to its EW queue ({ew_q:.1f}).")
        elif p == SignalPhase.EW_GREEN and ew_q > ns_q:
            reasons.append(f"**Node {node}** chose `{p.name}` because its EW queue ({ew_q:.1f}) was higher than its NS queue ({ns_q:.1f}).")
        else:
            reasons.append(f"**Node {node}** chose `{p.name}` to holistically balance the QUBO objectives (throughput, emissions, wait time).")
            
    return "\n- " + "\n- ".join(reasons)

def calculate_solver_metrics(state, plan, dt=1.0):
    w = estimate_waiting_time(state, plan, dt)
    t = estimate_throughput(state, plan, dt)
    f = estimate_fuel_consumption(w)
    c = estimate_co2_emissions(f)
    return w, t, f, c

def init_simulation():
    net = TrafficNetwork()
    # Initialize some baseline congestion for the demo
    for node in net.graph.nodes:
        net.graph.nodes[node]['queue_length_ns'] = 50.0
        net.graph.nodes[node]['queue_length_ew'] = 10.0
        net.graph.nodes[node]['queue_length'] = 60.0
        net.graph.nodes[node]['traffic_density'] = 0.6
        
    scheduler = EventScheduler(net)
    ev_event = EmergencyVehicleEvent(0, 2, net, time_per_edge=1.0)
    scheduler.schedule(1.0, ev_event) # triggers at t=1
    return net, scheduler

def render_state(placeholder, net, scheduler, t):
    weights = [1.0, 2.0, 1.0, 50.0, 1.0, 1.0] 
    
    # Step simulation logically
    scheduler.step(t, dt=1.0)
    corridor = scheduler.get_current_emergency_corridor()
    state = net.get_network_state(t)
    
    # Propagate queues for solver input
    for node in state:
        state[node]['queue_length_ns'] = net.graph.nodes[node]['queue_length_ns']
        state[node]['queue_length_ew'] = net.graph.nodes[node]['queue_length_ew']
        
    # 1. Solve Network with all 3 solvers
    plan_ft, c_ft, _ = fixed_timing_baseline.solve(state, weights, corridor)
    plan_rb, c_rb, _ = rule_based_baseline.solve(state, weights, corridor)
    # Using 500 shots for faster UI rendering during live updates
    plan_qa, c_qa, _ = qaoa_solver.solve(state, weights, corridor, shots=500)
    
    # 2. Calculate metrics
    dt = 1.0
    w_ft, thr_ft, f_ft, co2_ft = calculate_solver_metrics(state, plan_ft, dt)
    w_rb, thr_rb, f_rb, co2_rb = calculate_solver_metrics(state, plan_rb, dt)
    w_qa, thr_qa, f_qa, co2_qa = calculate_solver_metrics(state, plan_qa, dt)
    
    # Prepare table data
    current_signals = {n: state[n]['current_signal_phase'].name.replace("_GREEN", "") for n in range(6)}
    optimized_signals = {n: plan_qa[n].name.replace("_GREEN", "") for n in range(6)}
    
    with placeholder.container():
        st.header(f"⏱️ Simulation Time: t = {t}")
        if corridor:
            st.error(f"🚨 **EMERGENCY VEHICLE ACTIVE!** Prioritizing corridor nodes: {list(corridor.keys())}")
        else:
            st.success("✅ **Normal Operation** (Adaptive Baseline)")
            
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.subheader("1. & 2. & 4. Road Network & Traffic Density")
            fig = draw_network(net, state, plan_qa, corridor)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("8. Classical vs. Quantum Results")
            results_df = pd.DataFrame({
                "Solver": ["Fixed Timing", "Rule-Based", "QAOA (Quantum)"],
                "QUBO Cost": [c_ft, c_rb, c_qa],
                "Wait Time (veh-s)": [w_ft, w_rb, w_qa],
                "Throughput (veh)": [thr_ft, thr_rb, thr_qa],
                "Fuel (gal)": [f_ft, f_rb, f_qa],
                "CO2 (kg)": [co2_ft, co2_rb, co2_qa]
            }).set_index("Solver")
            st.dataframe(results_df.style.highlight_min(subset=["QUBO Cost", "Wait Time (veh-s)", "Fuel (gal)", "CO2 (kg)"], color='lightgreen')
                                       .highlight_max(subset=["Throughput (veh)"], color='lightgreen'), 
                         use_container_width=True)
            
            st.info("**Why did QAOA choose this plan?**" + generate_why_text(state, plan_qa, corridor))
            
        with col2:
            st.subheader("3. Current vs Optimized Signals")
            sig_df = pd.DataFrame({
                "Node": list(range(6)),
                "Before (Current)": list(current_signals.values()),
                "After (QAOA)": list(optimized_signals.values())
            }).set_index("Node")
            st.dataframe(sig_df, use_container_width=True)
            
            st.subheader("5. Queue Lengths")
            q_df = pd.DataFrame({
                "Node": list(range(6)),
                "NS Queue": [state[n]['queue_length_ns'] for n in range(6)],
                "EW Queue": [state[n]['queue_length_ew'] for n in range(6)]
            }).set_index("Node")
            st.bar_chart(q_df)
            
            st.subheader("6. Waiting Time (Before vs After)")
            w_df = pd.DataFrame({
                "Baseline (Fixed)": [w_ft],
                "Optimized (QAOA)": [w_qa]
            }, index=["Wait Time (veh-seconds)"])
            st.bar_chart(w_df.T)
            
            st.subheader("7. Environmental Estimates")
            f_delta = f_qa - f_ft
            c_delta = co2_qa - co2_ft
            m1, m2 = st.columns(2)
            m1.metric("Fuel Consumption (QAOA)", f"{f_qa:.4f} gal", f"{f_delta:.4f} gal (vs Fixed)", delta_color="inverse")
            m2.metric("CO2 Emissions (QAOA)", f"{co2_qa:.4f} kg", f"{c_delta:.4f} kg (vs Fixed)", delta_color="inverse")
        
    # Apply the QAOA plan to physically progress the network for the next timestep
    net.apply_signal_plan(plan_qa, dt=1.0)


def app():
    st.set_page_config(layout="wide", page_title="Hybrid Quantum Traffic Optimization")
    st.title("🚦 Hybrid Quantum-Classical Traffic Optimization Platform")
    
    st.markdown("""
    **Note on Environmental Estimates:** All fuel and CO2 metrics shown in this dashboard 
    are illustrative estimates derived from simulation idle time and throughput. 
    They are NOT from real sensor data and serve only to demonstrate the optimization logic.
    """)
    
    placeholder = st.empty()
    
    if st.button("▶️ Run Simulation with Emergency Event", type="primary"):
        net, scheduler = init_simulation()
        for t in range(5):
            render_state(placeholder, net, scheduler, float(t))
            time.sleep(2.5) # Pause to let user see the live dashboard update
    else:
        # Just render initial static state at t=0
        net, scheduler = init_simulation()
        render_state(placeholder, net, scheduler, 0.0)

if __name__ == "__main__":
    app()
