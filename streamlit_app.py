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

# Import authentication
from auth import setup_authentication, render_login_page, render_logout_section, check_user_permissions, require_permission

# Page configuration
st.set_page_config(
    page_title="VC Fund Monte Carlo Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Merak Capital Institutional Grade Styling
st.markdown("""
    <style>
    /* Import Merak Capital Brand Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Theme - Merak Capital Color Palette */
    .stApp {
        background-color: #ffffff; /* white */
        color: #0A1A1E; /* rich-black */
    }
    
    /* Main content area - ensure white background */
    .main .block-container {
        background-color: #ffffff;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Tab content background */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
    }
    
    /* Main Headers - Reduced size, professional styling */
    .main-header {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: #0A1A1E; /* rich-black */
        margin-bottom: 1.5rem;
        letter-spacing: -0.02em;
    }
    
    /* Subheaders - Professional hierarchy */
    .stSubheader {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 1.2rem;
        font-weight: 500;
        color: #0A1A1E; /* rich-black */
        margin-bottom: 1rem;
    }
    
    /* Metric Cards - Merak Capital theme */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #AFB9BD; /* silver */
        padding: 1.5rem;
        border-radius: 8px;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(10, 26, 30, 0.1);
    }
    
    /* Ensure all metric containers are white */
    .stMetric {
        background-color: #ffffff;
    }
    
    /* Ensure all expanders have white background */
    .streamlit-expander {
        background-color: #ffffff;
    }
    
    /* Ensure all columns have white background */
    .stColumn {
        background-color: #ffffff;
    }
    
    /* Enhanced Tab Styling - Merak Capital theme */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: #ffffff;
        border-bottom: 2px solid #AFB9BD; /* silver */
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 1rem;
        font-weight: 500;
        padding: 1rem 2rem;
        color: #AFB9BD; /* silver */
        background-color: #ffffff;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #024761; /* indigo-dye */
        background-color: #F3F3F3; /* white-smoke */
    }
    
    .stTabs [aria-selected="true"] {
        color: #0A1A1E; /* rich-black */
        background-color: #ffffff;
        border-bottom: 2px solid #268BA0; /* blue-munsell */
    }
    
    /* Sidebar Styling - Merak Capital Brand */
    .css-1d391kg {
        background-color: #0A1A1E; /* rich-black */
        border-right: 1px solid #024761; /* indigo-dye */
    }
    
    .css-1d391kg .stMarkdown {
        color: #F3F3F3; /* white-smoke */
    }
    
    /* Input Fields - Merak Capital theme */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background-color: #ffffff;
        border: 1px solid #AFB9BD; /* silver */
        color: #0A1A1E; /* rich-black */
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #268BA0; /* blue-munsell */
        box-shadow: 0 0 0 1px #268BA0; /* blue-munsell */
    }
    
    /* Buttons - Dark grey styling */
    .stButton > button {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 500;
        border-radius: 6px;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background-color: #374151; /* dark grey */
        color: #ffffff;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #4b5563; /* darker grey */
        transform: translateY(-1px);
    }
    
    .stButton > button[kind="secondary"] {
        background-color: #374151; /* dark grey */
        color: #ffffff;
        border: 1px solid #374151; /* dark grey */
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #4b5563; /* darker grey */
        border-color: #4b5563; /* darker grey */
    }
    
    /* Default button styling (no kind specified) */
    .stButton > button:not([kind]):not([type]) {
        background-color: #374151; /* dark grey */
        color: #ffffff;
        border: 1px solid #374151; /* dark grey */
    }
    
    .stButton > button:not([kind]):not([type]):hover {
        background-color: #4b5563; /* darker grey */
        border-color: #4b5563; /* darker grey */
    }
    
    /* Data Tables - Merak Capital theme */
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #AFB9BD; /* silver */
    }
    
    /* Remove emoji/icon clutter */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Plotly chart styling */
    .js-plotly-plot {
        background-color: transparent !important;
    }
    
    /* Custom widget containers */
    .widget-container {
        background-color: #ffffff;
        border: 1px solid #AFB9BD; /* silver */
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(10, 26, 30, 0.1);
    }
    
    /* Merak Capital Logo Styling */
    .merak-logo {
        text-align: center;
        padding: 1.5rem 0;
        border-bottom: 1px solid #024761; /* indigo-dye */
        margin-bottom: 1rem;
    }
    
    .merak-logo img {
        max-width: 200px;
        height: auto;
        margin-bottom: 1rem;
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

def render_password_reset_page(reset_token):
    """Render password reset page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1 style="color: #0A1A1E; font-family: 'Inter', sans-serif;">Merak Capital</h1>
        <h2 style="color: #268BA0; font-family: 'Inter', sans-serif;">Password Reset</h2>
        <p style="color: #6b7280; margin-top: 1rem;">Enter your new password below</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Import here to avoid circular imports
    from user_management import reset_password_with_token, validate_reset_token
    
    # Validate token first
    username = validate_reset_token(reset_token)
    
    if not username:
        st.error("❌ Invalid or expired reset token. Please request a new password reset.")
        st.markdown("---")
        if st.button("← Back to Login", type="secondary"):
            # Clear the reset token from URL and clear auth cache
            if 'auth_config_cache' in st.session_state:
                del st.session_state.auth_config_cache
            # Set flag to skip reset token processing
            st.session_state.skip_reset_token = True
            st.rerun()
        return
    
    st.success(f"✅ Valid reset token for user: **{username}**")
    
    # Debug toggle (remove in production)
    if st.checkbox("Debug Mode", key="debug_toggle"):
        st.session_state.debug_mode = True
    else:
        st.session_state.debug_mode = False
    
    # Password reset form
    with st.form("password_reset_form", clear_on_submit=True):
        st.markdown("### Set New Password")
        
        new_password = st.text_input("New Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_password")
        
        submitted = st.form_submit_button("Reset Password", type="primary")
        
        if submitted:
            if not new_password:
                st.error("Please enter a new password")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                success, message = reset_password_with_token(reset_token, new_password)
                if success:
                    st.success("🎉 Password reset successfully!")
                    st.info("You can now log in with your new password.")
                    # Clear the token from URL immediately after successful reset
                    st.session_state.skip_reset_token = True
                    st.session_state.password_reset_success = True
                    # Force clear URL parameters
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    # Add navigation button outside the form (only show if password reset failed)
    if not st.session_state.get('password_reset_success', False):
        st.markdown("---")
        if st.button("← Go to Login", type="primary"):
            # Clear the reset token from URL and clear auth cache
            if 'auth_config_cache' in st.session_state:
                del st.session_state.auth_config_cache
            # Set flag to skip reset token processing
            st.session_state.skip_reset_token = True
            # Debug output
            st.write("🔧 DEBUG: Button clicked! Setting skip_reset_token = True")
            st.rerun()

def main():
    """Main application entry point"""
    
    # Setup authentication
    auth_config = setup_authentication()
    
    # Check if we need to clear reset token first
    if st.session_state.get('clear_reset_token', False):
        st.session_state.clear_reset_token = False
        # Clear any remaining query params
        st.query_params.clear()
        st.rerun()
    
    # Check for password reset token in URL
    # Only process reset token if we haven't successfully completed a password reset
    if ('reset_token' in st.query_params and 
        not st.session_state.get('skip_reset_token', False) and 
        not st.session_state.get('password_reset_success', False)):
        reset_token = st.query_params['reset_token']
        render_password_reset_page(reset_token)
        return
    
    # Only reset the skip flag if we're not in a password reset context
    # This prevents the token from being processed again during login
    if st.session_state.get('skip_reset_token', False) and not st.session_state.get('password_reset_success', False):
        # Keep the skip flag active for a few more reruns to ensure clean login
        pass  # Don't reset the flag yet
    
    # Debug information (remove in production)
    if st.session_state.get('debug_mode', False):
        st.sidebar.write("Debug Info:")
        st.sidebar.write(f"Reset token in URL: {'reset_token' in st.query_params}")
        st.sidebar.write(f"Skip reset token: {st.session_state.get('skip_reset_token', False)}")
        st.sidebar.write(f"Query params: {dict(st.query_params)}")
    
    # Check authentication status
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    # Render login page if not authenticated
    if not st.session_state.authentication_status:
        name, authentication_status, username, user_role = render_login_page(auth_config)
        st.session_state.authentication_status = authentication_status
        st.session_state.name = name
        st.session_state.username = username
        st.session_state.user_role = user_role
        
        if authentication_status:
            st.rerun()
        else:
            return
    
    # User is authenticated, render main app
    if st.session_state.authentication_status:
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
                    # Default scenario loaded silently
                else:
                    st.warning("⚠️ Could not load default scenario. Please check if precompute_default.py has been run.")
        
        # Sidebar - Merak Capital Branding with Authentication
        with st.sidebar:
            # Merak Capital Logo
            st.markdown("""
            <div class="merak-logo">
                <img src="https://i0.wp.com/merak.capital/wp-content/uploads/2022/11/Merak_logo_WEB.png?w=1620&ssl=1" 
                     alt="Merak Capital" 
                     style="max-width: 200px; height: auto; margin-bottom: 1rem;">
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("## VC Fund Monte Carlo Simulator")
            st.markdown("---")
            
            # User info and logout
            render_logout_section(st.session_state.name)
            
            # User role and permissions
            user_permissions = check_user_permissions(st.session_state.username)
            st.markdown(f"**Role:** {st.session_state.user_role.title()}")
            st.markdown(f"**Permissions:** {', '.join(user_permissions)}")
            
            st.markdown("---")
            
            # Scenario count
            st.metric("Active Scenarios", len(st.session_state.scenarios))
            
            scenarios_with_results = sum(
                1 for s in st.session_state.scenarios.values() 
                if s['results'] is not None
            )
            st.metric("Completed Simulations", scenarios_with_results)
            
            st.markdown("---")
            
            # Quick actions based on permissions
            st.markdown("### Quick Actions")
            
            if 'create' in user_permissions:
                if st.button("Reload Default", use_container_width=True):
                    default_scenario = load_default_scenario()
                    if default_scenario:
                        st.session_state.scenarios[default_scenario['name']] = default_scenario
                        st.success("Default scenario reloaded!")
                        st.rerun()
                
                if st.button("Clear All Scenarios", use_container_width=True):
                    if st.session_state.scenarios:
                        st.session_state.scenarios = {}
                        st.session_state.current_scenario_name = None
                        st.success("All scenarios cleared!")
                        st.rerun()
            else:
                st.info("Limited permissions - contact admin for scenario management")
            
            # User management for admins
            if st.session_state.user_role == 'admin':
                st.markdown("---")
                st.markdown("### 👥 User Management")
                
                if st.button("Manage Users", use_container_width=True):
                    st.session_state.show_user_management = True
                    st.rerun()
            
            st.markdown("---")
            
            # Help section
            with st.expander("Help & Documentation"):
                st.markdown("""
                ### How to Use
                
                1. **Scenario Management**: Configure your fund parameters
                2. **Run & Analyze**: Execute Monte Carlo simulation
                3. **Compare**: Analyze multiple scenarios
                
                ### Key Features
                - Monte Carlo simulation with 100-10,000 runs
                - Basic and Advanced configuration modes
                - Comprehensive performance metrics
                - Waterfall distribution analysis
                - Scenario comparison and export
                
                ### Support
                For questions or issues, please refer to the documentation.
                """)
        
        # Check if user management is requested
        if st.session_state.get('show_user_management', False):
            from user_management import render_user_management
            
            st.markdown("<h1 class='main-header'>User Management</h1>", unsafe_allow_html=True)
            
            # Back button
            if st.button("← Back to Main App", type="secondary"):
                st.session_state.show_user_management = False
                st.rerun()
            
            st.markdown("---")
            
            render_user_management()
        else:
            # Main content area with tabs
            tab1, tab2, tab3 = st.tabs([
                "Scenario Management",
                "Run & Analyze",
                "Compare"
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
            <div style='text-align: center; color: #999999; padding: 1rem; font-family: Inter, sans-serif;'>
                <p>VC Fund Monte Carlo Simulator | Built with Streamlit</p>
                <p style='font-size: 0.8rem;'>For educational and analytical purposes only. Not investment advice.</p>
            </div>
    """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()