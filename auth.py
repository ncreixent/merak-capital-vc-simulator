import os
import streamlit as st
import hashlib
import base64
from typing import Dict, Any

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def load_production_credentials():
    """Load credentials from environment variables"""
    users = {}
    
    # Load admin credentials
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD')
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@merakcapital.com')
    admin_name = os.getenv('ADMIN_NAME', 'Admin User')
    
    if admin_password:
        users[admin_username] = {
            'email': admin_email,
            'name': admin_name,
            'password': hash_password(admin_password),
            'role': 'admin'
        }
    
    # Load user credentials
    user_username = os.getenv('USER_USERNAME', 'user')
    user_password = os.getenv('USER_PASSWORD')
    user_email = os.getenv('USER_EMAIL', 'user@merakcapital.com')
    user_name = os.getenv('USER_NAME', 'Investment Analyst')
    
    if user_password:
        users[user_username] = {
            'email': user_email,
            'name': user_name,
            'password': hash_password(user_password),
            'role': 'user'
        }
    
    return {'users': users}

def load_development_credentials():
    """Load default development credentials"""
    return {
        'users': {
            'admin': {
                'email': 'admin@merakcapital.com',
                'name': 'Admin User',
                'password': hash_password('admin123'),
                'role': 'admin'
            },
            'user': {
                'email': 'user@merakcapital.com', 
                'name': 'Investment Analyst',
                'password': hash_password('user123'),
                'role': 'user'
            }
        }
    }

def setup_authentication():
    """Setup authentication for the app"""
    # Check if we have cached auth config
    if 'auth_config_cache' in st.session_state:
        return st.session_state.auth_config_cache
    
    # Import here to avoid circular imports
    from user_management import get_all_users
    
    # Get all users (environment + file-based)
    all_users = get_all_users()
    
    # Check if we're in production (environment variables set)
    is_production = any([
        os.getenv('ADMIN_PASSWORD'),
        os.getenv('USER_PASSWORD')
    ])
    
    if is_production or all_users:
        # Use all available users
        auth_config = {'users': all_users}
    else:
        # Fall back to development credentials
        auth_config = load_development_credentials()
    
    # Cache the auth config
    st.session_state.auth_config_cache = auth_config
    return auth_config

def render_login_page(auth_config):
    """Render the login page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1 style="color: #0A1A1E; font-family: 'Inter', sans-serif;">Merak Capital</h1>
        <h2 style="color: #268BA0; font-family: 'Inter', sans-serif;">Investment Analysis Platform</h2>
        <p style="color: #6b7280; margin-top: 1rem;">Please log in to access the platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Manual login form
    st.markdown("### Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    # Initialize return values
    name = None
    authentication_status = None
    user_role = None
    
    if st.button("Login", type="primary"):
        if username in auth_config['users']:
            user_data = auth_config['users'][username]
            if verify_password(password, user_data['password']):
                name = user_data['name']
                authentication_status = True
                user_role = user_data['role']
                st.success(f"Welcome, {name}!")
            else:
                authentication_status = False
                st.error("Invalid password")
        else:
            authentication_status = False
            st.error("Invalid username")
    
    # Forgot password section
    st.markdown("---")
    st.markdown("### Forgot Password?")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        reset_email = st.text_input("Enter your email address", key="forgot_password_email")
    with col2:
        if st.button("Send Reset Link", key="forgot_password_btn"):
            if reset_email:
                # Import here to avoid circular imports
                from user_management import reset_password_by_email
                success, message = reset_password_by_email(reset_email)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("Please enter an email address")
    
    # Show demo credentials only in development
    is_production = any([
        os.getenv('ADMIN_PASSWORD'),
        os.getenv('USER_PASSWORD')
    ])
    
    if not is_production:
        with st.expander("Demo Credentials", expanded=False):
            st.markdown("""
            **Demo Accounts:**
            - **Admin**: `admin` / `admin123` (Full access - create scenarios, run simulations, manage system)
            - **User**: `user` / `user123` (Standard access - run simulations, view results)
            """)
    
    return name, authentication_status, username, user_role

def render_logout_section(name):
    """Render logout section in sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**Welcome, {name}**")
        if st.button("Logout", type="secondary"):
            # Clear session state
            st.session_state.authentication_status = None
            st.session_state.name = None
            st.session_state.username = None
            st.session_state.user_role = None
            st.rerun()

def check_user_permissions(username):
    """Check user permissions based on role"""
    # Get user role from session state or auth config
    user_role = st.session_state.get('user_role')
    
    if not user_role:
        # Fallback: try to get role from auth config
        try:
            from user_management import get_all_users
            all_users = get_all_users()
            if username in all_users:
                user_role = all_users[username]['role']
            else:
                return ['read']  # Default permissions
        except:
            return ['read']  # Default permissions
    
    permissions = {
        'admin': ['create', 'read', 'update', 'delete', 'run_simulations', 'view_all'],
        'user': ['read', 'run_simulations', 'view_all']
    }
    return permissions.get(user_role, ['read'])

def require_permission(required_permission):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'username' in st.session_state and st.session_state.username:
                user_permissions = check_user_permissions(st.session_state.username)
                if required_permission in user_permissions:
                    return func(*args, **kwargs)
                else:
                    st.error(f"❌ Access denied. You need '{required_permission}' permission.")
                    return None
            else:
                st.error("❌ Please log in to access this feature.")
                return None
        return wrapper
    return decorator