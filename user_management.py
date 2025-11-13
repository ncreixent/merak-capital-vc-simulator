# user_management.py

import streamlit as st
import pandas as pd
import hashlib
import json
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from auth import hash_password, verify_password, check_user_permissions

def load_users_from_file():
    """Load users from JSON file or session state"""
    # First, try to load from session state (for Streamlit Cloud compatibility)
    if 'persistent_users' in st.session_state:
        return st.session_state.persistent_users.copy()
    
    # Fallback: try to load from file (works in local dev)
    users_file = 'users.json'
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
                # Validate and fix password hashing
                users = validate_and_fix_passwords(users)
                # Store in session state for future access
                st.session_state.persistent_users = users
                return users
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # Initialize empty dict in session state if nothing exists
    if 'persistent_users' not in st.session_state:
        st.session_state.persistent_users = {}
    
    return {}

def validate_and_fix_passwords(users):
    """Validate that all passwords are properly hashed and fix if needed"""
    fixed_users = {}
    for username, user_info in users.items():
        user_info_copy = user_info.copy()
        
        # Check if password looks like plain text (not a hash)
        password = user_info.get('password', '')
        if password and len(password) < 64:  # SHA-256 hashes are 64 characters
            # This looks like plain text, hash it
            user_info_copy['password'] = hash_password(password)
            st.warning(f"⚠️ Password for user '{username}' was stored as plain text. It has been automatically hashed.")
        
        fixed_users[username] = user_info_copy
    
    # Save the fixed users back to file if any were changed
    if fixed_users != users:
        save_users_to_file(fixed_users)
    
    return fixed_users

def save_users_to_file(users):
    """Save users to session state and optionally to JSON file"""
    # Always save to session state (works in Streamlit Cloud)
    st.session_state.persistent_users = users.copy()
    
    # Try to save to file (works in local dev, may fail in Streamlit Cloud)
    users_file = 'users.json'
    try:
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except (IOError, OSError, PermissionError) as e:
        # File write failed (likely in Streamlit Cloud) - that's OK, we have session state
        # Don't show error for read-only filesystem
        return True  # Return True because session state save succeeded
    except Exception as e:
        # Other errors - show warning but still return True since session state works
        st.warning(f"Could not save to file, but users saved to session: {str(e)}")
        return True

def add_user(username, password, email, name, role):
    """Add a new user to the system"""
    users = load_users_from_file()
    
    if username in users:
        return False, f"Username '{username}' already exists"
    
    # Validate role
    valid_roles = ['admin', 'user']
    if role not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    # Add user
    users[username] = {
        'email': email,
        'name': name,
        'password': hash_password(password),
        'role': role,
        'created_at': datetime.now().isoformat(),
        'created_by': st.session_state.username
    }
    
    if save_users_to_file(users):
        # Clear authentication cache to force refresh
        if 'auth_config_cache' in st.session_state:
            del st.session_state.auth_config_cache
        return True, f"User '{username}' added successfully"
    else:
        return False, "Failed to save user data"

def remove_user(username):
    """Remove a user from the system"""
    # Check if this is an environment-based user (cannot be deleted)
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    user_username = os.getenv('USER_USERNAME', 'user')
    admin_password = os.getenv('ADMIN_PASSWORD')
    user_password = os.getenv('USER_PASSWORD')
    
    if (admin_password and username == admin_username) or (user_password and username == user_username):
        return False, f"User '{username}' is configured via environment variables and cannot be deleted"
    
    users = load_users_from_file()
    
    if username not in users:
        return False, f"User '{username}' not found"
    
    # Prevent admin from deleting themselves
    if username == st.session_state.username:
        return False, "You cannot delete your own account"
    
    # Prevent deleting the last admin (check all users including environment)
    all_users = get_all_users()
    admin_count = sum(1 for user in all_users.values() if user['role'] == 'admin')
    if users[username]['role'] == 'admin' and admin_count <= 1:
        return False, "Cannot delete the last admin user"
    
    del users[username]
    
    if save_users_to_file(users):
        # Clear authentication cache to force refresh
        if 'auth_config_cache' in st.session_state:
            del st.session_state.auth_config_cache
        return True, f"User '{username}' removed successfully"
    else:
        return False, "Failed to save user data"

