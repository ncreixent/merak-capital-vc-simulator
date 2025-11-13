[1mdiff --git a/auth.py b/auth.py[m
[1mindex d1566b7..66b91bf 100644[m
[1m--- a/auth.py[m
[1m+++ b/auth.py[m
[36m@@ -83,12 +83,20 @@[m [mdef setup_authentication():[m
         os.getenv('USER_PASSWORD')[m
     ])[m
     [m
[31m-    if is_production or all_users:[m
[31m-        # Use all available users[m
[32m+[m[32m    if is_production:[m
[32m+[m[32m        # In production, use only environment + file-based users[m
         auth_config = {'users': all_users}[m
     else:[m
[31m-        # Fall back to development credentials[m
[31m-        auth_config = load_development_credentials()[m
[32m+[m[32m        # In development, always include default admin/user accounts[m
[32m+[m[32m        # Merge development credentials with existing users[m
[32m+[m[32m        dev_credentials = load_development_credentials()[m
[32m+[m[32m        dev_users = dev_credentials['users'][m
[32m+[m[41m        [m
[32m+[m[32m        # Merge: file-based users take precedence, but dev users are always available[m
[32m+[m[32m        merged_users = dev_users.copy()[m
[32m+[m[32m        merged_users.update(all_users)  # File-based users override dev users if they exist[m
[32m+[m[41m        [m
[32m+[m[32m        auth_config = {'users': merged_users}[m
     [m
     # Cache the auth config[m
     st.session_state.auth_config_cache = auth_config[m
