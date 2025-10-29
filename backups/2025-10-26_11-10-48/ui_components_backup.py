# ui_components.py

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_metric_cards(metrics):
    """Render key metrics in card format"""
    
    # Portfolio Summary Metrics (Top Row)
    st.markdown("#### 📊 Portfolio Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Average Portfolio Size",
            value=f"{metrics['avg_portfolio_size']:.0f}",
            delta=None,
            help="Average number of companies invested in across all simulations"
        )
    
    with col2:
        if metrics['avg_initial_investment'] is not None:
            st.metric(
                label="Average Initial Investment",
                value=f"${metrics['avg_initial_investment']:,.0f}",
                delta=None,
                help="Average size of initial investment per company"
            )
        else:
            st.metric(
                label="Average Initial Investment",
                value="N/A",
                delta=None
            )
    
    with col3:
        if metrics['avg_cumulative_investment'] is not None:
            st.metric(
                label="Average Cumulative Investment",
                value=f"${metrics['avg_cumulative_investment']:,.0f}",
                delta=None,
                help="Average total investment per company including follow-ons"
            )
        else:
            st.metric(
                label="Average Cumulative Investment",
                value="N/A",
                delta=None
            )
    
    st.markdown("---")
    
    # Performance Metrics (Bottom Row)
    st.markdown("#### 📈 Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Median Net IRR",
            value=f"{metrics['median_net_irr']:.2%}",
            delta=None
        )
        st.metric(
            label="Mean Net IRR",
            value=f"{metrics['mean_net_irr']:.2%}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Median Net Multiple",
            value=f"{metrics['median_net_multiple']:.2f}x",
            delta=None
        )
        st.metric(
            label="Mean Net Multiple",
            value=f"{metrics['mean_net_multiple']:.2f}x",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Median Gross IRR",
            value=f"{metrics['median_gross_irr']:.2%}",
            delta=None
        )
        st.metric(
            label="Mean Gross IRR",
            value=f"{metrics['mean_gross_irr']:.2%}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="VaR (5%)",
            value=f"{metrics['var_5']:.2%}",
            delta=None,
            help="Value at Risk: Worst-case scenario in 95% of simulations"
        )
        st.metric(
            label="VaR (10%)",
            value=f"{metrics['var_10']:.2%}",
            delta=None
        )

def render_irr_histogram(results, title="Net IRR Distribution"):
    """Render interactive IRR histogram with percentile bands"""
    df_results = pd.DataFrame([vars(res) for res in results])
    
    # Filter extreme values for better visualization
    viz_data = df_results[df_results['net_irr'] > -0.99]['net_irr'] * 100
    
    # Calculate percentiles
    p10 = viz_data.quantile(0.10)
    p25 = viz_data.quantile(0.25)
    p50 = viz_data.quantile(0.50)
    p75 = viz_data.quantile(0.75)
    p90 = viz_data.quantile(0.90)
    
    # Create histogram
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=viz_data,
        nbinsx=50,
        name='Net IRR',
        marker_color='#1f77b4',
        opacity=0.7
    ))
    
    # Add percentile lines
    for percentile, value, color in [
        ('P10', p10, '#d62728'),
        ('P25', p25, '#ff7f0e'),
        ('P50 (Median)', p50, '#2ca02c'),
        ('P75', p75, '#ff7f0e'),
        ('P90', p90, '#d62728')
    ]:
        fig.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{percentile}: {value:.1f}%",
            annotation_position="top"
        )
    
    fig.update_layout(
        title=title,
        xaxis_title="Net IRR (%)",
        yaxis_title="Frequency",
        showlegend=False,
        height=500,
        hovermode='x unified'
    )
    
    return fig

