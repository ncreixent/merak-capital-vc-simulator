# setup_tab.py

import streamlit as st
import pandas as pd
import numpy as np
import yaml
from datetime import datetime
from pathlib import Path

from parameters_loader import load_parameters
from scenario_manager import ScenarioManager
from auth import check_user_permissions

def render_setup_tab():
    """Render the Scenario Management tab"""
    st.markdown("<h1 class='main-header'>Scenario Management</h1>", unsafe_allow_html=True)
    
    # 1. Display existing scenarios at the top
    st.subheader("Existing Scenarios")
    render_scenario_list()
    
    st.markdown("---")
    
    # 2. Create new scenario section
    st.subheader("Create New Scenario")
    
    # Check user permissions for scenario creation
    user_permissions = check_user_permissions(st.session_state.username)
    
    if 'create' not in user_permissions:
        st.warning("🔒 **Access Restricted**: You don't have permission to create new scenarios. Contact your administrator for access.")
        st.info("💡 You can still view existing scenarios and run simulations.")
        return
    
    # Check if user wants to create a new scenario
    if 'show_create_form' not in st.session_state:
        st.session_state.show_create_form = False
    
    if not st.session_state.show_create_form:
        if st.button("Create New Scenario", type="primary", use_container_width=True):
            st.session_state.show_create_form = True
            st.rerun()
    else:
        # Show configuration options
        render_create_scenario_form()

