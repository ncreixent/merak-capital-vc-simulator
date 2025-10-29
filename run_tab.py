# run_tab.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io
import base64

from ui_components import (
    render_metric_cards,
    render_irr_histogram,
    render_time_to_exit_chart,
    render_success_rate_by_stage,
    render_waterfall_breakdown
)
from auth import check_user_permissions

def render_run_tab():
    """Render the Run & Analyze tab"""
    st.markdown("<h1 class='main-header'>Run & Analyze Simulation</h1>", unsafe_allow_html=True)
    
    # Scenario selector
    scenario_names = list(st.session_state.scenarios.keys())
    
    if not scenario_names:
        st.warning("No scenarios available. Please create a scenario in the Scenario Management tab or load the default scenario.")
        
        # Debug info
        st.write("**Debug Info:**")
        st.write(f"- Session state scenarios: {list(st.session_state.scenarios.keys())}")
        st.write(f"- Default loaded flag: {st.session_state.get('default_loaded', 'Not set')}")
        st.write(f"- Current scenario name: {st.session_state.get('current_scenario_name', 'Not set')}")
        
        if st.button("Load Default Scenario"):
            load_and_set_default()
            st.rerun()
        
        return
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get current index to avoid unnecessary updates
        current_index = 0
        if st.session_state.current_scenario_name and st.session_state.current_scenario_name in scenario_names:
            current_index = scenario_names.index(st.session_state.current_scenario_name)
        
        selected_scenario_name = st.selectbox(
            "Select Scenario to Run",
            options=scenario_names,
            index=current_index,
            key="scenario_selector"  # Add key to prevent unnecessary re-renders
        )
        
        # Only update if selection actually changed
        if selected_scenario_name != st.session_state.current_scenario_name:
            st.session_state.current_scenario_name = selected_scenario_name
    
    with col2:
        st.write("")
        st.write("")
        if st.button("Refresh Scenarios", use_container_width=True):
            st.rerun()
    
    scenario = st.session_state.scenarios[selected_scenario_name]
    
    # Check if scenario has been run
    has_results = scenario['results'] is not None
    
    if not has_results:
        # Check user permissions for running simulations
        user_permissions = check_user_permissions(st.session_state.username)
        
        if 'run_simulations' not in user_permissions:
            st.warning("🔒 **Access Restricted**: You don't have permission to run simulations. Contact your administrator for access.")
            st.info("💡 You can still view existing simulation results.")
            return
        
        render_run_interface(scenario)
    else:
        render_results_interface(scenario)

def render_run_interface(scenario):
    """Render interface for running a scenario"""
    st.markdown("---")
    st.subheader("⚙️ Simulation Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_simulations = st.number_input(
            "Number of Simulations",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            help="More simulations = more accurate but slower"
        )
    
    with col2:
        use_seed = st.checkbox(
            "Use Random Seed",
            value=True,
            help="Enable for reproducible results"
        )
        
        if use_seed:
            seed = st.number_input(
                "Random Seed",
                min_value=0,
                max_value=999999,
                value=421,
                step=1
            )
        else:
            seed = None
    
    with col3:
        st.write("")
        st.write("")
        run_quick = st.checkbox(
            "Quick Run (100 sims)",
            value=False,
            help="Run with 100 simulations for faster results"
        )
        
        if run_quick:
            num_simulations = 100
    
    st.markdown("---")
    
    # Run button
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button("Run Simulation", use_container_width=True, type="primary"):
            run_simulation(scenario, num_simulations, seed)

def run_simulation(scenario, num_simulations, seed):
    """Execute simulation with progress bar"""
    
    # Check user permissions
    user_permissions = check_user_permissions(st.session_state.username)
    if 'run_simulations' not in user_permissions:
        st.error("❌ Access denied: You don't have permission to run simulations.")
        return
    
    from scenario_manager import ScenarioManager
    
    with st.spinner(f'Running {num_simulations} simulations... This may take a minute.'):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Initializing simulation...")
        progress_bar.progress(10)
        
        # Run the simulation
        success, message = ScenarioManager.run_scenario(scenario, num_simulations, seed)
        
        if success:
            progress_bar.progress(100)
            status_text.text("Simulation complete!")
            st.success(message)
            st.balloons()
            
            # Auto-rerun to show results
            st.rerun()
        else:
            progress_bar.empty()
            status_text.empty()
            st.error(message)