def render_time_to_exit_chart(results):
    """Render time-to-exit distribution by outcome"""
    all_companies = []
    
    for res in results:
        for company in res.company_results:
            if company.time_to_exit_months is not None:
                all_companies.append({
                    'time_to_exit_years': company.time_to_exit_months / 12,
                    'outcome': company.outcome,
                    'multiple': company.multiple
                })
    
    df_companies = pd.DataFrame(all_companies)
    
    if df_companies.empty:
        st.warning("No exit data available")
        return None
    
    # Create box plot by outcome
    fig = px.box(
        df_companies,
        x='outcome',
        y='time_to_exit_years',
        color='outcome',
        title="Time to Exit by Outcome",
        labels={'time_to_exit_years': 'Years to Exit', 'outcome': 'Outcome'}
    )
    
    fig.update_layout(height=400, showlegend=False)
    
    return fig

def render_success_rate_by_stage(results):
    """Render success rate analysis by initial stage"""
    all_companies = []
    
    for res in results:
        for company in res.company_results:
            if company.history:
                initial_stage = company.history[0].get('stage', 'Unknown')
                all_companies.append({
                    'initial_stage': initial_stage,
                    'outcome': company.outcome,
                    'exited': 1 if company.outcome == 'exited' else 0
                })
    
    df_companies = pd.DataFrame(all_companies)
    
    if df_companies.empty:
        st.warning("No company data available")
        return None
    
    # Calculate success rates
    success_rates = df_companies.groupby('initial_stage').agg({
        'exited': ['sum', 'count']
    }).reset_index()
    success_rates.columns = ['initial_stage', 'exits', 'total']
    success_rates['success_rate'] = success_rates['exits'] / success_rates['total']
    
    # Create bar chart
    fig = px.bar(
        success_rates,
        x='initial_stage',
        y='success_rate',
        title="Success Rate by Initial Investment Stage",
        labels={'success_rate': 'Exit Rate', 'initial_stage': 'Initial Stage'},
        text='success_rate'
    )
    
    fig.update_traces(texttemplate='%{text:.1%}', textposition='outside')
    fig.update_layout(height=400, yaxis_tickformat='.0%')
    
    return fig

