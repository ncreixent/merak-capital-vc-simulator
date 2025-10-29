# compare_tab.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_compare_tab():
    """Render the Compare Scenarios tab"""
    st.markdown("<h1 class='main-header'>⚖️ Compare Scenarios</h1>", unsafe_allow_html=True)
    
    # Get scenarios with results
    scenarios_with_results = {
        name: scenario for name, scenario in st.session_state.scenarios.items()
        if scenario['results'] is not None
    }
    
    if len(scenarios_with_results) < 2:
        st.warning("⚠️ You need at least 2 scenarios with results to compare.")
        st.info("💡 Run simulations in the 'Run & Analyze' tab first, then return here to compare.")
        
        # Show available scenarios
        if st.session_state.scenarios:
            st.markdown("### Available Scenarios")
            render_scenario_list()
        
        return
    
    # Scenario selection
    st.subheader("Select Scenarios to Compare")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scenario1_name = st.selectbox(
            "Scenario 1",
            options=list(scenarios_with_results.keys()),
            key="compare_scenario1"
        )
    
    with col2:
        # Filter out already selected scenario
        scenario2_options = [s for s in scenarios_with_results.keys() if s != scenario1_name]
        scenario2_name = st.selectbox(
            "Scenario 2",
            options=scenario2_options,
            key="compare_scenario2"
        )
    
    with col3:
        # Optional third scenario
        scenario3_options = [s for s in scenarios_with_results.keys() 
                           if s not in [scenario1_name, scenario2_name]]
        
        if scenario3_options:
            include_third = st.checkbox("Add 3rd Scenario", value=False)
            
            if include_third:
                scenario3_name = st.selectbox(
                    "Scenario 3",
                    options=scenario3_options,
                    key="compare_scenario3"
                )
            else:
                scenario3_name = None
        else:
            scenario3_name = None
    
    # Get selected scenarios
    scenarios_to_compare = [
        scenarios_with_results[scenario1_name],
        scenarios_with_results[scenario2_name]
    ]
    
    scenario_names = [scenario1_name, scenario2_name]
    
    if scenario3_name:
        scenarios_to_compare.append(scenarios_with_results[scenario3_name])
        scenario_names.append(scenario3_name)
    
    st.markdown("---")
    
    # Comparison tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Configuration Comparison",
        "📈 Performance Metrics",
        "📉 Distribution Analysis"
    ])
    
    with tab1:
        render_config_comparison(scenarios_to_compare, scenario_names)
    
    with tab2:
        render_metrics_comparison(scenarios_to_compare, scenario_names)
    
    with tab3:
        render_distribution_comparison(scenarios_to_compare, scenario_names)

def render_scenario_list():
    """Render list of all scenarios with summary info"""
    from scenario_manager import ScenarioManager
    
    scenario_data = []
    
    for name, scenario in st.session_state.scenarios.items():
        row = {
            'Scenario Name': name,
            'Created': scenario['timestamp'].strftime('%Y-%m-%d %H:%M'),
            'Has Results': '✅' if scenario['results'] is not None else '❌',
            'Committed Capital': scenario['config'].get('committed_capital', 'N/A'),
            'Num Investments': scenario['config'].get('num_investments', 'N/A'),
        }
        
        if scenario['results'] is not None:
            metrics = ScenarioManager.calculate_metrics(scenario)  # Uses cache
            if metrics:
                row['Median Net IRR'] = f"{metrics['median_net_irr']:.2%}"
                row['Median Net Multiple'] = f"{metrics['median_net_multiple']:.2f}x"
        else:
            row['Median Net IRR'] = 'N/A'
            row['Median Net Multiple'] = 'N/A'
        
        scenario_data.append(row)
    
    df_scenarios = pd.DataFrame(scenario_data)
    
    st.dataframe(
        df_scenarios.style.format({
            'Committed Capital': lambda x: f'${x:,.0f}' if isinstance(x, (int, float)) else x,
            'Num Investments': lambda x: f'{x:.0f}' if isinstance(x, (int, float)) else x
        }),
        use_container_width=True,
        hide_index=True
    )
    