def render_results_interface(scenario):
    """Render results analysis interface"""
    from scenario_manager import ScenarioManager
    
    # Get metrics (will use cache if available)
    metrics = ScenarioManager.calculate_metrics(scenario)
    
    if metrics is None:
        st.error("Unable to calculate metrics from results")
        return
    
    # Results header with download options
    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
    
    with col1:
        st.markdown(f"### Results: {scenario['name']}")
        st.caption(f"Run date: {scenario['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    
    with col2:
        if st.button("Re-run", use_container_width=True):
            scenario['results'] = None
            scenario['cached_metrics'] = None
            
            # Clear download caches for this scenario
            excel_cache_key = f"excel_{scenario['name']}_{scenario['timestamp'].isoformat()}"
            package_cache_key = f"package_{scenario['name']}_{scenario['timestamp'].isoformat()}"
            
            if excel_cache_key in st.session_state:
                del st.session_state[excel_cache_key]
            if package_cache_key in st.session_state:
                del st.session_state[package_cache_key]
            
            st.rerun()
    
    with col3:
        # Download Excel - use pre-generated for default scenario, cache for others
        excel_buffer = None
        
        if 'excel_buffer' in scenario and scenario['excel_buffer'] is not None:
            # Default scenario has pre-generated Excel file
            excel_buffer = scenario['excel_buffer']
        else:
            # Other scenarios - cache the buffer to avoid regenerating
            excel_cache_key = f"excel_{scenario['name']}_{scenario['timestamp'].isoformat()}"
            
            if excel_cache_key not in st.session_state:
                # Generate Excel buffer only once and cache it
                with st.spinner("Preparing Excel download..."):
                    excel_buffer = generate_excel_download(scenario)
                    st.session_state[excel_cache_key] = excel_buffer
            else:
                excel_buffer = st.session_state[excel_cache_key]
        
        if excel_buffer:
            st.download_button(
                label="Excel",
                data=excel_buffer,
                file_name=f"{scenario['name']}_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col4:
        # Download scenario package - cache the buffer to avoid regenerating
        package_cache_key = f"package_{scenario['name']}_{scenario['timestamp'].isoformat()}"
        
        if package_cache_key not in st.session_state:
            # Generate package buffer only once and cache it
            with st.spinner("Preparing scenario package..."):
                scenario_zip = generate_scenario_package(scenario)
                st.session_state[package_cache_key] = scenario_zip
        
        scenario_zip = st.session_state[package_cache_key]
        if scenario_zip:
            st.download_button(
                label="Package",
                data=scenario_zip,
                file_name=f"{scenario['name']}_package.zip",
                mime="application/zip",
                use_container_width=True
            )
    
    with col5:
        # Refresh metrics button
        if st.button("Refresh Metrics", use_container_width=True, help="Recalculate metrics from existing results"):
            scenario['cached_metrics'] = None
            st.success("Cache cleared! Metrics will be recalculated.")
            st.rerun()
    
    st.markdown("---")
    
    # Key Metrics Cards
    st.subheader("Key Performance Metrics")
    
    # Show cache status prominently
    cache_status = "Cached" if scenario.get('cached_metrics') is not None else "Calculated"
    # Metrics are loaded silently - no need to show status messages
    
    render_metric_cards(metrics)
    
    st.markdown("---")
    
    # Main visualizations
    tab1, tab2, tab3 = st.tabs([
        "Distributions",
        "Exit Analysis",
        "Waterfall Details"
    ])
    
    with tab1:
        render_distribution_tab(scenario, metrics)
    
    with tab2:
        render_time_analysis_tab(scenario)
    
    with tab3:
        render_waterfall_tab(scenario)

def render_distribution_tab(scenario, metrics):
    """Render distribution analysis tab"""
    st.subheader("Return Distributions")
    
    # IRR Distribution
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig_irr = render_irr_histogram(scenario['results'], "Net IRR Distribution")
        st.plotly_chart(fig_irr, use_container_width=True)
    
    with col2:
        st.markdown("#### Distribution Statistics")
        
        df_results = pd.DataFrame([vars(res) for res in scenario['results']])
        
        percentiles = df_results['net_irr'].quantile([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
        
        stats_data = {
            'Percentile': ['P5', 'P10', 'P25', 'P50 (Median)', 'P75', 'P90', 'P95'],
            'Net IRR': [f"{v:.2%}" for v in percentiles.values]
        }
        
        st.dataframe(
            pd.DataFrame(stats_data),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("#### Risk Metrics")
        st.metric("Value at Risk (5%)", f"{metrics['var_5']:.2%}")
        st.metric("Value at Risk (10%)", f"{metrics['var_10']:.2%}")
    
    st.markdown("---")
    
    # Multiple Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Net Multiple Distribution")
        fig_multiple = render_histogram(
            df_results['net_multiple'],
            "Net Multiple",
            "Frequency",
            metrics['median_net_multiple']
        )
        st.plotly_chart(fig_multiple, use_container_width=True)
    
    with col2:
        st.markdown("#### Gross IRR Distribution")
        gross_irr_data = df_results[df_results['gross_irr'] > -0.99]['gross_irr'] * 100
        fig_gross = render_histogram(
            gross_irr_data,
            "Gross IRR (%)",
            "Frequency",
            metrics['median_gross_irr'] * 100
        )
        st.plotly_chart(fig_gross, use_container_width=True)

def calculate_key_metrics(scenario):
    """Calculate key metrics for the overview section"""
    if not scenario['results']:
        return {
            'portfolio_size': 0,
            'success_rate': 0,
            'avg_investment': 0
        }
    
    # Calculate portfolio size
    portfolio_sizes = [len(res.company_results) for res in scenario['results']]
    avg_portfolio_size = sum(portfolio_sizes) / len(portfolio_sizes)
    
    # Calculate success rate
    all_companies = []
    for res in scenario['results']:
        all_companies.extend(res.company_results)
    
    if all_companies:
        exited_companies = sum(1 for company in all_companies if company.outcome == 'exited')
        success_rate = (exited_companies / len(all_companies)) * 100
    else:
        success_rate = 0
    
    # Calculate average investment
    all_investments = []
    for res in scenario['results']:
        for company in res.company_results:
            if company.history:
                initial_investment = company.history[0].get('round_investment', 0)
                all_investments.append(initial_investment)
    
    avg_investment = (sum(all_investments) / len(all_investments)) / 1_000_000 if all_investments else 0
    
    return {
        'portfolio_size': avg_portfolio_size,
        'success_rate': success_rate,
        'avg_investment': avg_investment
    }

def render_time_analysis_tab(scenario):
    """Render exit analysis tab with professional design"""
    
    # Add custom CSS for professional styling
    st.markdown("""
    <style>
    .exit-analysis-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .metric-card {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        padding: 24px;
        margin-bottom: 16px;
        border-left: 4px solid #268BA0; /* blue-munsell */
    }
    
    .metric-card h3 {
        color: #1e3a8a;
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 16px 0;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #111827;
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: #6b7280;
        margin: 0;
    }
    
    .section-header {
        color: #1e3a8a;
        font-size: 18px;
        font-weight: 600;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e5e7eb;
    }
    
    .expandable-section {
        background: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 16px;
        overflow: hidden;
    }
    
    .section-toggle {
        background: #f8fafc;
        padding: 16px 24px;
        border-bottom: 1px solid #e5e7eb;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .section-content {
        padding: 24px;
    }
    
    /* Make expander titles bigger */
    .streamlit-expanderHeader {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #0A1A1E !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 1. KEY METRICS SECTION (Always Visible)
    st.markdown('<div class="exit-analysis-container">', unsafe_allow_html=True)
    
    # Add dark grey separator like in Waterfall Details
    st.markdown("""
    <div style="background: #2a2a2a; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3); padding: 1rem; margin: 1rem 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; border: 1px solid #333333;">
        <div style="margin-bottom: 0.5rem;">
            <h2 style="font-size: 1.2rem; font-weight: 600; color: #e0e0e0; margin: 0;">Portfolio Performance Overview</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate key metrics
    key_metrics = calculate_key_metrics(scenario)
    
    # Display key metrics in a 3-column layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Portfolio Size</h3>
            <div class="metric-value">{key_metrics['portfolio_size']:.0f}</div>
            <p class="metric-label">Average companies invested</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Success Rate</h3>
            <div class="metric-value">{key_metrics['success_rate']:.1f}%</div>
            <p class="metric-label">Companies that exited</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Avg Investment</h3>
            <div class="metric-value">${key_metrics['avg_investment']:.1f}M</div>
            <p class="metric-label">Per company</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 2. DETAILED ANALYSIS SECTION (Expandable)
    st.markdown("""
    <div style="background: #2a2a2a; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3); padding: 1rem; margin: 1rem 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; border: 1px solid #333333;">
        <div style="margin-bottom: 0.5rem;">
            <h2 style="font-size: 1.2rem; font-weight: 600; color: #e0e0e0; margin: 0;">Detailed Analysis</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Investment Analysis
    with st.expander("Investment Analysis", expanded=True):
        render_investment_comparison_widget(scenario)
    
    # Portfolio Composition
    with st.expander("Portfolio Composition", expanded=True):
        render_portfolio_composition_widget(scenario)
    
    # Success Rate Analysis
    with st.expander("Success Rate Analysis", expanded=True):
        render_success_rate_widget(scenario)
    
    # Exit Analysis
    with st.expander("Exit Analysis", expanded=True):
        render_exit_size_widget(scenario)
        st.markdown("---")
        render_time_to_exit_widget(scenario)
    
    # Company Outcome Statistics (last item in Detailed Analysis)
    with st.expander("Company Outcome Statistics", expanded=True):
        # Remove the duplicate header from the widget since expander already has the title
        render_outcome_statistics_widget_no_header(scenario)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_portfolio_composition_widget(scenario):
    """Render mean portfolio composition widget"""
    import streamlit.components.v1 as components
    
    # Aggregate all companies from all simulations
    all_companies = []
    for sim_idx, res in enumerate(scenario['results']):
        for company in res.company_results:
            if company.history:
                initial_stage = company.history[0].get('stage', 'Unknown')
                all_companies.append({
                    'simulation': sim_idx + 1,
                    'initial_stage': initial_stage
                })
    
    df_companies = pd.DataFrame(all_companies)
    
    if df_companies.empty:
        st.warning("No company data available")
        return
    
    # Calculate average count by stage across all simulations
    stage_counts = df_companies.groupby(['simulation', 'initial_stage']).size().reset_index(name='count')
    avg_counts = stage_counts.groupby('initial_stage')['count'].mean().reset_index()
    
    # Create professional bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=avg_counts['initial_stage'],
        y=avg_counts['count'],
        marker_color=['#268BA0', '#024761', '#0A1A1E'],  # Merak Capital color scheme
        text=[f"{count:.1f}" for count in avg_counts['count']],
        textposition='outside',
        textfont=dict(size=12, color='#0A1A1E'),
        marker_line_width=0
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="Investment Stage",
        yaxis_title="Average Count",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size=12),
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(
            title_font=dict(size=14, color='#AFB9BD'),
            tickfont=dict(size=12, color='#0A1A1E'),
            gridcolor='#F3F3F3',
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            title_font=dict(size=14, color='#AFB9BD'),
            tickfont=dict(size=12, color='#0A1A1E'),
            gridcolor='#F3F3F3',
            showline=False,
            zeroline=False
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_investment_comparison_widget(scenario):
    """Render average investment comparison widget"""
    import streamlit.components.v1 as components
    
    # Aggregate all companies from all simulations
    all_companies = []
    for sim_idx, res in enumerate(scenario['results']):
        for company in res.company_results:
            if company.history:
                initial_stage = company.history[0].get('stage', 'Unknown')
                initial_investment = company.history[0].get('round_investment', 0)
                all_companies.append({
                    'simulation': sim_idx + 1,
                    'initial_stage': initial_stage,
                    'initial_investment': initial_investment,
                    'total_invested': company.total_invested
                })
    
    df_companies = pd.DataFrame(all_companies)
    
    if df_companies.empty:
        st.warning("No company data available")
        return
    
    # Calculate averages by stage
    stage_averages = df_companies.groupby('initial_stage').agg({
        'initial_investment': 'mean',
            'total_invested': 'mean'
        }).reset_index()
        
    # Create professional grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Initial Investment',
        x=stage_averages['initial_stage'],
        y=stage_averages['initial_investment'] / 1_000_000,  # Convert to millions
        marker_color='#268BA0',  # blue-munsell
        text=[f"${val/1_000_000:.1f}M" for val in stage_averages['initial_investment']],
        textposition='outside',
        textfont=dict(size=11, color='#0A1A1E'),
        marker_line_width=0
    ))
    
    fig.add_trace(go.Bar(
        name='Total Investment',
        x=stage_averages['initial_stage'],
        y=stage_averages['total_invested'] / 1_000_000,  # Convert to millions
        marker_color='#024761',  # indigo-dye
        text=[f"${val/1_000_000:.1f}M" for val in stage_averages['total_invested']],
        textposition='outside',
        textfont=dict(size=11, color='#0A1A1E'),
        marker_line_width=0
    ))
    
    fig.update_layout(
        title="",
        xaxis_title="Investment Stage",
        yaxis_title="Investment ($M)",
        barmode='group',
        height=400,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size=12),
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color='#0A1A1E')
        ),
        xaxis=dict(
            title_font=dict(size=14, color='#AFB9BD'),
            tickfont=dict(size=12, color='#0A1A1E'),
            gridcolor='#F3F3F3',
            showline=False,
            zeroline=False
        ),
        yaxis=dict(
            title_font=dict(size=14, color='#AFB9BD'),
            tickfont=dict(size=12, color='#0A1A1E'),
            gridcolor='#F3F3F3',
            showline=False,
            zeroline=False
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_success_rate_widget(scenario):
    """Render success rate by stage widget with professional styling"""
    # Use existing success rate chart with professional styling
    fig_success = render_success_rate_by_stage(scenario['results'])
    if fig_success:
        # Update the chart with professional styling
        fig_success.update_layout(
            font_family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis=dict(
                title_font=dict(size=14, color='#AFB9BD'),
                tickfont=dict(size=12, color='#0A1A1E'),
                gridcolor='#F3F3F3',
                showline=False,
                zeroline=False
            ),
            yaxis=dict(
                title_font=dict(size=14, color='#AFB9BD'),
                tickfont=dict(size=12, color='#0A1A1E'),
                gridcolor='#F3F3F3',
                showline=False,
                zeroline=False
            )
        )
        st.plotly_chart(fig_success, use_container_width=True)
    
def render_exit_size_widget(scenario):
    """Render exit size analysis widget"""
    import streamlit.components.v1 as components
    
    # Aggregate all companies from all simulations
    all_companies = []
    for sim_idx, res in enumerate(scenario['results']):
        for company in res.company_results:
            if company.history and company.outcome == 'exited':
                initial_stage = company.history[0].get('stage', 'Unknown')
                all_companies.append({
                    'simulation': sim_idx + 1,
                    'initial_stage': initial_stage,
                    'exit_valuation': company.exit_valuation,
                    'total_invested': company.total_invested,
                    'multiple': company.multiple
                })
    
    df_companies = pd.DataFrame(all_companies)
    
    if df_companies.empty:
        st.warning("No exit data available")
        return
    
    # Calculate averages by stage
    stage_averages = df_companies.groupby('initial_stage').agg({
        'exit_valuation': 'mean',
        'multiple': 'mean'
    }).reset_index()
    
    
    # Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add exit valuation bars
    fig.add_trace(
        go.Bar(
            name='Exit Valuation',
            x=stage_averages['initial_stage'],
            y=stage_averages['exit_valuation'] / 1_000_000,  # Convert to millions
            marker_color='#268BA0',  # blue-munsell
            text=[f"${val/1_000_000:.1f}M" for val in stage_averages['exit_valuation']],
            textposition='inside'
        ),
        secondary_y=False,
    )
    
    # Add multiple line
    fig.add_trace(
        go.Scatter(
            name='Multiple',
            x=stage_averages['initial_stage'],
            y=stage_averages['multiple'],
            mode='lines+markers+text',
            line=dict(color='#024761', width=3),  # indigo-dye
            marker=dict(size=8),
            text=[f"{val:.1f}x" for val in stage_averages['multiple']],
            textposition='top center',
            textfont=dict(size=12, color='#024761')  # indigo-dye
        ),
        secondary_y=True,
    )
    
    # Update layout
    fig.update_layout(
        title="",
        xaxis_title="Stage",
        height=400,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif", size=12),
        xaxis=dict(showline=False, zeroline=False),
        yaxis=dict(showline=False, zeroline=False)
    )
    
    # Set y-axes titles
    fig.update_yaxes(title_text="Exit Valuation ($M)", secondary_y=False)
    fig.update_yaxes(title_text="Multiple", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

def render_time_to_exit_widget(scenario):
    """Render time to exit analysis widget"""
    import streamlit.components.v1 as components
    
    
    # Use existing time to exit chart
    fig_time = render_time_to_exit_chart(scenario['results'])
    if fig_time:
        st.plotly_chart(fig_time, use_container_width=True)

def render_outcome_statistics_widget(scenario):
    """Render outcome statistics widget"""
    import streamlit.components.v1 as components
    
    # Aggregate all companies from all simulations
    all_companies = []
    for sim_idx, res in enumerate(scenario['results']):
        for company in res.company_results:
            if company.history:
                initial_stage = company.history[0].get('stage', 'Unknown')
                initial_valuation = company.history[0].get('valuation', 0)
                initial_investment = company.history[0].get('round_investment', 0)
                all_companies.append({
                    'simulation': sim_idx + 1,
                    'initial_stage': initial_stage,
                    'outcome': company.outcome,
                    'initial_valuation': initial_valuation,
                    'initial_investment': initial_investment,
                    'cumulative_investment': company.total_invested,
                    'exit_valuation': company.exit_valuation if company.outcome == 'exited' else 0,
                    'exit_proceeds': company.exit_proceeds if company.outcome == 'exited' else 0
                })
    
    df_companies = pd.DataFrame(all_companies)
    
    if df_companies.empty:
        st.warning("No company data available")
        return
    
    # Calculate statistics by outcome
    outcome_stats = df_companies.groupby('outcome').agg({
        'simulation': 'count',  # Count of companies using simulation column
        'initial_valuation': 'mean',
        'initial_investment': 'mean',
        'cumulative_investment': 'mean',
        'exit_valuation': 'mean',
        'exit_proceeds': 'mean'
    }).reset_index()
    
    # Rename the count column
    outcome_stats = outcome_stats.rename(columns={'simulation': 'company_count'})
    
    # Calculate ownership percentages
    outcome_stats['initial_ownership'] = outcome_stats['initial_investment'] / outcome_stats['initial_valuation']
    outcome_stats['initial_ownership'] = outcome_stats['initial_ownership'].fillna(0)  # Handle division by zero
    
    outcome_stats['exit_ownership'] = outcome_stats['exit_proceeds'] / outcome_stats['exit_valuation']
    outcome_stats['exit_ownership'] = outcome_stats['exit_ownership'].fillna(0)  # Handle division by zero
    
    # Calculate investment multiple: Exit Proceeds / Cumulative Investment
    outcome_stats['investment_multiple'] = outcome_stats['exit_proceeds'] / outcome_stats['cumulative_investment']
    outcome_stats['investment_multiple'] = outcome_stats['investment_multiple'].fillna(0)  # Handle division by zero
    
    # Create widget header
    widget_html = """
    <div style="background: #2a2a2a; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3); padding: 1.5rem; margin: 1rem 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; border: 1px solid #333333;">
        <div style="margin-bottom: 1rem;">
            <h2 style="font-size: 1.2rem; font-weight: 600; color: #e0e0e0; margin: 0 0 0.5rem 0;">Company Outcome Statistics</h2>
            <p style="color: #999999; margin: 0;">Comprehensive analysis of company performance by outcome</p>
        </div>
    </div>
    """
    
    components.html(widget_html, height=80)
    
    # Create custom HTML table
    table_html = """
    <div style="overflow-x: auto; margin: 1rem 0;">
        <table style="width: 100%; border-collapse: collapse; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'; font-size: 13px;">
            <thead>
                <tr style="border-bottom: 2px solid #e5e7eb; background-color: #f9fafb;">
                    <th style="text-align: left; padding: 10px 12px; font-weight: 600; color: #374151;">Outcome</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Company Count</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Initial Valuation</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Initial Investment</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Initial Ownership</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Exit Valuation</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Exit Ownership</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Cumulative Investment</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Exit Proceeds</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Investment Multiple</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add data rows
    for _, row in outcome_stats.iterrows():
        outcome = row['outcome']
        company_count = int(row['company_count'])
        initial_val = row['initial_valuation'] / 1_000_000  # Convert to millions
        initial_inv = row['initial_investment'] / 1_000_000
        initial_ownership = row['initial_ownership'] * 100  # Convert to percentage
        exit_val = row['exit_valuation'] / 1_000_000 if row['exit_valuation'] > 0 else 0
        exit_ownership = row['exit_ownership'] * 100 if row['exit_ownership'] > 0 else 0  # Convert to percentage
        cumulative_inv = row['cumulative_investment'] / 1_000_000
        exit_proceeds = row['exit_proceeds'] / 1_000_000 if row['exit_proceeds'] > 0 else 0
        investment_multiple = row['investment_multiple']
        
        # Color coding for outcome
        outcome_color = '#268BA0' if outcome == 'exited' else '#024761'  # blue-munsell for exited, indigo-dye for failed
        
        table_html += f"""
                <tr style="border-bottom: 1px solid #e5e7eb; hover:background-color: #f9fafb;">
                    <td style="padding: 10px 12px; font-weight: 500; color: {outcome_color};">{outcome.title()}</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{company_count:,}</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${initial_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${initial_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{initial_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${exit_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{exit_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${cumulative_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${exit_proceeds:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{investment_multiple:.1f}x</td>
                </tr>
        """
    
    # Add total row
    total_count = outcome_stats['company_count'].sum()
    total_initial_val = (outcome_stats['initial_valuation'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_initial_inv = (outcome_stats['initial_investment'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_exit_val = (outcome_stats['exit_valuation'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_cumulative_inv = (outcome_stats['cumulative_investment'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_exit_proceeds = (outcome_stats['exit_proceeds'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    
    # Calculate total ownership percentages
    total_initial_ownership = (total_initial_inv / total_initial_val) * 100 if total_initial_val > 0 else 0
    total_exit_ownership = (total_exit_proceeds / total_exit_val) * 100 if total_exit_val > 0 else 0
    total_investment_multiple = total_exit_proceeds / total_cumulative_inv if total_cumulative_inv > 0 else 0
    
    table_html += f"""
                <tr style="background-color: #f3f4f6; font-weight: bold; border-top: 2px solid #d1d5db;">
                    <td style="padding: 10px 12px; color: #111827;">Total</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_count:,}</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_initial_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_initial_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_initial_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_exit_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_exit_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_cumulative_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_exit_proceeds:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_investment_multiple:.1f}x</td>
                </tr>
    """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    components.html(table_html, height=250, scrolling=True)

def render_outcome_statistics_widget_no_header(scenario):
    """Render outcome statistics widget without header (for use in expander)"""
    import streamlit.components.v1 as components
    
    # Aggregate all companies from all simulations
    all_companies = []
    for sim_idx, res in enumerate(scenario['results']):
        for company in res.company_results:
            if company.history:
                initial_stage = company.history[0].get('stage', 'Unknown')
                initial_valuation = company.history[0].get('valuation', 0)
                initial_investment = company.history[0].get('round_investment', 0)
                all_companies.append({
                    'simulation': sim_idx + 1,
                    'initial_stage': initial_stage,
                    'outcome': company.outcome,
                    'initial_valuation': initial_valuation,
                    'initial_investment': initial_investment,
                    'cumulative_investment': company.total_invested,
                    'exit_valuation': company.exit_valuation if company.outcome == 'exited' else 0,
                    'exit_proceeds': company.exit_proceeds if company.outcome == 'exited' else 0
                })
    
    df_companies = pd.DataFrame(all_companies)
    
    if df_companies.empty:
        st.warning("No company data available")
        return
    
    # Calculate statistics by outcome
    outcome_stats = df_companies.groupby('outcome').agg({
        'simulation': 'count',  # Count of companies using simulation column
        'initial_valuation': 'mean',
        'initial_investment': 'mean',
        'cumulative_investment': 'mean',
        'exit_valuation': 'mean',
        'exit_proceeds': 'mean'
    }).reset_index()
    
    # Rename the count column
    outcome_stats = outcome_stats.rename(columns={'simulation': 'company_count'})
    
    # Calculate ownership percentages
    outcome_stats['initial_ownership'] = outcome_stats['initial_investment'] / outcome_stats['initial_valuation']
    outcome_stats['initial_ownership'] = outcome_stats['initial_ownership'].fillna(0)  # Handle division by zero
    
    outcome_stats['exit_ownership'] = outcome_stats['exit_proceeds'] / outcome_stats['exit_valuation']
    outcome_stats['exit_ownership'] = outcome_stats['exit_ownership'].fillna(0)  # Handle division by zero
    
    # Calculate investment multiple: Exit Proceeds / Cumulative Investment
    outcome_stats['investment_multiple'] = outcome_stats['exit_proceeds'] / outcome_stats['cumulative_investment']
    outcome_stats['investment_multiple'] = outcome_stats['investment_multiple'].fillna(0)  # Handle division by zero
    
    # Create custom HTML table (no header widget)
    table_html = """
    <div style="overflow-x: auto; margin: 1rem 0;">
        <table style="width: 100%; border-collapse: collapse; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'; font-size: 13px;">
            <thead>
                <tr style="border-bottom: 2px solid #e5e7eb; background-color: #f9fafb;">
                    <th style="text-align: left; padding: 10px 12px; font-weight: 600; color: #374151;">Outcome</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Company Count</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Initial Valuation</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Initial Investment</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Initial Ownership</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Exit Valuation</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Exit Ownership</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Avg Cumulative Investment</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Exit Proceeds</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Investment Multiple</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add data rows
    for _, row in outcome_stats.iterrows():
        outcome = row['outcome']
        company_count = int(row['company_count'])
        initial_val = row['initial_valuation'] / 1_000_000  # Convert to millions
        initial_inv = row['initial_investment'] / 1_000_000
        initial_ownership = row['initial_ownership'] * 100  # Convert to percentage
        exit_val = row['exit_valuation'] / 1_000_000 if row['exit_valuation'] > 0 else 0
        exit_ownership = row['exit_ownership'] * 100 if row['exit_ownership'] > 0 else 0  # Convert to percentage
        cumulative_inv = row['cumulative_investment'] / 1_000_000
        exit_proceeds = row['exit_proceeds'] / 1_000_000 if row['exit_proceeds'] > 0 else 0
        investment_multiple = row['investment_multiple']
        
        # Color coding for outcome
        outcome_color = '#268BA0' if outcome == 'exited' else '#024761'  # blue-munsell for exited, indigo-dye for failed
        
        table_html += f"""
                <tr style="border-bottom: 1px solid #e5e7eb; hover:background-color: #f9fafb;">
                    <td style="padding: 10px 12px; font-weight: 500; color: {outcome_color};">{outcome.title()}</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{company_count:,}</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${initial_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${initial_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{initial_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${exit_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{exit_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${cumulative_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">${exit_proceeds:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #111827;">{investment_multiple:.1f}x</td>
                </tr>
        """
    
    # Add total row
    total_count = outcome_stats['company_count'].sum()
    total_initial_val = (outcome_stats['initial_valuation'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_initial_inv = (outcome_stats['initial_investment'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_exit_val = (outcome_stats['exit_valuation'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_cumulative_inv = (outcome_stats['cumulative_investment'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    total_exit_proceeds = (outcome_stats['exit_proceeds'] * outcome_stats['company_count']).sum() / outcome_stats['company_count'].sum() / 1_000_000
    
    # Calculate total ownership percentages
    total_initial_ownership = (total_initial_inv / total_initial_val) * 100 if total_initial_val > 0 else 0
    total_exit_ownership = (total_exit_proceeds / total_exit_val) * 100 if total_exit_val > 0 else 0
    total_investment_multiple = total_exit_proceeds / total_cumulative_inv if total_cumulative_inv > 0 else 0
    
    table_html += f"""
                <tr style="background-color: #f3f4f6; font-weight: bold; border-top: 2px solid #d1d5db;">
                    <td style="padding: 10px 12px; color: #111827;">Total</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_count:,}</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_initial_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_initial_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_initial_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_exit_val:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_exit_ownership:.1f}%</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_cumulative_inv:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">${total_exit_proceeds:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #111827;">{total_investment_multiple:.1f}x</td>
                </tr>
    """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    components.html(table_html, height=250, scrolling=True)

def render_waterfall_tab(scenario):
    """Render waterfall details tab for the selected scenario"""
    st.subheader("Waterfall Distribution Breakdown")
    
    if scenario['waterfall_log'] is None or scenario['waterfall_log'].empty:
        st.warning("No waterfall data available")
        return
    
    # Show waterfall for the selected scenario only
    from ui_components import render_comprehensive_waterfall
    
    # Create a single-scenario dictionary for the selected scenario
    selected_scenario_dict = {scenario['name']: scenario}
    
    # Render comprehensive waterfall for this scenario only
    render_comprehensive_waterfall(selected_scenario_dict)
    
    st.markdown("---")
    
    # Detailed waterfall table for current scenario
    with st.expander("View Detailed Waterfall Table (Current Scenario)", expanded=False):
        # Select key columns for display
        display_columns = [
            'Year',
            'LP Contributions in year',
            'GP Contributions in year',
            'Distributable Proceeds this year',
            'ROC to LP',
            'ROC to GP',
            'Pref to LP',
            'LP Carry Cumulative',
            'GP Carry Cumulative',
            'Total to LP',
            'Total to GP'
        ]
        
        available_columns = [col for col in display_columns if col in scenario['waterfall_log'].columns]
        
        st.dataframe(
            scenario['waterfall_log'][available_columns].style.format(
                {col: '${:,.0f}' for col in available_columns if col != 'Year'}
            ),
            use_container_width=True
        )


def render_histogram(data, xlabel, ylabel, median_value):
    """Helper function to render a histogram with median line"""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=data,
        nbinsx=50,
        marker_color='#1f77b4',
        opacity=0.7
    ))
    
    fig.add_vline(
        x=median_value,
        line_dash="dash",
        line_color='#2ca02c',
        annotation_text=f"Median: {median_value:.2f}",
        annotation_position="top"
    )
    
    fig.update_layout(
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        showlegend=False,
        height=400,
        hovermode='x unified'
    )
    
    return fig

def generate_excel_download(scenario):
    """Generate Excel file for download"""
    try:
        # Check if scenario has pre-generated Excel buffer (for default scenario)
        if 'excel_buffer' in scenario and scenario['excel_buffer'] is not None:
            return scenario['excel_buffer']
        
        # For other scenarios, generate Excel on-the-fly
        from engine import convert_multiple_simulations_to_excel_with_flows
        
        # Create in-memory Excel file
        output = io.BytesIO()
        
        # Generate Excel
        convert_multiple_simulations_to_excel_with_flows(
            scenario['results'],
            scenario['gross_flows'],
            waterfall_log=scenario['waterfall_log'],
            net_lp_flows_log=scenario['net_lp_flows'],
            filename="temp.xlsx"  # This will be overridden
        )
        
        # Read the generated file
        with open("temp.xlsx", 'rb') as f:
            output.write(f.read())
        
        output.seek(0)
        return output.getvalue()
    
    except Exception as e:
        st.error(f"Error generating Excel: {str(e)}")
        return None

def generate_scenario_package(scenario):
    """Generate complete scenario package as ZIP"""
    import zipfile
    import yaml
    import pickle
    import json
    
    try:
        output = io.BytesIO()
        
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add config YAML
            config_str = yaml.dump(scenario['config'])
            zipf.writestr('config.yaml', config_str)
            
            # Add results pickle
            if scenario['results'] is not None:
                results_dict = {
                    'all_results': scenario['results'],
                    'all_gross_flows': scenario['gross_flows'],
                    'waterfall_log': scenario['waterfall_log'],
                    'net_lp_flows_log': scenario['net_lp_flows']
                }
                
                results_bytes = pickle.dumps(results_dict)
                zipf.writestr('results.pkl', results_bytes)
            
            # Add Excel file if available
            if 'excel_buffer' in scenario and scenario['excel_buffer'] is not None:
                zipf.writestr('results.xlsx', scenario['excel_buffer'])
            elif scenario['results'] is not None:
                # Generate Excel file if not pre-generated
                excel_buffer = generate_excel_download(scenario)
                if excel_buffer:
                    zipf.writestr('results.xlsx', excel_buffer)
            
            # Add metadata
            metadata = {
                'name': scenario['name'],
                'timestamp': scenario['timestamp'].isoformat(),
                'has_results': scenario['results'] is not None,
                'has_excel': ('excel_buffer' in scenario and scenario['excel_buffer'] is not None) or scenario['results'] is not None
            }
            
            metadata_str = json.dumps(metadata, indent=2)
            zipf.writestr('metadata.json', metadata_str)
        
        output.seek(0)
        return output.getvalue()
    
    except Exception as e:
        st.error(f"Error generating package: {str(e)}")
        return None

def load_and_set_default():
    """Load default scenario into session state"""
    from streamlit_app import load_default_scenario
    
    default_scenario = load_default_scenario()
    if default_scenario:
        st.session_state.scenarios[default_scenario['name']] = default_scenario
        st.session_state.current_scenario_name = default_scenario['name']

# Continue in next message with Compare Tab...