def update_user_role(username, new_role):
    """Update a user's role"""
    users = load_users_from_file()
    
    if username not in users:
        return False, f"User '{username}' not found"
    
    # Validate role
    valid_roles = ['admin', 'user']
    if new_role not in valid_roles:
        return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    # Prevent admin from demoting themselves
    if username == st.session_state.username and users[username]['role'] == 'admin' and new_role != 'admin':
        return False, "You cannot change your own role"
    
    # Prevent demoting the last admin
    admin_count = sum(1 for user in users.values() if user['role'] == 'admin')
    if users[username]['role'] == 'admin' and new_role != 'admin' and admin_count <= 1:
        return False, "Cannot demote the last admin user"
    
    users[username]['role'] = new_role
    users[username]['updated_at'] = datetime.now().isoformat()
    users[username]['updated_by'] = st.session_state.username
    
    if save_users_to_file(users):
        # Clear authentication cache to force refresh
        if 'auth_config_cache' in st.session_state:
            del st.session_state.auth_config_cache
        return True, f"User '{username}' role updated to {new_role}"
    else:
        return False, "Failed to save user data"

def change_user_password(username, new_password):
    """Change a user's password"""
    users = load_users_from_file()
    
    if username not in users:
        return False, f"User '{username}' not found"
    
    users[username]['password'] = hash_password(new_password)
    users[username]['password_changed_at'] = datetime.now().isoformat()
    users[username]['password_changed_by'] = st.session_state.username
    
    if save_users_to_file(users):
        # Clear authentication cache to force refresh
        if 'auth_config_cache' in st.session_state:
            del st.session_state.auth_config_cache
        return True, f"Password updated for user '{username}'"
    else:
        return False, "Failed to save user data"