def render_scenario_list():
    """Render list of all scenarios with summary info including follow-on strategy"""
    from scenario_manager import ScenarioManager
    
    if not st.session_state.scenarios:
        st.info("No scenarios created yet. Use the 'Create New Scenario' button below to create your first scenario.")
        return
    
    scenario_data = []
    
    for name, scenario in st.session_state.scenarios.items():
        # Get follow-on strategy
        follow_on_strategy = "N/A"
        if 'follow_on_strategy' in scenario['config']:
            strategy_type = scenario['config']['follow_on_strategy'].get('type', 'N/A')
            if strategy_type == 'spray_and_pray':
                follow_on_strategy = "Spray and Pray"
            elif strategy_type == 'pro_rata':
                follow_on_strategy = "Pro Rata"
            else:
                follow_on_strategy = strategy_type
        
        row = {
            'Scenario Name': name,
            'Created': scenario['timestamp'].strftime('%Y-%m-%d %H:%M'),
            'Has Results': '✅' if scenario['results'] is not None else '❌',
            'Fund Size ($M)': f"${scenario['config'].get('committed_capital', 0) / 1_000_000:.0f}M",
            'Portfolio Size': scenario['config'].get('num_investments', 'N/A'),
            'Follow-on Strategy': follow_on_strategy,
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
    
    # Create custom table with action buttons
    
    # Table header
    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([3, 2, 1, 2, 2, 2, 2, 2, 1, 1])
    
    with col1:
        st.markdown("**Scenario Name**")
    with col2:
        st.markdown("**Created**")
    with col3:
        st.markdown("**Results**")
    with col4:
        st.markdown("**Fund Size**")
    with col5:
        st.markdown("**Portfolio**")
    with col6:
        st.markdown("**Strategy**")
    with col7:
        st.markdown("**Net IRR**")
    with col8:
        st.markdown("**Net Multiple**")
    with col9:
        st.markdown("**View**")
    with col10:
        st.markdown("**Delete**")
    
    st.markdown("---")
    
    # Table rows
    for i, row in enumerate(scenario_data):
        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([3, 2, 1, 2, 2, 2, 2, 2, 1, 1])
        
        with col1:
            st.write(row['Scenario Name'])
        with col2:
            st.write(row['Created'])
        with col3:
            st.write(row['Has Results'])
        with col4:
            st.write(row['Fund Size ($M)'])
        with col5:
            st.write(row['Portfolio Size'])
        with col6:
            st.write(row['Follow-on Strategy'])
        with col7:
            st.write(row['Median Net IRR'])
        with col8:
            st.write(row['Median Net Multiple'])
        with col9:
            if st.button("View", key=f"view_summary_{i}", help="View configuration summary"):
                st.session_state.selected_scenario_for_summary = row['Scenario Name']
                st.rerun()
        with col10:
            if st.button("Delete", key=f"delete_scenario_{i}", help="Delete scenario"):
                if row['Scenario Name'] in st.session_state.scenarios:
                    del st.session_state.scenarios[row['Scenario Name']]
                    st.success(f"Scenario '{row['Scenario Name']}' deleted")
                    st.rerun()
    
    # Display configuration summary if a scenario is selected
    if 'selected_scenario_for_summary' in st.session_state and st.session_state.selected_scenario_for_summary:
        display_scenario_configuration_summary(st.session_state.selected_scenario_for_summary)
    

def display_scenario_configuration_summary(scenario_name):
    """Display detailed configuration summary for a selected scenario"""
    if scenario_name not in st.session_state.scenarios:
        st.error(f"Scenario '{scenario_name}' not found")
        return
    
    scenario = st.session_state.scenarios[scenario_name]
    config = scenario['config']
    
    st.markdown("---")
    st.markdown(f"#### 📊 Configuration Summary: {scenario_name}")
    
    # Basic info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Created", scenario['timestamp'].strftime('%Y-%m-%d %H:%M'))
    
    with col2:
        has_results = "✅ Yes" if scenario['results'] is not None else "❌ No"
        st.metric("Has Results", has_results)
    
    with col3:
        fund_size = config.get('committed_capital', 0) / 1_000_000
        st.metric("Fund Size", f"${fund_size:.0f}M")
    
    st.markdown("---")
    
    # Fund Structure
    st.markdown("#### 🏦 Fund Structure")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Fund Size", f"${config.get('committed_capital', 0) / 1_000_000:.0f}M")
        st.metric("Portfolio Size", f"{config.get('num_investments', 'N/A')} companies")
    
    with col2:
        mgmt_fee = config.get('mgmt_fee_commitment_period_rate', 0) * 100
        st.metric("Management Fee", f"{mgmt_fee:.1f}%")
        fund_life = config.get('fund_lifespan_months', 0) / 12
        st.metric("Fund Life", f"{fund_life:.0f} years")
    
    with col3:
        carried_interest = config.get('waterfall', {}).get('carried_interest_pct', 0) * 100
        st.metric("Carried Interest", f"{carried_interest:.1f}%")
        preferred_return = config.get('waterfall', {}).get('preferred_return_pct', 0) * 100
        st.metric("Preferred Return", f"{preferred_return:.1f}%")
    
    with col4:
        max_deals = config.get('max_deals_per_year', 'N/A')
        st.metric("Max Deals/Year", max_deals)
        investment_period = config.get('investment_period_months', 0) / 12
        st.metric("Investment Period", f"{investment_period:.0f} years")
    
    st.markdown("---")
    
    # Investment Strategy
    st.markdown("#### 🎯 Investment Strategy")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Follow-on Strategy:**")
        follow_on_strategy = config.get('follow_on_strategy', {})
        strategy_type = follow_on_strategy.get('type', 'N/A')
        if strategy_type == 'spray_and_pray':
            st.write("• **Spray and Pray**")
        elif strategy_type == 'pro_rata':
            st.write("• **Pro Rata**")
        else:
            st.write(f"• {strategy_type}")
        
        passive_rate = follow_on_strategy.get('passive_participation_rate', 0) * 100
        st.write(f"• Passive Participation Rate: {passive_rate:.0f}%")
        
        st.markdown("**Initial Ownership Targets:**")
        ownership_targets = config.get('initial_ownership_targets', {})
        for stage, target in ownership_targets.items():
            st.write(f"• {stage}: {target*100:.1f}%")
    
    with col2:
        st.markdown("**Dynamic Stage Allocation:**")
        stage_allocation = config.get('dynamic_stage_allocation', [])
        
        if stage_allocation:
            allocation_data = []
            for year_data in stage_allocation:
                allocation_data.append({
                    'Year': year_data.get('year', 'N/A'),
                    'Pre-Seed': f"{year_data.get('allocation', {}).get('Pre-Seed', 0)*100:.0f}%",
                    'Seed': f"{year_data.get('allocation', {}).get('Seed', 0)*100:.0f}%",
                    'Series A': f"{year_data.get('allocation', {}).get('Series A', 0)*100:.0f}%"
                })
            
            df_allocation = pd.DataFrame(allocation_data)
            st.dataframe(df_allocation, use_container_width=True, hide_index=True)
        else:
            st.write("No stage allocation data available")
    
    st.markdown("---")
    
    # Performance Metrics (if available)
    if scenario['results'] is not None:
        st.markdown("#### 📈 Performance Metrics")
        from scenario_manager import ScenarioManager
        
        metrics = ScenarioManager.calculate_metrics(scenario)
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Median Net IRR", f"{metrics['median_net_irr']:.2%}")
                st.metric("Mean Net IRR", f"{metrics['mean_net_irr']:.2%}")
            
            with col2:
                st.metric("Median Net Multiple", f"{metrics['median_net_multiple']:.2f}x")
                st.metric("Mean Net Multiple", f"{metrics['mean_net_multiple']:.2f}x")
            
            with col3:
                st.metric("Median Gross IRR", f"{metrics['median_gross_irr']:.2%}")
                st.metric("Mean Gross IRR", f"{metrics['mean_gross_irr']:.2%}")
            
            with col4:
                st.metric("VaR (5%)", f"{metrics['var_5']:.2%}")
                st.metric("VaR (10%)", f"{metrics['var_10']:.2%}")
    
    # Close button
    st.markdown("---")
    if st.button("❌ Close Summary", use_container_width=True):
        st.session_state.selected_scenario_for_summary = None
        st.rerun()

def render_create_scenario_form():
    """Render the create scenario form with configuration options"""
    st.markdown("#### 🔧 Configuration Mode")
    
    config_mode = st.radio(
        "Choose configuration approach:",
        ["Basic Configuration", "Advanced Configuration", "Load from File", "Import Scenario"],
        horizontal=True,
        key="create_scenario_config_mode"
    )
    
    st.markdown("---")
    
    if config_mode == "Basic Configuration":
        render_basic_config()
    elif config_mode == "Advanced Configuration":
        render_advanced_config()
    elif config_mode == "Load from File":
        render_file_config()
    else:  # Import Scenario
        render_import_scenario()
    
    # Cancel button
    st.markdown("---")
    if st.button("Cancel", use_container_width=True):
        st.session_state.show_create_form = False
        st.rerun()

def render_basic_config():
    """Render basic configuration interface"""
    st.subheader("Basic Fund Parameters")
    
    with st.form("basic_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Fund Structure")
            fund_size = st.number_input(
                "Fund Size ($M)",
                min_value=10.0,
                max_value=10000.0,
                value=50.0,
                step=10.0,
                help="Total fund size in millions"
            )
            
            management_fee = st.slider(
                "Management Fee (%)",
                min_value=1.0,
                max_value=3.0,
                value=2.0,
                step=0.1,
                help="Annual management fee as percentage of committed capital"
            )
            
            carried_interest = st.slider(
                "Carried Interest (%)",
                min_value=15.0,
                max_value=25.0,
                value=20.0,
                step=0.5,
                help="GP carried interest percentage"
            )
            
            preferred_return = st.slider(
                "Preferred Return (%)",
                min_value=6.0,
                max_value=12.0,
                value=8.0,
                step=0.5,
                help="Annual preferred return to LPs"
            )
            
            fund_life = st.number_input(
                "Fund Life (Years)",
                min_value=8,
                max_value=15,
                value=10,
                step=1,
                help="Total fund life in years"
            )
        
        with col2:
            st.markdown("#### Investment Strategy")
            num_companies = st.number_input(
                "Target Portfolio Size",
                min_value=10,
                max_value=200,
                value=40,
                step=1,
                help="Number of companies to invest in"
            )
            
            follow_on_strategy = st.selectbox(
                "Follow-on Strategy",
                options=["spray_and_pray", "pro_rata"],
                format_func=lambda x: "Spray and Pray" if x == "spray_and_pray" else "Pro Rata",
                help="Investment strategy for follow-on rounds"
            )
            
            st.markdown("**Initial Ownership Targets (%)**")
            ownership_pre_seed = st.slider(
                "Pre-Seed Ownership (%)",
                min_value=5.0,
                max_value=30.0,
                value=15.0,
                step=0.5,
                help="Target ownership percentage for Pre-Seed investments"
            )
            
            ownership_seed = st.slider(
                "Seed Ownership (%)",
                min_value=5.0,
                max_value=30.0,
                value=15.0,
                step=0.5,
                help="Target ownership percentage for Seed investments"
            )
            
            ownership_series_a = st.slider(
                "Series A Ownership (%)",
                min_value=5.0,
                max_value=30.0,
                value=15.0,
                step=0.5,
                help="Target ownership percentage for Series A investments"
            )
        
        st.markdown("---")
        
        # Dynamic Stage Allocation Table
        st.markdown("#### Dynamic Stage Allocation (%)")
        st.markdown("Configure how the fund allocates investments across stages over time. Values must sum to 100% for each year.")
        
        # Create a table for stage allocation
        stage_allocation_data = []
        
        for year in range(1, 6):
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                st.write(f"**Year {year}**")
            
            with col2:
                pre_seed_pct = st.number_input(
                    f"Pre-Seed %",
                    min_value=0.0,
                    max_value=100.0,
                    value=50.0 if year == 1 else 40.0 if year == 2 else 20.0 if year == 3 else 10.0 if year == 4 else 0.0,
                    step=5.0,
                    key=f"pre_seed_{year}",
                    help=f"Pre-Seed allocation for year {year}"
                )
            
            with col3:
                seed_pct = st.number_input(
                    f"Seed %",
                    min_value=0.0,
                    max_value=100.0,
                    value=50.0 if year == 1 else 55.0 if year == 2 else 70.0 if year == 3 else 80.0 if year == 4 else 70.0,
                    step=5.0,
                    key=f"seed_{year}",
                    help=f"Seed allocation for year {year}"
                )
            
            with col4:
                series_a_pct = st.number_input(
                    f"Series A %",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0 if year == 1 else 5.0 if year == 2 else 10.0 if year == 3 else 10.0 if year == 4 else 30.0,
                    step=5.0,
                    key=f"series_a_{year}",
                    help=f"Series A allocation for year {year}"
                )
            
            # Validate that percentages sum to 100%
            total_pct = pre_seed_pct + seed_pct + series_a_pct
            if abs(total_pct - 100.0) > 0.1:  # Allow small floating point errors
                st.error(f"Year {year} allocations must sum to 100%. Current total: {total_pct:.1f}%")
            
            stage_allocation_data.append({
                'year': year,
                'Pre-Seed': pre_seed_pct / 100.0,
                'Seed': seed_pct / 100.0,
                'Series A': series_a_pct / 100.0
            })
        
        st.markdown("---")
        
        # Real-time Configuration Summary
        st.markdown("#### 📋 Configuration Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Fund Structure:**")
            st.write(f"- Fund Size: ${fund_size:.0f}M")
            st.write(f"- Management Fee: {management_fee:.1f}%")
            st.write(f"- Carried Interest: {carried_interest:.1f}%")
            st.write(f"- Preferred Return: {preferred_return:.1f}%")
            st.write(f"- Fund Life: {fund_life:.0f} years")
        
        with col2:
            st.markdown("**Investment Strategy:**")
            st.write(f"- Portfolio Size: {num_companies} companies")
            st.write(f"- Follow-on Strategy: {'Spray and Pray' if follow_on_strategy == 'spray_and_pray' else 'Pro Rata'}")
            st.write(f"- Pre-Seed Ownership: {ownership_pre_seed:.1f}%")
            st.write(f"- Seed Ownership: {ownership_seed:.1f}%")
            st.write(f"- Series A Ownership: {ownership_series_a:.1f}%")
        
        # Stage Allocation Summary
        st.markdown("**Stage Allocation Over Time:**")
        allocation_summary = []
        for year_data in stage_allocation_data:
            allocation_summary.append({
                'Year': year_data['year'],
                'Pre-Seed': f"{year_data['Pre-Seed']*100:.0f}%",
                'Seed': f"{year_data['Seed']*100:.0f}%",
                'Series A': f"{year_data['Series A']*100:.0f}%"
            })
        
        df_allocation = pd.DataFrame(allocation_summary)
        st.dataframe(df_allocation, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Scenario naming - use session state to persist user input
        if 'basic_config_scenario_name' not in st.session_state:
            st.session_state.basic_config_scenario_name = f"Basic Config - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        scenario_name = st.text_input(
            "Scenario Name",
            value=st.session_state.basic_config_scenario_name,
            help="Name for this scenario configuration",
            key="basic_config_scenario_name_input"
        )
        
        # Update session state when user changes the input
        if scenario_name != st.session_state.basic_config_scenario_name:
            st.session_state.basic_config_scenario_name = scenario_name
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Scenario", type="primary")
        
        if submitted:
            create_scenario_from_basic_config(
                scenario_name, fund_size, num_companies, management_fee,
                carried_interest, preferred_return, fund_life, follow_on_strategy,
                ownership_pre_seed, ownership_seed, ownership_series_a,
                stage_allocation_data
            )

def render_advanced_config():
    """Render advanced configuration interface with form-based inputs"""
    st.subheader("🔬 Advanced Configuration")
    
    st.info("💡 **Advanced Mode**: Configure all fund parameters with detailed customization options.")
    
    # Load current config as starting point for defaults
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            default_config = yaml.safe_load(f)
    except FileNotFoundError:
        st.error("Default config.yaml not found. Please ensure the file exists.")
        return
    
    with st.form("advanced_config_form"):
        # 1. Basic Fund Parameters (same as Basic Config)
        st.markdown("#### 📊 Basic Fund Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Fund Structure")
            fund_size = st.number_input(
                "Fund Size ($M)",
                min_value=10.0,
                max_value=10000.0,
                value=default_config.get('committed_capital', 50000000) / 1_000_000,
                step=10.0,
                help="Total fund size in millions",
                key="adv_fund_size"
            )
            
            management_fee = st.slider(
                "Management Fee (%)",
                min_value=1.0,
                max_value=3.0,
                value=default_config.get('mgmt_fee_commitment_period_rate', 0.02) * 100,
                step=0.1,
                help="Annual management fee as percentage of committed capital",
                key="adv_mgmt_fee"
            )
            
            carried_interest = st.slider(
                "Carried Interest (%)",
                min_value=15.0,
                max_value=25.0,
                value=default_config.get('waterfall', {}).get('carried_interest_pct', 0.2) * 100,
                step=0.5,
                help="GP carried interest percentage",
                key="adv_carried_interest"
            )
            
            preferred_return = st.slider(
                "Preferred Return (%)",
                min_value=6.0,
                max_value=12.0,
                value=default_config.get('waterfall', {}).get('preferred_return_pct', 0.08) * 100,
                step=0.5,
                help="Annual preferred return to LPs",
                key="adv_preferred_return"
            )
        
        with col2:
            st.markdown("##### Investment Strategy")
            num_companies = st.number_input(
                "Target Portfolio Size",
                min_value=10,
                max_value=200,
                value=default_config.get('num_investments', 40),
                step=1,
                help="Number of companies to invest in",
                key="adv_num_companies"
            )
            
            max_deals_per_year = st.number_input(
                "Max Deals per Year",
                min_value=1,
                max_value=50,
                value=default_config.get('max_deals_per_year', 8),
                step=1,
                help="Maximum number of deals per year",
                key="adv_max_deals"
            )
            
            follow_on_strategy = st.selectbox(
                "Follow-on Strategy",
                options=["spray_and_pray", "pro_rata"],
                format_func=lambda x: "Spray and Pray" if x == "spray_and_pray" else "Pro Rata",
                index=0 if default_config.get('follow_on_strategy', {}).get('type', 'spray_and_pray') == 'spray_and_pray' else 1,
                help="Investment strategy for follow-on rounds",
                key="adv_follow_on"
            )
            
            st.markdown("**Initial Ownership Targets (%)**")
            ownership_pre_seed = st.slider(
                "Pre-Seed Ownership (%)",
                min_value=5.0,
                max_value=30.0,
                value=default_config.get('initial_ownership_targets', {}).get('Pre-Seed', 0.15) * 100,
                step=0.5,
                key="adv_own_pre_seed"
            )
            
            ownership_seed = st.slider(
                "Seed Ownership (%)",
                min_value=5.0,
                max_value=30.0,
                value=default_config.get('initial_ownership_targets', {}).get('Seed', 0.15) * 100,
                step=0.5,
                key="adv_own_seed"
            )
            
            ownership_series_a = st.slider(
                "Series A Ownership (%)",
                min_value=5.0,
                max_value=30.0,
                value=default_config.get('initial_ownership_targets', {}).get('Series A', 0.15) * 100,
                step=0.5,
                key="adv_own_series_a"
            )
        
        st.markdown("---")
        
        # 2. Capital Calls Configuration
        st.markdown("#### 💰 Capital Calls Configuration")
        col1, col2 = st.columns(2)
    
        with col1:
            minimum_cash_balance_pct = st.slider(
                "Minimum Cash Balance (%)",
                min_value=0.0,
                max_value=20.0,
                value=default_config.get('capital_calls', {}).get('minimum_cash_balance_pct', 0.05) * 100,
                step=0.5,
                help="Minimum cash balance as percentage of committed capital",
                key="adv_min_cash"
            )
        
        with col2:
            tranche_size_pct = st.slider(
                "Tranche Size (%)",
                min_value=5.0,
                max_value=50.0,
                value=default_config.get('capital_calls', {}).get('tranche_size_pct', 0.25) * 100,
                step=1.0,
                help="Size of each capital call tranche as percentage",
                key="adv_tranche_size"
            )
        
        st.markdown("---")
        
        # 3. Fund Lifespan Configuration
        st.markdown("#### ⏱️ Fund Lifespan Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            fund_lifespan_months = st.number_input(
                "Fund Lifespan (Months)",
                min_value=60,
                max_value=180,
                value=default_config.get('fund_lifespan_months', 120),
                step=6,
                help="Total fund lifespan in months",
                key="adv_fund_lifespan"
            )
        
        with col2:
            fund_lifespan_extensions_months = st.number_input(
                "Fund Lifespan Extensions (Months)",
                min_value=0,
                max_value=60,
                value=default_config.get('fund_lifespan_extensions_months', 24),
                step=6,
                help="Additional months available through extensions",
                key="adv_fund_extensions"
            )
        
        st.markdown("---")
        
        # 4. Management Fees Configuration
        st.markdown("#### 💼 Management Fees Configuration")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mgmt_fee_commitment = st.slider(
                "Commitment Period Fee (%)",
                min_value=1.0,
                max_value=3.0,
                value=default_config.get('mgmt_fee_commitment_period_rate', 0.02) * 100,
                step=0.1,
                help="Management fee during commitment period",
                key="adv_mgmt_commitment"
            )
        
        with col2:
            mgmt_fee_extension = st.slider(
                "Extension Period Fee (%)",
                min_value=0.5,
                max_value=2.0,
                value=default_config.get('mgmt_fee_extension_period_rate', 0.01) * 100,
                step=0.1,
                help="Management fee during extension period",
                key="adv_mgmt_extension"
            )
        
        with col3:
            mgmt_fee_post_commitment = st.slider(
                "Post-Commitment Fee (%)",
                min_value=1.0,
                max_value=2.5,
                value=default_config.get('mgmt_fee_post_commitment_period_rate', 0.0175) * 100,
                step=0.05,
                help="Management fee after commitment period",
                key="adv_mgmt_post"
            )
        
        st.markdown("---")
        
        # 5. Dynamic Stage Allocation (same as Basic Config)
        st.markdown("#### 📈 Dynamic Stage Allocation (%)")
        st.markdown("Configure how the fund allocates investments across stages over time. Values must sum to 100% for each year.")
        
        stage_allocation_data = []
        default_allocation = default_config.get('dynamic_stage_allocation', [])
        
        for year in range(1, 6):
            # Get default values for this year
            year_default = next((item for item in default_allocation if item.get('year') == year), None)
            default_pre_seed = year_default.get('allocation', {}).get('Pre-Seed', 0) * 100 if year_default else (50.0 if year == 1 else 40.0 if year == 2 else 20.0 if year == 3 else 10.0 if year == 4 else 0.0)
            default_seed = year_default.get('allocation', {}).get('Seed', 0) * 100 if year_default else (50.0 if year == 1 else 55.0 if year == 2 else 70.0 if year == 3 else 80.0 if year == 4 else 70.0)
            default_series_a = year_default.get('allocation', {}).get('Series A', 0) * 100 if year_default else (0.0 if year == 1 else 5.0 if year == 2 else 10.0 if year == 3 else 10.0 if year == 4 else 30.0)
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                st.write(f"**Year {year}**")
            
            with col2:
                pre_seed_pct = st.number_input(
                    f"Pre-Seed %",
                    min_value=0.0,
                    max_value=100.0,
                    value=default_pre_seed,
                    step=5.0,
                    key=f"adv_pre_seed_{year}",
                    help=f"Pre-Seed allocation for year {year}"
                )
            
            with col3:
                seed_pct = st.number_input(
                    f"Seed %",
                    min_value=0.0,
                    max_value=100.0,
                    value=default_seed,
                    step=5.0,
                    key=f"adv_seed_{year}",
                    help=f"Seed allocation for year {year}"
                )
            
            with col4:
                series_a_pct = st.number_input(
                    f"Series A %",
                    min_value=0.0,
                    max_value=100.0,
                    value=default_series_a,
                    step=5.0,
                    key=f"adv_series_a_{year}",
                    help=f"Series A allocation for year {year}"
                )
            
            # Validate that percentages sum to 100%
            total_pct = pre_seed_pct + seed_pct + series_a_pct
            if abs(total_pct - 100.0) > 0.1:  # Allow small floating point errors
                st.error(f"Year {year} allocations must sum to 100%. Current total: {total_pct:.1f}%")
            
            stage_allocation_data.append({
                'year': year,
                'Pre-Seed': pre_seed_pct / 100.0,
                'Seed': seed_pct / 100.0,
                'Series A': series_a_pct / 100.0
            })
        
        st.markdown("---")
        
        # 6. Stage Customization (separate expandable section)
        st.markdown("#### 🎯 Stage Customization")
        st.markdown("Customize detailed parameters for each investment stage.")
        
        stages_config = {}
        stages_order = default_config.get('stages_order', ['Pre-Seed', 'Seed', 'Series A', 'Series B', 'Series C'])
        default_stages = default_config.get('stages', {})
        
        # Create tabs for each stage
        stage_tabs = st.tabs(stages_order)
        
        for idx, stage_name in enumerate(stages_order):
            with stage_tabs[idx]:
                stage_default = default_stages.get(stage_name, {})
                
                st.markdown(f"##### {stage_name} Stage Parameters")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    min_valuation = st.number_input(
                        "Min Valuation ($)",
                        min_value=0,
                        max_value=1000000000,
                        value=stage_default.get('min_valuation', 0),
                        step=100000,
                        format="%d",
                        key=f"adv_{stage_name}_min_val",
                        help=f"Minimum post-money valuation for {stage_name}"
                    )
                    
                    max_valuation = st.number_input(
                        "Max Valuation ($)",
                        min_value=0,
                        max_value=1000000000,
                        value=stage_default.get('max_valuation', 0),
                        step=100000,
                        format="%d",
                        key=f"adv_{stage_name}_max_val",
                        help=f"Maximum post-money valuation for {stage_name}"
                    )
                    
                    time_in_stage = st.number_input(
                        "Time in Stage (Months)",
                        min_value=1,
                        max_value=60,
                        value=stage_default.get('time_in_stage_months', 12),
                        step=1,
                        key=f"adv_{stage_name}_time",
                        help=f"Average time spent in {stage_name} stage"
                    )
                    
                    target_dilution = st.number_input(
                        "Target Dilution (%)",
                        min_value=0.0,
                        max_value=50.0,
                        value=(stage_default.get('target_dilution_pct', 0.2) * 100) if stage_default.get('target_dilution_pct') is not None else 0.0,
                        step=0.5,
                        key=f"adv_{stage_name}_dilution",
                        help=f"Target dilution percentage for {stage_name}"
                    )
                
                with col2:
                    prob_to_exit = st.slider(
                        "Probability to Exit (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=stage_default.get('prob_to_exit', 0.0) * 100,
                        step=0.5,
                        key=f"adv_{stage_name}_exit",
                        help=f"Probability of exit from {stage_name} stage"
                    )
                    
                    prob_to_fail = st.slider(
                        "Probability to Fail (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=stage_default.get('prob_to_fail', 0.0) * 100,
                        step=0.5,
                        key=f"adv_{stage_name}_fail",
                        help=f"Probability of failure from {stage_name} stage"
                    )
                    
                    # Get prob_to_next_stage, ensuring it's a float (not a list)
                    prob_to_next_raw = stage_default.get('prob_to_next_stage', 0.0)
                    if isinstance(prob_to_next_raw, list):
                        prob_to_next_raw = prob_to_next_raw[0] if prob_to_next_raw else 0.0
                    elif not isinstance(prob_to_next_raw, (int, float)):
                        prob_to_next_raw = 0.0
                    
                    prob_to_next = st.slider(
                        "Probability to Next Stage (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(prob_to_next_raw) * 100,
                        step=0.5,
                        key=f"adv_{stage_name}_next",
                        help=f"Probability of advancing to next stage from {stage_name}"
                    )
                
                st.markdown("**Valuation Distributions**")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown("**Post-Money Valuation Distribution**")
                    post_money_median = st.number_input(
                        "Median Valuation ($)",
                        min_value=0,
                        max_value=1000000000,
                        value=stage_default.get('post_money_valuation_dist', {}).get('median_valuation', 0),
                        step=100000,
                        format="%d",
                        key=f"adv_{stage_name}_post_median",
                        help="Median post-money valuation"
                    )
                    
                    post_money_sigma = st.number_input(
                        "Sigma (Log)",
                        min_value=0.1,
                        max_value=5.0,
                        value=stage_default.get('post_money_valuation_dist', {}).get('sigma_log', 1.0),
                        step=0.1,
                        key=f"adv_{stage_name}_post_sigma",
                        help="Log-normal distribution sigma parameter"
                    )
                
                with col4:
                    st.markdown("**Multiple to Next Stage Distribution**")
                    multiple_median = st.number_input(
                        "Median Multiple",
                        min_value=0.1,
                        max_value=20.0,
                        value=stage_default.get('multiple_to_next_dist', {}).get('median_valuation', 1.0),
                        step=0.1,
                        key=f"adv_{stage_name}_mult_median",
                        help="Median multiple to next stage"
                    )
                    
                    multiple_sigma = st.number_input(
                        "Sigma (Log)",
                        min_value=0.1,
                        max_value=5.0,
                        value=stage_default.get('multiple_to_next_dist', {}).get('sigma_log', 1.0),
                        step=0.1,
                        key=f"adv_{stage_name}_mult_sigma",
                        help="Log-normal distribution sigma parameter"
                    )
                
                # Store stage configuration
                stages_config[stage_name] = {
                    'min_valuation': min_valuation,
                    'max_valuation': max_valuation,
                    'time_in_stage_months': time_in_stage,
                    'target_dilution_pct': target_dilution / 100.0 if target_dilution > 0 else None,
                    'prob_to_exit': prob_to_exit / 100.0,
                    'prob_to_fail': prob_to_fail / 100.0,
                    'prob_to_next_stage': prob_to_next / 100.0,
                    'post_money_valuation_dist': {
                        'median_valuation': post_money_median,
                        'sigma_log': post_money_sigma,
                        'type': 'lognormal'
                    },
                    'multiple_to_next_dist': {
                        'median_valuation': multiple_median,
                        'sigma_log': multiple_sigma,
                        'type': 'lognormal'
                    }
                }
        
        st.markdown("---")
        
        # Scenario naming
        if 'advanced_config_scenario_name' not in st.session_state:
            st.session_state.advanced_config_scenario_name = f"Advanced Config - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        scenario_name = st.text_input(
            "Scenario Name",
            value=st.session_state.advanced_config_scenario_name,
            help="Name for this scenario configuration",
            key="advanced_config_scenario_name_input"
        )
        
        # Update session state when user changes the input
        if scenario_name != st.session_state.advanced_config_scenario_name:
            st.session_state.advanced_config_scenario_name = scenario_name
    
        # Submit button
        submitted = st.form_submit_button("🚀 Create Scenario", type="primary")
        
        if submitted:
            # stages_config is already built with form values in the loop above
            # All form input variables are available here with their submitted values
            create_scenario_from_advanced_config_form(
                scenario_name, fund_size, num_companies, management_fee,
                carried_interest, preferred_return, max_deals_per_year,
                follow_on_strategy, ownership_pre_seed, ownership_seed, ownership_series_a,
                minimum_cash_balance_pct, tranche_size_pct,
                fund_lifespan_months, fund_lifespan_extensions_months,
                mgmt_fee_commitment, mgmt_fee_extension, mgmt_fee_post_commitment,
                stage_allocation_data, stages_config, default_config
            )