def render_waterfall_breakdown(waterfall_log):
    """Render waterfall distribution breakdown"""
    if waterfall_log is None or waterfall_log.empty:
        st.warning("No waterfall data available")
        return None
    
    # Ensure there is a year-like column to group by
    df = waterfall_log.copy()
    year_col = None
    # 1) Exact match
    if 'Year' in df.columns:
        year_col = 'Year'
    else:
        # 2) Case-insensitive match
        for col in df.columns:
            if isinstance(col, str) and col.lower() == 'year':
                year_col = col
                break
        # 3) Index named Year
        if year_col is None and isinstance(df.index.name, str) and df.index.name.lower() == 'year':
            df = df.reset_index()
            year_col = 'Year'
        # 4) Derive from first datetime-like column
        if year_col is None:
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df['Year'] = df[col].dt.year
                    year_col = 'Year'
                    break
        # 5) As a last resort, if there is a numeric period-like column
        if year_col is None:
            for col in df.columns:
                if pd.api.types.is_integer_dtype(df[col]) and df[col].nunique() <= len(df):
                    year_col = col
                    break
    
    if year_col is None:
        st.warning("Waterfall data does not contain a 'Year' column or any year-like field")
        return None
    
    # Build aggregation only with available columns
    desired_aggs = {
        'Total to LP': 'sum',
        'Total to GP': 'sum',
        'ROC to LP': 'sum',
        'ROC to GP': 'sum',
        'Pref to LP': 'sum',
        'LP Carry Cumulative': 'last',
        'GP Carry Cumulative': 'last'
    }
    available_aggs = {col: func for col, func in desired_aggs.items() if col in df.columns}
    if not available_aggs:
        st.warning("Waterfall data is missing expected distribution columns")
        return None
    
    waterfall_summary = df.groupby(year_col).agg(available_aggs).reset_index().rename(columns={year_col: 'Year'})
    
    # Create stacked area chart
    fig = go.Figure()
    
    if 'Total to LP' in waterfall_summary.columns:
        fig.add_trace(go.Scatter(
            x=waterfall_summary['Year'],
            y=waterfall_summary['Total to LP'],
            mode='lines',
            name='LP Distributions',
            fill='tozeroy',
            line=dict(color='#2ca02c')
        ))
    
    if 'Total to GP' in waterfall_summary.columns:
        fig.add_trace(go.Scatter(
            x=waterfall_summary['Year'],
            y=waterfall_summary['Total to GP'],
            mode='lines',
            name='GP Distributions',
            fill='tozeroy',
            line=dict(color='#ff7f0e')
        ))
    
    fig.update_layout(
        title="Annual Distributions: LP vs GP",
        xaxis_title="Year",
        yaxis_title="Distribution Amount ($)",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def calculate_average_waterfall(scenarios):
    """Calculate average waterfall across all scenarios"""
    if not scenarios:
        return None
    
    # Get scenarios with waterfall data
    scenarios_with_waterfall = {name: s for name, s in scenarios.items() if s.get('waterfall_log') is not None and not s['waterfall_log'].empty}
    
    if not scenarios_with_waterfall:
        return None
    
    # Combine all waterfall data from all scenarios with unique simulation numbers
    all_waterfall_data = []
    simulation_offset = 0
    
    for scenario_name, scenario in scenarios_with_waterfall.items():
        waterfall_log = scenario['waterfall_log'].copy()
        
        # Create unique simulation numbers by adding offset
        # This prevents simulation number conflicts between scenarios
        max_sim_num = waterfall_log['simulation_number'].max()
        waterfall_log['simulation_number'] = waterfall_log['simulation_number'] + simulation_offset
        
        # Add scenario identifier for debugging
        waterfall_log['scenario_name'] = scenario_name
        
        all_waterfall_data.append(waterfall_log)
        simulation_offset += max_sim_num
    
    # Concatenate all waterfall data
    combined_waterfall = pd.concat(all_waterfall_data, ignore_index=True)
    
    # Group by simulation_number and sum across years for each simulation
    simulation_totals = combined_waterfall.groupby('simulation_number').agg({
        'GP Contributions in year': 'sum',
        'LP Contributions in year': 'sum',
        'ROC to LP': 'sum',
        'ROC to GP': 'sum',
        'Pref to LP': 'sum',
        'Catch-up to GP': 'sum',
        'Catch-up LP cut': 'sum',
        'Final Split to LP': 'sum',
        'Final Split to GP': 'sum',
        'Total to LP': 'sum',
        'Total to GP': 'sum'
    }).reset_index()
    
    # Calculate averages across all simulations
    avg_totals = simulation_totals.mean()
    
    # For year-by-year data, group by year position and calculate proper averages
    # Add year column (1-10) based on position within each simulation
    combined_waterfall['Year'] = combined_waterfall.groupby('simulation_number').cumcount() + 1
    
    # Get total number of simulations across all scenarios
    # This now correctly counts unique simulations across all scenarios
    total_simulations = combined_waterfall['simulation_number'].nunique()
    
    # Calculate yearly averages as sum of all cash flows divided by total simulations
    # This ensures simulations without data for certain years are treated as 0
    yearly_averages = combined_waterfall.groupby('Year').agg({
        'LP Contributions in year': 'sum',
        'ROC to LP': 'sum',
        'Pref to LP': 'sum',
        'Catch-up LP cut': 'sum',
        'Final Split to LP': 'sum'
    }).reset_index()
    
    # Divide by total number of simulations to get proper average
    for col in ['LP Contributions in year', 'ROC to LP', 'Pref to LP', 'Catch-up LP cut', 'Final Split to LP']:
        yearly_averages[col] = yearly_averages[col] / total_simulations
    
    return {
        'simulation_totals': simulation_totals,
        'avg_totals': avg_totals,
        'yearly_averages': yearly_averages,
        'combined_waterfall': combined_waterfall
    }

def render_comprehensive_waterfall(scenarios):
    """Render comprehensive waterfall analysis similar to the JSX design"""
    if not scenarios:
        st.warning("No scenarios available for waterfall analysis")
        return
    
    # Calculate average waterfall
    waterfall_data = calculate_average_waterfall(scenarios)
    if waterfall_data is None:
        st.warning("No waterfall data available across scenarios")
        return
    
    # Get fund parameters from first scenario
    first_scenario = list(scenarios.values())[0]
    config = first_scenario.get('config', {})
    
    fund_size = config.get('committed_capital', 0) / 1_000_000  # Convert to millions
    
    # Extract average totals (already in dollars, convert to millions)
    avg_totals = waterfall_data['avg_totals']
    
    # Calculate key metrics
    lp_contributions = abs(avg_totals['LP Contributions in year']) / 1_000_000
    total_lp_distributions = avg_totals['Total to LP'] / 1_000_000
    total_gp_distributions = avg_totals['Total to GP'] / 1_000_000
    total_fund_distributions = total_lp_distributions + total_gp_distributions
    
    # Top-level summary cards with JSX-style widget design
    st.markdown("### 📊 Fund Waterfall Summary")
    
    # Calculate GP Carry (GP Catch-Up + Final GP Split)
    gp_carry = (avg_totals['Catch-up to GP'] + avg_totals['Final Split to GP']) / 1_000_000
    
    # Create custom HTML for summary cards
    summary_cards_html = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';">
        <div style="background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 1.5rem; border-left: 4px solid #6b7280;">
            <div>
                <p style="font-size: 0.875rem; color: #6b7280; margin: 0 0 0.25rem 0;">Fund Size</p>
                <p style="font-size: 1.5rem; font-weight: bold; color: #111827; margin: 0;">${fund_size:.0f}M</p>
            </div>
        </div>
        
        <div style="background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 1.5rem; border-left: 4px solid #10b981;">
            <div>
                <p style="font-size: 0.875rem; color: #6b7280; margin: 0 0 0.25rem 0;">Total Distributions</p>
                <p style="font-size: 1.5rem; font-weight: bold; color: #10b981; margin: 0;">${total_fund_distributions:.1f}M</p>
            </div>
        </div>
        
        <div style="background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 1.5rem; border-left: 4px solid #8b5cf6;">
            <div>
                <p style="font-size: 0.875rem; color: #6b7280; margin: 0 0 0.25rem 0;">MOIC</p>
                <p style="font-size: 1.5rem; font-weight: bold; color: #8b5cf6; margin: 0;">{(total_fund_distributions / fund_size):.2f}x</p>
            </div>
        </div>
        
        <div style="background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 1.5rem; border-left: 4px solid #3b82f6;">
            <div>
                <p style="font-size: 0.875rem; color: #6b7280; margin: 0 0 0.25rem 0;">LP Contributions</p>
                <p style="font-size: 1.5rem; font-weight: bold; color: #3b82f6; margin: 0;">${lp_contributions:.1f}M</p>
            </div>
        </div>
        
        <div style="background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 1.5rem; border-left: 4px solid #10b981;">
            <div>
                <p style="font-size: 0.875rem; color: #6b7280; margin: 0 0 0.25rem 0;">LP Distributions</p>
                <p style="font-size: 1.5rem; font-weight: bold; color: #10b981; margin: 0;">${total_lp_distributions:.1f}M</p>
            </div>
        </div>
        
        <div style="background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 1.5rem; border-left: 4px solid #06b6d4;">
            <div>
                <p style="font-size: 0.875rem; color: #6b7280; margin: 0 0 0.25rem 0;">LP MOIC</p>
                <p style="font-size: 1.5rem; font-weight: bold; color: #06b6d4; margin: 0;">{(total_lp_distributions / lp_contributions):.2f}x</p>
            </div>
        </div>
        
        <div style="background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding: 1.5rem; border-left: 4px solid #f97316;">
            <div>
                <p style="font-size: 0.875rem; color: #6b7280; margin: 0 0 0.25rem 0;">GP Carry</p>
                <p style="font-size: 1.5rem; font-weight: bold; color: #f97316; margin: 0;">${gp_carry:.1f}M</p>
            </div>
        </div>
    </div>
    """
    
    components.html(summary_cards_html, height=120)
    
    st.markdown("---")
    
    # Fund-level distribution waterfall widget
    waterfall_widget_html = f"""
    <div style="background: white; border-radius: 12px; box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1); padding: 1.5rem; margin: 1rem 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';">
        <div style="margin-bottom: 1rem;">
            <h2 style="font-size: 1.5rem; font-weight: bold; color: #111827; margin: 0 0 0.5rem 0;">🏦 Fund-Level Distribution Waterfall</h2>
            <p style="color: #6b7280; margin: 0;">Total distributions split between Limited Partners (LP) and General Partner (GP)</p>
        </div>
    </div>
    """
    
    components.html(waterfall_widget_html, height=80)
    
    # Prepare waterfall data with 4 categories
    waterfall_categories = [
        {
            'stage': 'Return of Capital',
            'lp': avg_totals['ROC to LP'] / 1_000_000,
            'gp': avg_totals['ROC to GP'] / 1_000_000,
            'description': 'LPs and GP receive invested capital back',
            'color': '#3b82f6'
        },
        {
            'stage': 'Preferred Return',
            'lp': avg_totals['Pref to LP'] / 1_000_000,
            'gp': 0,
            'description': 'LPs receive preferred return',
            'color': '#10b981'
        },
        {
            'stage': 'Catch Up',
            'lp': avg_totals['Catch-up LP cut'] / 1_000_000,
            'gp': avg_totals['Catch-up to GP'] / 1_000_000,
            'description': 'GP catch-up and LP cut',
            'color': '#f59e0b'
        },
        {
            'stage': 'Carried Interest',
            'lp': avg_totals['Final Split to LP'] / 1_000_000,
            'gp': avg_totals['Final Split to GP'] / 1_000_000,
            'description': 'Final profit split between LP and GP',
            'color': '#8b5cf6'
        }
    ]
    
    # Create waterfall chart
    fig_waterfall = go.Figure()
    
    # Add LP bars
    fig_waterfall.add_trace(go.Bar(
        name='LP Distribution',
        x=[item['stage'] for item in waterfall_categories],
        y=[item['lp'] for item in waterfall_categories],
        marker_color='#3b82f6',
        text=[f"${item['lp']:.1f}M" if item['lp'] > 0 else "" for item in waterfall_categories],
        textposition='inside'
    ))
    
    # Add GP bars
    fig_waterfall.add_trace(go.Bar(
        name='GP Distribution',
        x=[item['stage'] for item in waterfall_categories],
        y=[item['gp'] for item in waterfall_categories],
        marker_color='#f97316',
        text=[f"${item['gp']:.1f}M" if item['gp'] > 0 else "" for item in waterfall_categories],
        textposition='inside'
    ))
    
    fig_waterfall.update_layout(
        title="",
        xaxis_title="Distribution Stage",
        yaxis_title="Amount ($M)",
        barmode='stack',
        height=400,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif", size=12)
    )
    
    st.plotly_chart(fig_waterfall, use_container_width=True)
    
    # Distribution Summary Table Widget
    table_widget_html = f"""
    <div style="background: white; border-radius: 12px; box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1); padding: 1.5rem; margin: 1rem 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';">
        <div style="margin-bottom: 1rem;">
            <h2 style="font-size: 1.5rem; font-weight: bold; color: #111827; margin: 0 0 0.5rem 0;">📋 Distribution Summary Table</h2>
            <p style="color: #6b7280; margin: 0;">Detailed breakdown of fund distributions by stage</p>
        </div>
    </div>
    """
    
    components.html(table_widget_html, height=80)
    
    # Create custom HTML table
    table_html = """
    <div style="overflow-x: auto; margin: 1rem 0;">
        <table style="width: 100%; border-collapse: collapse; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'; font-size: 14px;">
            <thead>
                <tr style="border-bottom: 2px solid #e5e7eb; background-color: #f9fafb;">
                    <th style="text-align: left; padding: 12px 16px; font-weight: 600; color: #374151;">Stage</th>
                    <th style="text-align: left; padding: 12px 16px; font-weight: 600; color: #374151;">Description</th>
                    <th style="text-align: right; padding: 12px 16px; font-weight: 600; color: #374151;">LP Amount</th>
                    <th style="text-align: right; padding: 12px 16px; font-weight: 600; color: #374151;">GP Amount</th>
                    <th style="text-align: right; padding: 12px 16px; font-weight: 600; color: #374151;">Total</th>
                    <th style="text-align: right; padding: 12px 16px; font-weight: 600; color: #374151;">% of Total</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add data rows
    for item in waterfall_categories:
        total = item['lp'] + item['gp']
        percentage = (total / total_fund_distributions * 100) if total_fund_distributions > 0 else 0
        table_html += f"""
                <tr style="border-bottom: 1px solid #e5e7eb; hover:background-color: #f9fafb;">
                    <td style="padding: 12px 16px; font-weight: 500; color: #111827;">{item['stage']}</td>
                    <td style="padding: 12px 16px; color: #6b7280; font-size: 13px;">{item['description']}</td>
                    <td style="padding: 12px 16px; text-align: right; font-weight: 600; color: #3b82f6;">${item['lp']:.1f}M</td>
                    <td style="padding: 12px 16px; text-align: right; font-weight: 600; color: #f97316;">${item['gp']:.1f}M</td>
                    <td style="padding: 12px 16px; text-align: right; font-weight: 600; color: #111827;">${total:.1f}M</td>
                    <td style="padding: 12px 16px; text-align: right; color: #6b7280;">{percentage:.1f}%</td>
                </tr>
        """
    
    # Add total row
    table_html += f"""
                <tr style="background-color: #f3f4f6; font-weight: bold; border-top: 2px solid #d1d5db;">
                    <td style="padding: 12px 16px; color: #111827;">Total Distribution</td>
                    <td style="padding: 12px 16px; color: #6b7280;"></td>
                    <td style="padding: 12px 16px; text-align: right; color: #3b82f6;">${total_lp_distributions:.1f}M</td>
                    <td style="padding: 12px 16px; text-align: right; color: #f97316;">${total_gp_distributions:.1f}M</td>
                    <td style="padding: 12px 16px; text-align: right; color: #111827;">${total_fund_distributions:.1f}M</td>
                    <td style="padding: 12px 16px; text-align: right; color: #6b7280;">100.0%</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    
    components.html(table_html, height=400, scrolling=True)
    
    st.markdown("---")
    
    # Year-by-Year LP Cash Flows Widget
    yearly_widget_html = f"""
    <div style="background: white; border-radius: 12px; box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1); padding: 1.5rem; margin: 1rem 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';">
        <div style="margin-bottom: 1rem;">
            <h2 style="font-size: 1.5rem; font-weight: bold; color: #111827; margin: 0 0 0.5rem 0;">📅 Year-by-Year LP Cash Flows</h2>
            <p style="color: #6b7280; margin: 0;">Annual contributions (negative) and distributions (positive) to Limited Partners</p>
        </div>
    </div>
    """
    
    components.html(yearly_widget_html, height=80)
    
    # Get yearly averages
    yearly_averages = waterfall_data['yearly_averages']
    
    # Prepare yearly data
    yearly_data = []
    cumulative = 0
    
    for _, row in yearly_averages.iterrows():
        year = int(row['Year'])
        contributions = -row['LP Contributions in year'] / 1_000_000
        return_of_capital = row['ROC to LP'] / 1_000_000
        preferred_return = row['Pref to LP'] / 1_000_000
        catchup_lp_cut = row['Catch-up LP cut'] / 1_000_000
        final_split_lp = row['Final Split to LP'] / 1_000_000
        
        # Calculate net cash flow and cumulative
        net_cash_flow = contributions + return_of_capital + preferred_return + catchup_lp_cut + final_split_lp
        cumulative += net_cash_flow
        
        yearly_data.append({
            'Year': f'Year {year}',
            'Capital Calls': contributions,
            'Return of Capital': return_of_capital,
            'Preferred Return': preferred_return,
            'Catch-up LP Cut': catchup_lp_cut,
            'Final Split LP': final_split_lp,
            'Net Cash Flow': net_cash_flow,
            'Cumulative': cumulative
        })
    
    # Create yearly cash flow chart
    fig_yearly = go.Figure()
    
    # Add negative bars for capital calls
    fig_yearly.add_trace(go.Bar(
        name='Capital Calls',
        x=[item['Year'] for item in yearly_data],
        y=[item['Capital Calls'] for item in yearly_data],
        marker_color='#dc2626',
        text=[f"${abs(item['Capital Calls']):.1f}M" if item['Capital Calls'] < 0 else "" for item in yearly_data],
        textposition='inside'
    ))
    
    # Add positive stacked bars for distributions
    fig_yearly.add_trace(go.Bar(
        name='Return of Capital',
        x=[item['Year'] for item in yearly_data],
        y=[item['Return of Capital'] for item in yearly_data],
        marker_color='#3b82f6',
        text=[f"${item['Return of Capital']:.1f}M" if item['Return of Capital'] > 0 else "" for item in yearly_data],
        textposition='inside'
    ))
    
    fig_yearly.add_trace(go.Bar(
        name='Preferred Return',
        x=[item['Year'] for item in yearly_data],
        y=[item['Preferred Return'] for item in yearly_data],
        marker_color='#10b981',
        text=[f"${item['Preferred Return']:.1f}M" if item['Preferred Return'] > 0 else "" for item in yearly_data],
        textposition='inside'
    ))
    
    fig_yearly.add_trace(go.Bar(
        name='Catch-up LP Cut',
        x=[item['Year'] for item in yearly_data],
        y=[item['Catch-up LP Cut'] for item in yearly_data],
        marker_color='#f59e0b',
        text=[f"${item['Catch-up LP Cut']:.1f}M" if item['Catch-up LP Cut'] > 0 else "" for item in yearly_data],
        textposition='inside'
    ))
    
    fig_yearly.add_trace(go.Bar(
        name='Final Split LP',
        x=[item['Year'] for item in yearly_data],
        y=[item['Final Split LP'] for item in yearly_data],
        marker_color='#8b5cf6',
        text=[f"${item['Final Split LP']:.1f}M" if item['Final Split LP'] > 0 else "" for item in yearly_data],
        textposition='inside'
    ))
    
    fig_yearly.update_layout(
        title="",
        xaxis_title="Year",
        yaxis_title="LP Cash Flow ($M)",
        barmode='relative',
        height=450,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif", size=12)
    )
    
    # Add zero reference line
    fig_yearly.add_hline(y=0, line_dash="dash", line_color="black", line_width=2)
    
    st.plotly_chart(fig_yearly, use_container_width=True)
    
    # Detailed LP Cash Flow Schedule Widget
    flow_schedule_widget_html = f"""
    <div style="background: white; border-radius: 12px; box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1); padding: 1.5rem; margin: 1rem 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';">
        <div style="margin-bottom: 1rem;">
            <h2 style="font-size: 1.5rem; font-weight: bold; color: #111827; margin: 0 0 0.5rem 0;">📋 Detailed LP Cash Flow Schedule</h2>
            <p style="color: #6b7280; margin: 0;">Complete annual breakdown of LP cash flows and cumulative totals</p>
        </div>
    </div>
    """
    
    components.html(flow_schedule_widget_html, height=80)
    
    # Create custom HTML table for flow schedule
    flow_table_html = """
    <div style="overflow-x: auto; margin: 1rem 0;">
        <table style="width: 100%; border-collapse: collapse; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'; font-size: 13px;">
            <thead>
                <tr style="border-bottom: 2px solid #d1d5db; background-color: #f9fafb;">
                    <th style="text-align: left; padding: 10px 12px; font-weight: 600; color: #374151;">Period</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Capital Calls</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Return of Capital</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Preferred Return</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Catch-up LP Cut</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Final Split LP</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Net Cash Flow</th>
                    <th style="text-align: right; padding: 10px 12px; font-weight: 600; color: #374151;">Cumulative</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add data rows
    for item in yearly_data:
        capital_calls_display = f"${abs(item['Capital Calls']):.1f}M" if item['Capital Calls'] < 0 else "-"
        return_capital_display = f"${item['Return of Capital']:.1f}M" if item['Return of Capital'] > 0 else "-"
        preferred_display = f"${item['Preferred Return']:.1f}M" if item['Preferred Return'] > 0 else "-"
        catchup_display = f"${item['Catch-up LP Cut']:.1f}M" if item['Catch-up LP Cut'] > 0 else "-"
        final_split_display = f"${item['Final Split LP']:.1f}M" if item['Final Split LP'] > 0 else "-"
        net_cash_display = f"${item['Net Cash Flow']:.1f}M" if item['Net Cash Flow'] >= 0 else f"(${abs(item['Net Cash Flow']):.1f}M)"
        cumulative_display = f"${item['Cumulative']:.1f}M" if item['Cumulative'] >= 0 else f"(${abs(item['Cumulative']):.1f}M)"
        
        # Color coding for net cash flow and cumulative
        net_cash_color = "#059669" if item['Net Cash Flow'] >= 0 else "#dc2626"
        cumulative_color = "#059669" if item['Cumulative'] >= 0 else "#dc2626"
        
        flow_table_html += f"""
                <tr style="border-bottom: 1px solid #e5e7eb; hover:background-color: #f9fafb;">
                    <td style="padding: 10px 12px; font-weight: 500; color: #111827;">{item['Year']}</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: #dc2626;">{capital_calls_display}</td>
                    <td style="padding: 10px 12px; text-align: right; color: #3b82f6;">{return_capital_display}</td>
                    <td style="padding: 10px 12px; text-align: right; color: #10b981;">{preferred_display}</td>
                    <td style="padding: 10px 12px; text-align: right; color: #f59e0b;">{catchup_display}</td>
                    <td style="padding: 10px 12px; text-align: right; color: #8b5cf6;">{final_split_display}</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: 600; color: {net_cash_color};">{net_cash_display}</td>
                    <td style="padding: 10px 12px; text-align: right; font-weight: bold; color: {cumulative_color};">{cumulative_display}</td>
                </tr>
        """
    
    # Add total row
    total_capital_calls = sum(abs(item['Capital Calls']) for item in yearly_data if item['Capital Calls'] < 0)
    total_return_capital = sum(item['Return of Capital'] for item in yearly_data)
    total_preferred = sum(item['Preferred Return'] for item in yearly_data)
    total_catchup = sum(item['Catch-up LP Cut'] for item in yearly_data)
    total_final_split = sum(item['Final Split LP'] for item in yearly_data)
    total_net = sum(item['Net Cash Flow'] for item in yearly_data)
    
    total_net_display = f"${total_net:.1f}M" if total_net >= 0 else f"(${abs(total_net):.1f}M)"
    total_net_color = "#059669" if total_net >= 0 else "#dc2626"
    
    flow_table_html += f"""
                <tr style="background-color: #f3f4f6; font-weight: bold; border-top: 2px solid #d1d5db;">
                    <td style="padding: 10px 12px; color: #111827;">Total</td>
                    <td style="padding: 10px 12px; text-align: right; color: #dc2626;">${total_capital_calls:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #3b82f6;">${total_return_capital:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #10b981;">${total_preferred:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #f59e0b;">${total_catchup:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: #8b5cf6;">${total_final_split:.1f}M</td>
                    <td style="padding: 10px 12px; text-align: right; color: {total_net_color};">{total_net_display}</td>
                    <td style="padding: 10px 12px; text-align: right; color: #6b7280;">-</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    
    components.html(flow_table_html, height=500, scrolling=True)

# Continue in next message with Setup Tab...