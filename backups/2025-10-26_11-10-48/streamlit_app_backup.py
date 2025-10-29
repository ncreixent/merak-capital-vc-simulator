# streamlit_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml
import pickle
import json
from datetime import datetime
from pathlib import Path
import sys

# Increase pandas styler limit to handle large datasets
pd.set_option("styler.render.max_elements", 1000000)

# Import your existing modules
from parameters_loader import load_parameters
from engine import run_monte_carlo, convert_multiple_simulations_to_excel_with_flows
from parameters import FundParameters
from scenario_manager import ScenarioManager

# Page configuration
st.set_page_config(
    page_title="VC Fund Monte Carlo Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        padding: 0.5rem 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables"""
    if 'scenarios' not in st.session_state:
        st.session_state.scenarios = {}
    
    if 'current_scenario_name' not in st.session_state:
        st.session_state.current_scenario_name = None
    
    if 'default_loaded' not in st.session_state:
        st.session_state.default_loaded = False
    
    if 'config_dict' not in st.session_state:
        st.session_state.config_dict = None

# Load default scenario on startup
def load_default_scenario():
    """Load pre-computed default scenario results"""
    try:
        # Try to load pre-computed results
        default_path = Path("default_scenario")
        
        if default_path.exists():
            with open(default_path / "results.pkl", "rb") as f:
                results = pickle.load(f)
            
            with open(default_path / "config.yaml", "r", encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            # Load pre-generated Excel file
            excel_path = default_path / "results.xlsx"
            excel_buffer = None
            if excel_path.exists():
                with open(excel_path, 'rb') as f:
                    excel_buffer = f.read()
            
            return {
                'name': 'Base Case - Institutional Realism',
                'timestamp': datetime.now(),
                'config': config_dict,
                'results': results['all_results'],
                'gross_flows': results['all_gross_flows'],
                'waterfall_log': results['waterfall_log'],
                'net_lp_flows': results['net_lp_flows_log'],
                'params': None,  # Don't load params here to avoid issues
                'cached_metrics': None,  # Will be calculated on first use
                'excel_buffer': excel_buffer  # Pre-generated Excel file
            }
        else:
            # If no pre-computed results, show warning but don't compute
            st.warning("No pre-computed default scenario found. Please run 'python precompute_default.py' first.")
            return None
    
    except Exception as e:
        st.error(f"Error loading default scenario: {str(e)}")
        return None

# Scenario Manager Functions moved to scenario_manager.py

# Continue in next message due to length...

# Complete streamlit_app.py (continuation)

def main():
    """Main application entry point"""
    
    # Initialize session state
    init_session_state()
    
    # Load default scenario on first run
    if not st.session_state.default_loaded:
        with st.spinner("Loading default scenario..."):
            default_scenario = load_default_scenario()
            if default_scenario:
                st.session_state.scenarios[default_scenario['name']] = default_scenario
                st.session_state.current_scenario_name = default_scenario['name']
                st.session_state.default_loaded = True
                st.success(f"✅ Default scenario '{default_scenario['name']}' loaded successfully!")
            else:
                st.warning("⚠️ Could not load default scenario. Please check if precompute_default.py has been run.")
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=VC+Fund+Model", use_container_width=True)
        
        st.markdown("## 💼 VC Fund Monte Carlo Simulator")
        st.markdown("---")
        
        # Scenario count
        st.metric("Active Scenarios", len(st.session_state.scenarios))
        
        scenarios_with_results = sum(
            1 for s in st.session_state.scenarios.values() 
            if s['results'] is not None
        )
        st.metric("Completed Simulations", scenarios_with_results)
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("📥 Reload Default", use_container_width=True):
            default_scenario = load_default_scenario()
            if default_scenario:
                st.session_state.scenarios[default_scenario['name']] = default_scenario
                st.success("Default scenario reloaded!")
                st.rerun()
        
        if st.button("🗑️ Clear All Scenarios", use_container_width=True):
            if st.session_state.scenarios:
                st.session_state.scenarios = {}
                st.session_state.current_scenario_name = None
                st.success("All scenarios cleared!")
                st.rerun()
        
        st.markdown("---")
        
        # Help section
        with st.expander("ℹ️ Help & Documentation"):
            st.markdown("""
            ### How to Use
            
            1. **Setup Tab**: Configure your fund parameters
            2. **Run Tab**: Execute Monte Carlo simulation
            3. **Compare Tab**: Analyze multiple scenarios
            
            ### Key Features
            - Monte Carlo simulation with 100-10,000 runs
            - Basic and Advanced configuration modes
            - Comprehensive performance metrics
            - Waterfall distribution analysis
            - Scenario comparison and export
            
            ### Support
            For questions or issues, please refer to the documentation.
            """)
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Scenario Management",
        "🚀 Run & Analyze",
        "⚖️ Compare"
    ])
    
    with tab1:
        from setup_tab import render_setup_tab
        render_setup_tab()
    
    with tab2:
        from run_tab import render_run_tab
        render_run_tab()
    
    with tab3:
        from compare_tab import render_compare_tab
        render_compare_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>VC Fund Monte Carlo Simulator | Built with Streamlit</p>
            <p style='font-size: 0.8rem;'>⚠️ For educational and analytical purposes only. Not investment advice.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()