def render_file_config():
    """Render file upload configuration interface"""
    st.subheader("📁 Load Configuration from File")
    
    st.info("💡 **File Upload**: Upload a custom configuration YAML file.")
    
    uploaded_file = st.file_uploader(
        "Choose a YAML configuration file",
        type=['yaml', 'yml'],
        help="Upload a custom configuration file"
    )
    
    if uploaded_file is not None:
        try:
            # Read and display the uploaded config
            config_content = uploaded_file.read().decode('utf-8')
            config_dict = yaml.safe_load(config_content)
            
            st.success("✅ Configuration file loaded successfully!")
            
            # Display preview
            with st.expander("📋 Preview Configuration", expanded=True):
                st.code(config_content, language='yaml')
            
            # Scenario naming - use session state to persist user input
            if 'file_config_scenario_name' not in st.session_state:
                st.session_state.file_config_scenario_name = f"File Config - {uploaded_file.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            scenario_name = st.text_input(
                "Scenario Name",
                value=st.session_state.file_config_scenario_name,
                help="Name for this scenario configuration",
                key="file_config_scenario_name_input"
            )
            
            # Update session state when user changes the input
            if scenario_name != st.session_state.file_config_scenario_name:
                st.session_state.file_config_scenario_name = scenario_name
            
            if st.button("🚀 Create Scenario", type="primary"):
                create_scenario_from_file_config(scenario_name, config_dict)
                
        except yaml.YAMLError as e:
            st.error(f"❌ Invalid YAML file: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

def create_scenario_from_basic_config(scenario_name, fund_size, num_companies, management_fee,
                                    carried_interest, preferred_return, fund_life, follow_on_strategy,
                                    ownership_pre_seed, ownership_seed, ownership_series_a,
                                    stage_allocation_data):
    """Create scenario from basic configuration parameters"""
    
    # Check user permissions
    user_permissions = check_user_permissions(st.session_state.username)
    if 'create' not in user_permissions:
        st.error("❌ Access denied: You don't have permission to create scenarios.")
        return
    
    try:
        # Load base config
        with open('config.yaml', 'r', encoding='utf-8') as f:
            base_config = yaml.safe_load(f)
        
        # Update Fund Structure parameters
        base_config['committed_capital'] = fund_size * 1_000_000  # Convert to actual dollars
        base_config['mgmt_fee_commitment_period_rate'] = management_fee / 100
        base_config['waterfall']['carried_interest_pct'] = carried_interest / 100
        base_config['waterfall']['preferred_return_pct'] = preferred_return / 100
        base_config['fund_lifespan_months'] = fund_life * 12
        
        # Update Investment Strategy parameters
        base_config['num_investments'] = num_companies
        base_config['follow_on_strategy']['type'] = follow_on_strategy
        
        # Update Initial Ownership Targets
        base_config['initial_ownership_targets'] = {
            'Pre-Seed': ownership_pre_seed / 100.0,
            'Seed': ownership_seed / 100.0,
            'Series A': ownership_series_a / 100.0,
            'Series B': 0.15,  # Keep default
            'Series C': 0.15   # Keep default
        }
        
        # Update Dynamic Stage Allocation
        base_config['dynamic_stage_allocation'] = []
        for year_data in stage_allocation_data:
            base_config['dynamic_stage_allocation'].append({
                'year': year_data['year'],
                'allocation': {
                    'Pre-Seed': year_data['Pre-Seed'],
                    'Seed': year_data['Seed'],
                    'Series A': year_data['Series A']
                }
            })
        
        # Create scenario
        scenario = ScenarioManager.create_scenario(scenario_name, base_config)
        
        # Add to session state
        st.session_state.scenarios[scenario_name] = scenario
        st.session_state.current_scenario_name = scenario_name
        
        # Close the create form and clear scenario name
        st.session_state.show_create_form = False
        if 'basic_config_scenario_name' in st.session_state:
            del st.session_state.basic_config_scenario_name
        
        st.success(f"✅ Scenario '{scenario_name}' created successfully!")
        st.info("💡 Go to the 'Run & Analyze' tab to execute the simulation.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating scenario: {str(e)}")

def create_scenario_from_advanced_config_form(scenario_name, fund_size, num_companies, management_fee,
                                             carried_interest, preferred_return, max_deals_per_year,
                                             follow_on_strategy, ownership_pre_seed, ownership_seed, ownership_series_a,
                                             minimum_cash_balance_pct, tranche_size_pct,
                                             fund_lifespan_months, fund_lifespan_extensions_months,
                                             mgmt_fee_commitment, mgmt_fee_extension, mgmt_fee_post_commitment,
                                             stage_allocation_data, stages_config, default_config):
    """Create scenario from advanced configuration form inputs"""
    
    # Check user permissions
    user_permissions = check_user_permissions(st.session_state.username)
    if 'create' not in user_permissions:
        st.error("❌ Access denied: You don't have permission to create scenarios.")
        return
    
    try:
        # Start with base config
        base_config = default_config.copy()
        
        # Update Fund Structure parameters
        base_config['committed_capital'] = fund_size * 1_000_000  # Convert to actual dollars
        base_config['mgmt_fee_commitment_period_rate'] = management_fee / 100
        base_config['waterfall']['carried_interest_pct'] = carried_interest / 100
        base_config['waterfall']['preferred_return_pct'] = preferred_return / 100
        base_config['fund_lifespan_months'] = fund_lifespan_months
        base_config['fund_lifespan_extensions_months'] = fund_lifespan_extensions_months
        
        # Update Investment Strategy parameters
        base_config['num_investments'] = num_companies
        base_config['max_deals_per_year'] = max_deals_per_year
        base_config['follow_on_strategy']['type'] = follow_on_strategy
        
        # Update Initial Ownership Targets
        base_config['initial_ownership_targets'] = {
            'Pre-Seed': ownership_pre_seed / 100.0,
            'Seed': ownership_seed / 100.0,
            'Series A': ownership_series_a / 100.0,
            'Series B': default_config.get('initial_ownership_targets', {}).get('Series B', 0.15),
            'Series C': default_config.get('initial_ownership_targets', {}).get('Series C', 0.15)
        }
        
        # Update Capital Calls Configuration
        base_config['capital_calls'] = {
            'minimum_cash_balance_pct': minimum_cash_balance_pct / 100.0,
            'tranche_size_pct': tranche_size_pct / 100.0
        }
        
        # Update Management Fees Configuration
        base_config['mgmt_fee_commitment_period_rate'] = mgmt_fee_commitment / 100
        base_config['mgmt_fee_extension_period_rate'] = mgmt_fee_extension / 100
        base_config['mgmt_fee_post_commitment_period_rate'] = mgmt_fee_post_commitment / 100
        
        # Update Dynamic Stage Allocation
        base_config['dynamic_stage_allocation'] = []
        for year_data in stage_allocation_data:
            base_config['dynamic_stage_allocation'].append({
                'year': year_data['year'],
                'allocation': {
                    'Pre-Seed': year_data['Pre-Seed'],
                    'Seed': year_data['Seed'],
                    'Series A': year_data['Series A']
                }
            })
        
        # Update Stages Configuration
        base_config['stages'] = stages_config
        
        # Create scenario
        scenario = ScenarioManager.create_scenario(scenario_name, base_config)
        
        # Add to session state
        st.session_state.scenarios[scenario_name] = scenario
        st.session_state.current_scenario_name = scenario_name
        
        # Close the create form and clear scenario name
        st.session_state.show_create_form = False
        if 'advanced_config_scenario_name' in st.session_state:
            del st.session_state.advanced_config_scenario_name
        
        st.success(f"✅ Scenario '{scenario_name}' created successfully!")
        st.info("💡 Go to the 'Run & Analyze' tab to execute the simulation.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating scenario: {str(e)}")

def create_scenario_from_file_config(scenario_name, config_dict):
    """Create scenario from uploaded file configuration"""
    
    # Check user permissions
    user_permissions = check_user_permissions(st.session_state.username)
    if 'create' not in user_permissions:
        st.error("❌ Access denied: You don't have permission to create scenarios.")
        return
    
    try:
        # Validate the configuration
        if not validate_config(config_dict):
            st.error("❌ Invalid configuration. Please check your file parameters.")
            return
        
        # Create scenario
        scenario = ScenarioManager.create_scenario(scenario_name, config_dict)
        
        # Add to session state
        st.session_state.scenarios[scenario_name] = scenario
        st.session_state.current_scenario_name = scenario_name
        
        # Close the create form and clear scenario name
        st.session_state.show_create_form = False
        if 'file_config_scenario_name' in st.session_state:
            del st.session_state.file_config_scenario_name
        
        st.success(f"✅ Scenario '{scenario_name}' created successfully!")
        st.info("💡 Go to the 'Run & Analyze' tab to execute the simulation.")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating scenario: {str(e)}")

def validate_config(config_dict):
    """Basic validation of configuration dictionary"""
    required_fields = ['committed_capital', 'num_investments', 'mgmt_fee_commitment_period_rate']
    
    for field in required_fields:
        if field not in config_dict:
            st.error(f"❌ Missing required field: {field}")
            return False
    
    # Check waterfall parameters
    if 'waterfall' not in config_dict:
        st.error("❌ Missing required section: waterfall")
        return False
    
    waterfall_params = config_dict['waterfall']
    required_waterfall_params = ['carried_interest_pct', 'preferred_return_pct']
    
    for param in required_waterfall_params:
        if param not in waterfall_params:
            st.error(f"❌ Missing required waterfall parameter: {param}")
            return False
    
    return True

def render_scenario_management():
    """Render scenario management interface"""
    st.markdown("---")
    st.subheader("📊 Scenario Management")
    
    if not st.session_state.scenarios:
        st.info("No scenarios created yet. Use the configuration options above to create your first scenario.")
        return
    
    # Display existing scenarios
    scenario_names = list(st.session_state.scenarios.keys())
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_scenario = st.selectbox(
            "Select Scenario",
            options=scenario_names,
            help="Choose a scenario to view or manage"
        )
    
    with col2:
        if st.button("📋 View Config", use_container_width=True):
            view_scenario_config(selected_scenario)
    
    with col3:
        # Check user permissions for scenario deletion
        user_permissions = check_user_permissions(st.session_state.username)
        
        if 'delete' in user_permissions:
            if st.button("🗑️ Delete", use_container_width=True):
                delete_scenario(selected_scenario)
        else:
            st.button("🗑️ Delete", use_container_width=True, disabled=True, 
                     help="You don't have permission to delete scenarios")
    
    # Display scenario summary
    if selected_scenario:
        display_scenario_summary(selected_scenario)

def view_scenario_config(scenario_name):
    """Display scenario configuration in a modal-like format"""
    scenario = st.session_state.scenarios[scenario_name]
    
    st.markdown(f"#### Configuration: {scenario_name}")
    
    # Display config as formatted YAML
    config_yaml = yaml.dump(scenario['config'], default_flow_style=False, sort_keys=False)
    st.code(config_yaml, language='yaml')

def delete_scenario(scenario_name):
    """Delete a scenario from session state"""
    
    # Check user permissions
    user_permissions = check_user_permissions(st.session_state.username)
    if 'delete' not in user_permissions:
        st.error("❌ Access denied: You don't have permission to delete scenarios.")
        return
    
    if scenario_name in st.session_state.scenarios:
        del st.session_state.scenarios[scenario_name]
        
        # Update current scenario if it was deleted
        if st.session_state.current_scenario_name == scenario_name:
            remaining_scenarios = list(st.session_state.scenarios.keys())
            st.session_state.current_scenario_name = remaining_scenarios[0] if remaining_scenarios else None
        
        st.success(f"✅ Scenario '{scenario_name}' deleted successfully!")
        st.rerun()

def display_scenario_summary(scenario_name):
    """Display a summary of the selected scenario"""
    scenario = st.session_state.scenarios[scenario_name]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Created", scenario['timestamp'].strftime('%Y-%m-%d %H:%M'))
    
    with col2:
        has_results = "✅ Yes" if scenario['results'] is not None else "❌ No"
        st.metric("Has Results", has_results)
    
    with col3:
        fund_size = scenario['config']['committed_capital'] / 1_000_000
        st.metric("Fund Size", f"${fund_size:.0f}M")
    
    # Show key parameters
    with st.expander("📋 Key Parameters", expanded=False):
        config = scenario['config']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Fund Structure:**")
            st.write(f"- Fund Size: ${config['committed_capital']/1_000_000:.0f}M")
            st.write(f"- Portfolio Size: {config['num_investments']}")
            st.write(f"- Management Fee: {config['mgmt_fee_commitment_period_rate']*100:.1f}%")
            st.write(f"- Carried Interest: {config['waterfall']['carried_interest_pct']*100:.1f}%")
        
        with col2:
            st.markdown("**Investment Strategy:**")
            avg_inv = config.get('average_investment_size', 0)
            st.write(f"- Avg Investment: ${avg_inv/1_000_000:.1f}M" if avg_inv > 0 else "- Avg Investment: N/A")
            follow_on = config.get('follow_on_investment_rate', 0)
            st.write(f"- Follow-on Rate: {follow_on*100:.0f}%" if follow_on > 0 else "- Follow-on Rate: N/A")
            st.write(f"- Preferred Return: {config['waterfall']['preferred_return_pct']*100:.1f}%")
            fund_life = config.get('fund_lifespan_months', 0)
            st.write(f"- Fund Life: {fund_life/12:.0f} years" if fund_life > 0 else "- Fund Life: N/A")

def render_import_scenario():
    """Render import scenario interface"""
    st.subheader("Import Scenario")
    
    st.markdown("""
    Import a previously exported scenario package. This will load the scenario configuration, 
    results, and all associated data into your current session.
    """)
    
    # File upload for scenario import
    uploaded_file = st.file_uploader(
        "Upload scenario package (.zip)",
        type=['zip'],
        help="Select a .zip file containing a previously exported scenario",
        key="import_scenario_uploader"
    )
    
    if uploaded_file is not None:
        st.info(f"Selected file: {uploaded_file.name}")
        
        # Show file details
        file_size = len(uploaded_file.getvalue())
        st.write(f"File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # Import button
        if st.button("Import Scenario", type="primary", use_container_width=True):
            import_scenario_from_upload(uploaded_file)

def import_scenario_from_upload(uploaded_file):
    """Import scenario from uploaded ZIP file"""
    import zipfile
    import tempfile
    from scenario_manager import ScenarioManager
    
    try:
        with st.spinner("Importing scenario..."):
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Save uploaded file
                zip_path = temp_path / "upload.zip"
                with open(zip_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                # Extract ZIP
                extract_path = temp_path / "extracted"
                extract_path.mkdir()
                
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                
                # Import scenario
                scenario = ScenarioManager.import_scenario(extract_path)
                
                # Check if scenario name already exists
                if scenario['name'] in st.session_state.scenarios:
                    st.warning(f"A scenario named '{scenario['name']}' already exists.")
                    
                    # Offer to rename
                    new_name = st.text_input(
                        "Enter a new name for the imported scenario:",
                        value=f"{scenario['name']} (Imported)",
                        key="import_rename_input"
                    )
                    
                    if st.button("Import with New Name", use_container_width=True):
                        scenario['name'] = new_name
                        st.session_state.scenarios[scenario['name']] = scenario
                        st.success(f"Scenario '{scenario['name']}' imported successfully!")
                        st.session_state.show_create_form = False
                        st.rerun()
                else:
                    # Add to session state
                    st.session_state.scenarios[scenario['name']] = scenario
                    st.success(f"Scenario '{scenario['name']}' imported successfully!")
                    st.session_state.show_create_form = False
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error importing scenario: {str(e)}")
        st.write("Please ensure the uploaded file is a valid scenario package (.zip file).")