def render_user_management():
    """Render the user management interface"""
    st.markdown("### 👥 User Management")
    
    # Check if user has admin role
    if st.session_state.user_role != 'admin':
        st.error("❌ Access denied: Only administrators can manage users.")
        return
    
    # Refresh authentication data button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", help="Refresh user data from file"):
            if 'auth_config_cache' in st.session_state:
                del st.session_state.auth_config_cache
            st.success("Authentication data refreshed!")
            st.rerun()
    
    # Load current users
    users = load_users_from_file()
    
    # Debug information
    with st.expander("🔍 Debug Information", expanded=False):
        st.write("**Current Session State:**")
        st.write(f"- Username: {st.session_state.get('username', 'None')}")
        st.write(f"- User Role: {st.session_state.get('user_role', 'None')}")
        st.write(f"- Auth Cache Exists: {'auth_config_cache' in st.session_state}")
        
        st.write("**All Available Users:**")
        all_users = get_all_users()
        for username, user_info in all_users.items():
            st.write(f"- {username}: {user_info['role']} ({user_info.get('source', 'unknown')})")
    
    # Display current users
    st.markdown("#### Current Users")
    
    if not users:
        st.info("No users found. Default users are loaded from environment variables.")
    else:
        # Create a DataFrame for better display
        user_data = []
        for username, user_info in users.items():
            user_data.append({
                'Username': username,
                'Name': user_info['name'],
                'Email': user_info['email'],
                'Role': user_info['role'].title(),
                'Created': user_info.get('created_at', 'Unknown')[:10] if user_info.get('created_at') else 'Unknown'
            })
        
        if user_data:
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Add new user form
    st.markdown("#### Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username", help="Unique username for login")
            new_email = st.text_input("Email", help="User's email address")
            new_name = st.text_input("Full Name", help="User's display name")
        
        with col2:
            new_password = st.text_input("Password", type="password", help="Initial password")
            new_role = st.selectbox("Role", ["user", "admin"], help="User permissions level")
        
        submitted = st.form_submit_button("Add User", type="primary")
        
        if submitted:
            if not all([new_username, new_password, new_email, new_name]):
                st.error("Please fill in all fields")
            else:
                success, message = add_user(new_username, new_password, new_email, new_name, new_role)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    
    # User management actions
    if users:
        st.markdown("#### Manage Existing Users")
        
        # Select user to manage
        usernames = list(users.keys())
        selected_user = st.selectbox("Select User", usernames)
        
        if selected_user:
            user_info = users[selected_user]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Change Role**")
                current_role = user_info['role']
                new_role = st.selectbox(
                    "New Role", 
                    ["user", "admin"], 
                    index=0 if current_role == "user" else 1,
                    key=f"role_{selected_user}"
                )
                
                if st.button("Update Role", key=f"update_role_{selected_user}"):
                    if new_role != current_role:
                        success, message = update_user_role(selected_user, new_role)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.info("Role is already set to this value")
            
            with col2:
                st.markdown("**Change Password**")
                new_password = st.text_input("New Password", type="password", key=f"password_{selected_user}")
                
                if st.button("Update Password", key=f"update_password_{selected_user}"):
                    if new_password:
                        success, message = change_user_password(selected_user, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter a new password")
            
            with col3:
                st.markdown("**Remove User**")
                st.warning("⚠️ This action cannot be undone!")
                
                if st.button("Remove User", key=f"remove_{selected_user}", type="secondary"):
                    success, message = remove_user(selected_user)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    st.markdown("---")
    
    # Export/Import users
    st.markdown("#### Backup & Restore")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Users", use_container_width=True):
            if users:
                users_json = json.dumps(users, indent=2)
                st.download_button(
                    label="Download Users Backup",
                    data=users_json,
                    file_name=f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("No users to export")
    
    with col2:
        uploaded_file = st.file_uploader("Import Users", type=['json'], help="Upload a users backup file")
        if uploaded_file:
            try:
                imported_users = json.load(uploaded_file)
                # Validate the imported data
                valid_users = {}
                for username, user_info in imported_users.items():
                    if all(key in user_info for key in ['email', 'name', 'password', 'role']):
                        valid_users[username] = user_info
                
                if valid_users:
                    if st.button("Import Users", type="primary"):
                        # Merge with existing users (imported users will overwrite existing ones)
                        existing_users = load_users_from_file()
                        existing_users.update(valid_users)
                        
                        if save_users_to_file(existing_users):
                            st.success(f"Successfully imported {len(valid_users)} users")
                            st.rerun()
                        else:
                            st.error("Failed to save imported users")
                else:
                    st.error("Invalid users file format")
            except json.JSONDecodeError:
                st.error("Invalid JSON file")
    
    # Password reset section
    st.markdown("---")
    st.markdown("#### 🔐 Password Reset")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Reset Password by Email**")
        reset_email = st.text_input("Enter email address", key="reset_email_input")
        if st.button("Send Reset Email", key="send_reset_email_btn"):
            if reset_email:
                success, message = reset_password_by_email(reset_email)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("Please enter an email address")
    
    with col2:
        st.markdown("**Admin Password Reset**")
        if st.session_state.user_role == 'admin':
            users = get_all_users()
            user_list = list(users.keys())
            if user_list:
                selected_user_reset = st.selectbox("Select user to reset", user_list, key="admin_reset_select")
                new_password = st.text_input("New password", type="password", key="admin_new_password")
                if st.button("Reset Password", key="admin_reset_btn"):
                    if new_password:
                        # Update password directly
                        users = load_users_from_file()
                        if selected_user_reset in users:
                            users[selected_user_reset]['password'] = hash_password(new_password)
                            users[selected_user_reset]['password_reset_at'] = datetime.now().isoformat()
                            users[selected_user_reset]['password_reset_by'] = st.session_state.username
                            
                            if save_users_to_file(users):
                                st.success(f"Password reset successfully for {selected_user_reset}")
                                st.rerun()
                            else:
                                st.error("Failed to save new password")
                        else:
                            st.error("User not found")
                    else:
                        st.error("Please enter a new password")
            else:
                st.info("No users to reset")
        else:
            st.info("Only administrators can reset passwords")

def generate_reset_token():
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)

def save_reset_token(username, token):
    """Save reset token with expiration"""
    reset_tokens_file = 'reset_tokens.json'
    
    # Load existing tokens
    if os.path.exists(reset_tokens_file):
        with open(reset_tokens_file, 'r') as f:
            tokens = json.load(f)
    else:
        tokens = {}
    
    # Add new token with 1 hour expiration
    tokens[token] = {
        'username': username,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=1)).isoformat(),
        'used': False
    }
    
    # Save tokens
    with open(reset_tokens_file, 'w') as f:
        json.dump(tokens, f, indent=2)