def render_config_comparison(scenarios, names):
    """Render configuration comparison"""
    st.subheader("⚙️ Configuration Parameters")
    
    # Extract key configuration parameters
    config_data = []
    
    for scenario, name in zip(scenarios, names):
        config = scenario['config']
        
        row = {
            'Parameter': name,
            'Committed Capital': config.get('committed_capital', 0),
            'Number of Investments': config.get('num_investments', 0),
            'Max Deals/Year': config.get('max_deals_per_year', 0),
            'Investment Period (months)': config.get('investment_period_months', 0),
            'Follow-on Strategy': config.get('follow_on_strategy', {}).get('type', 'N/A'),
            'Mgmt Fee (Commitment)': config.get('mgmt_fee_commitment_period_rate', 0),
            'Carried Interest': config.get('waterfall', {}).get('carried_interest_pct', 0),
            'Preferred Return': config.get('waterfall', {}).get('preferred_return_pct', 0),
        }
        
        config_data.append(row)
    
    df_config = pd.DataFrame(config_data).T
    df_config.columns = names
    df_config.index.name = 'Parameter'
    
    # Format the dataframe
    formatted_df = df_config.copy()
    
    # Apply formatting
    for col in df_config.columns:
        formatted_df[col] = df_config[col].apply(lambda x: format_config_value(x))
    
    st.dataframe(formatted_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🎯 Initial Ownership Targets")
    
    # Compare ownership targets
    ownership_data = []
    
    for scenario, name in zip(scenarios, names):
        ownership = scenario['config'].get('initial_ownership_targets', {})
        row = {'Scenario': name}
        row.update({stage: f"{pct:.0%}" for stage, pct in ownership.items()})
        ownership_data.append(row)
    
    df_ownership = pd.DataFrame(ownership_data)
    
    st.dataframe(df_ownership, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("📅 Stage Allocation Over Time")
    
    # Create comparison chart for stage allocations
    render_stage_allocation_comparison(scenarios, names)

def render_metrics_comparison(scenarios, names):
    """Render performance metrics comparison"""
    from scenario_manager import ScenarioManager
    
    st.subheader("📊 Performance Metrics Comparison")
    
    # Add refresh button for metrics
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("")  # Spacer
    with col2:
        if st.button("🔄 Refresh All Metrics", help="Recalculate metrics for all scenarios"):
            for scenario in scenarios:
                scenario['cached_metrics'] = None
            st.rerun()
    
    # Calculate metrics for all scenarios (using cache)
    metrics_list = [ScenarioManager.calculate_metrics(s) for s in scenarios]
    
    # Show cache status for all scenarios
    cache_statuses = []
    for scenario in scenarios:
        status = "✅ Cached" if scenario.get('cached_metrics') is not None else "🔄 Calculated"
        cache_statuses.append(status)
    
    st.caption(f"Metrics status: {' | '.join([f'{name}: {status}' for name, status in zip(names, cache_statuses)])}")
    
    # Create comparison table
    metrics_data = []
    
    metric_definitions = [
        ('median_net_irr', 'Median Net IRR', '{:.2%}'),
        ('mean_net_irr', 'Mean Net IRR', '{:.2%}'),
        ('median_net_multiple', 'Median Net Multiple', '{:.2f}x'),
        ('mean_net_multiple', 'Mean Net Multiple', '{:.2f}x'),
        ('median_gross_irr', 'Median Gross IRR', '{:.2%}'),
        ('mean_gross_irr', 'Mean Gross IRR', '{:.2%}'),
        ('median_gross_multiple', 'Median Gross Multiple', '{:.2f}x'),
        ('mean_gross_multiple', 'Mean Gross Multiple', '{:.2f}x'),
        ('var_5', 'VaR (5%)', '{:.2%}'),
        ('var_10', 'VaR (10%)', '{:.2%}'),
        ('avg_portfolio_size', 'Avg Portfolio Size', '{:.1f}'),
        ('avg_initial_investment', 'Avg Initial Investment', '${:,.0f}'),
        ('avg_cumulative_investment', 'Avg Cumulative Investment', '${:,.0f}'),
    ]
    
    for key, label, fmt in metric_definitions:
        row = {'Metric': label}
        for i, (metrics, name) in enumerate(zip(metrics_list, names)):
            value = metrics.get(key, 0)
            if value is not None:
                row[name] = value
            else:
                row[name] = 0
        
        metrics_data.append(row)
    
    df_metrics = pd.DataFrame(metrics_data)
    
    # Apply formatting
    def format_metric_row(row):
        metric = row['Metric']
        
        # Find the format string
        fmt = next((f for k, l, f in metric_definitions if l == metric), None)
        
        if fmt:
            for col in names:
                if col in row.index:
                    value = row[col]
                    if pd.notna(value):
                        if '%' in fmt:
                            row[col] = fmt.format(value)
                        elif 'x' in fmt:
                            row[col] = fmt.format(value)
                        elif '$' in fmt:
                            row[col] = fmt.format(value)
                        else:
                            row[col] = fmt.format(value)
        
        return row
    
    # Create styled dataframe
    st.dataframe(
        df_metrics,
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Visualize key metrics
    st.subheader("📈 Key Metrics Visualization")
    
    # Create comparison bar chart
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Net IRR Comparison', 'Net Multiple Comparison',
                       'Gross IRR Comparison', 'VaR Comparison')
    )
    
    # Net IRR
    fig.add_trace(
        go.Bar(
            x=names,
            y=[m['median_net_irr'] * 100 for m in metrics_list],
            name='Median Net IRR',
            marker_color='#1f77b4'
        ),
        row=1, col=1
    )
    
    # Net Multiple
    fig.add_trace(
        go.Bar(
            x=names,
            y=[m['median_net_multiple'] for m in metrics_list],
            name='Median Net Multiple',
            marker_color='#ff7f0e'
        ),
        row=1, col=2
    )
    
    # Gross IRR
    fig.add_trace(
        go.Bar(
            x=names,
            y=[m['median_gross_irr'] * 100 for m in metrics_list],
            name='Median Gross IRR',
            marker_color='#2ca02c'
        ),
        row=2, col=1
    )
    
    # VaR
    fig.add_trace(
        go.Bar(
            x=names,
            y=[m['var_5'] * 100 for m in metrics_list],
            name='VaR (5%)',
            marker_color='#d62728'
        ),
        row=2, col=2
    )
    
    fig.update_yaxes(title_text="IRR (%)", row=1, col=1)
    fig.update_yaxes(title_text="Multiple", row=1, col=2)
    fig.update_yaxes(title_text="IRR (%)", row=2, col=1)
    fig.update_yaxes(title_text="VaR (%)", row=2, col=2)
    
    fig.update_layout(height=600, showlegend=False)
    
    st.plotly_chart(fig, use_container_width=True)

def render_distribution_comparison(scenarios, names):
    """Render distribution comparison"""
    st.subheader("📉 Return Distribution Comparison")
    
    # Overlay IRR histograms
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, (scenario, name) in enumerate(zip(scenarios, names)):
        df_results = pd.DataFrame([vars(res) for res in scenario['results']])
        irr_data = df_results[df_results['net_irr'] > -0.99]['net_irr'] * 100
        
        fig.add_trace(go.Histogram(
            x=irr_data,
            name=name,
            opacity=0.6,
            marker_color=colors[i],
            nbinsx=50
        ))
    
    fig.update_layout(
        title="Net IRR Distribution Comparison",
        xaxis_title="Net IRR (%)",
        yaxis_title="Frequency",
        barmode='overlay',
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Box plots for comparison
    st.subheader("📦 Distribution Box Plots")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Net IRR box plot
        fig_irr = go.Figure()
        
        for i, (scenario, name) in enumerate(zip(scenarios, names)):
            df_results = pd.DataFrame([vars(res) for res in scenario['results']])
            irr_data = df_results[df_results['net_irr'] > -0.99]['net_irr'] * 100
            
            fig_irr.add_trace(go.Box(
                y=irr_data,
                name=name,
                marker_color=colors[i]
            ))
        
        fig_irr.update_layout(
            title="Net IRR Distribution",
            yaxis_title="Net IRR (%)",
            height=400
        )
        
        st.plotly_chart(fig_irr, use_container_width=True)
    
    with col2:
        # Net Multiple box plot
        fig_multiple = go.Figure()
        
        for i, (scenario, name) in enumerate(zip(scenarios, names)):
            df_results = pd.DataFrame([vars(res) for res in scenario['results']])
            
            fig_multiple.add_trace(go.Box(
                y=df_results['net_multiple'],
                name=name,
                marker_color=colors[i]
            ))
        
        fig_multiple.update_layout(
            title="Net Multiple Distribution",
            yaxis_title="Net Multiple",
            height=400
        )
        
        st.plotly_chart(fig_multiple, use_container_width=True)
    
    st.markdown("---")
    
    # Percentile comparison table
    st.subheader("📊 Percentile Comparison")
    
    percentile_data = []
    
    for scenario, name in zip(scenarios, names):
        df_results = pd.DataFrame([vars(res) for res in scenario['results']])
        
        percentiles = df_results['net_irr'].quantile([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
        
        row = {
            'Scenario': name,
            'P5': f"{percentiles[0.05]:.2%}",
            'P10': f"{percentiles[0.10]:.2%}",
            'P25': f"{percentiles[0.25]:.2%}",
            'P50': f"{percentiles[0.50]:.2%}",
            'P75': f"{percentiles[0.75]:.2%}",
            'P90': f"{percentiles[0.90]:.2%}",
            'P95': f"{percentiles[0.95]:.2%}"
        }
        
        percentile_data.append(row)
    
    df_percentiles = pd.DataFrame(percentile_data)
    
    st.dataframe(df_percentiles, use_container_width=True, hide_index=True)

def render_stage_allocation_comparison(scenarios, names):
    """Render stage allocation comparison chart"""
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    fig = make_subplots(
        rows=1, cols=len(scenarios),
        subplot_titles=names,
        specs=[[{'type': 'bar'}] * len(scenarios)]
    )
    
    for i, (scenario, name) in enumerate(zip(scenarios, names)):
        allocations = scenario['config'].get('dynamic_stage_allocation', [])
        
        if allocations:
            years = [a['year'] for a in allocations]
            stages = list(allocations[0]['allocation'].keys())
            
            for stage in stages:
                values = [a['allocation'].get(stage, 0) * 100 for a in allocations]
                
                fig.add_trace(
                    go.Bar(
                        x=years,
                        y=values,
                        name=stage if i == 0 else None,  # Only show legend for first subplot
                        showlegend=(i == 0),
                        marker_color=colors[stages.index(stage) % len(colors)]
                    ),
                    row=1, col=i+1
                )
    
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Allocation (%)")
    fig.update_layout(
        height=400,
        barmode='stack',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def format_config_value(value):
    """Format configuration values for display"""
    if isinstance(value, float):
        if value < 1:
            return f"{value:.2%}"
        else:
            return f"${value:,.0f}" if value > 1000 else f"{value:.2f}"
    elif isinstance(value, int):
        if value > 1000000:
            return f"${value:,.0f}"
        else:
            return f"{value}"
    else:
        return str(value)