def validate_reset_token(token):
    """Validate reset token and return username if valid"""
    reset_tokens_file = 'reset_tokens.json'
    
    if not os.path.exists(reset_tokens_file):
        return None
    
    with open(reset_tokens_file, 'r') as f:
        tokens = json.load(f)
    
    if token not in tokens:
        return None
    
    token_data = tokens[token]
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    if datetime.now() > expires_at:
        return None
    
    # Check if token is already used
    if token_data.get('used', False):
        return None
    
    return token_data['username']

def mark_token_as_used(token):
    """Mark a reset token as used"""
    reset_tokens_file = 'reset_tokens.json'
    
    if not os.path.exists(reset_tokens_file):
        return
    
    with open(reset_tokens_file, 'r') as f:
        tokens = json.load(f)
    
    if token in tokens:
        tokens[token]['used'] = True
        tokens[token]['used_at'] = datetime.now().isoformat()
        
        with open(reset_tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)

def send_reset_email(email, username, reset_token):
    """Send password reset email"""
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not smtp_username or not smtp_password:
            return False, "Email configuration not set. Please contact administrator."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = "Password Reset - Merak Capital Platform"
        
        # Create reset link
        base_url = os.getenv('BASE_URL', 'http://localhost:8501')
        reset_link = f"{base_url}?reset_token={reset_token}"
        
        # Email body
        body = f"""
        Hello {username},
        
        You have requested a password reset for your Merak Capital account.
        
        Click the link below to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you did not request this password reset, please ignore this email.
        
        Best regards,
        Merak Capital Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, email, text)
        server.quit()
        
        return True, "Password reset email sent successfully!"
        
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def reset_password_by_email(email):
    """Reset password by email"""
    # Find user by email
    all_users = get_all_users()
    user_found = None
    
    for username, user_info in all_users.items():
        if user_info.get('email') == email:
            user_found = username
            break
    
    if not user_found:
        return False, "No user found with that email address."
    
    # Generate reset token
    reset_token = generate_reset_token()
    save_reset_token(user_found, reset_token)
    
    # Check if email is configured
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_username or not smtp_password:
        # Email not configured - show reset link directly
        base_url = os.getenv('BASE_URL', 'http://localhost:8501')
        reset_link = f"{base_url}?reset_token={reset_token}"
        return True, f"Email not configured. Reset link: {reset_link}"
    
    # Send email
    success, message = send_reset_email(email, user_found, reset_token)
    
    if success:
        return True, f"Password reset instructions sent to {email}"
    else:
        return False, message

def reset_password_with_token(token, new_password):
    """Reset password using token"""
    username = validate_reset_token(token)
    
    if not username:
        return False, "Invalid or expired reset token."
    
    # Update password
    users = load_users_from_file()
    if username in users:
        users[username]['password'] = hash_password(new_password)
        users[username]['password_reset_at'] = datetime.now().isoformat()
        
        if save_users_to_file(users):
            mark_token_as_used(token)
            # Clear authentication cache to force refresh
            if 'auth_config_cache' in st.session_state:
                del st.session_state.auth_config_cache
            return True, f"Password reset successfully for user {username}"
        else:
            return False, "Failed to save new password."
    else:
        return False, "User not found."

def get_all_users():
    """Get all users including those from environment variables and file"""
    # Start with environment-based users
    all_users = {}
    
    # Add environment-based users
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD')
    if admin_password:
        all_users[admin_username] = {
            'email': os.getenv('ADMIN_EMAIL', 'admin@merakcapital.com'),
            'name': os.getenv('ADMIN_NAME', 'Admin User'),
            'password': hash_password(admin_password),
            'role': 'admin',
            'source': 'environment'
        }
    
    user_username = os.getenv('USER_USERNAME', 'user')
    user_password = os.getenv('USER_PASSWORD')
    if user_password:
        all_users[user_username] = {
            'email': os.getenv('USER_EMAIL', 'user@merakcapital.com'),
            'name': os.getenv('USER_NAME', 'Investment Analyst'),
            'password': hash_password(user_password),
            'role': 'user',
            'source': 'environment'
        }
    
    # Add file-based or session state users (but don't overwrite environment users)
    file_users = load_users_from_file()
    for username, user_info in file_users.items():
        # Only add if not already in all_users (environment users take priority)
        if username not in all_users:
            user_info['source'] = 'session' if 'persistent_users' in st.session_state else 'file'
            all_users[username] = user_info
    
    return all_users
