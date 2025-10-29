# Merak Capital GUI Delivery - Authentication Setup

## 🔐 **Authentication Features Added**

Your Streamlit app now includes comprehensive authentication with:

- **Role-based access control** (Admin, Analyst, Viewer)
- **Secure password hashing** using bcrypt
- **Session management** with cookies
- **Permission-based UI** restrictions
- **Professional login interface**

## 👥 **Default User Accounts**

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `admin` | `admin123` | Admin | Full access (create, read, update, delete, run_simulations, view_all) |
| `analyst` | `analyst123` | Analyst | Analysis tools (read, run_simulations, view_all) |
| `viewer` | `viewer123` | Viewer | View-only access (read) |

## 🚀 **Deployment with Authentication**

### **1. Streamlit Community Cloud (Recommended)**

**Steps**:
1. **Update requirements.txt** (already done):
   ```
   streamlit-authenticator>=0.2.3
   ```

2. **Push to GitHub** (exclude sensitive files):
   ```bash
   git add .
   git commit -m "Add authentication system"
   git push origin main
   ```

3. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Connect your repository
   - Set main file: `streamlit_app.py`
   - Deploy!

4. **Configure secrets** (after deployment):
   - Go to your app's settings
   - Add secrets for production users
   - Update `config.yaml` with real passwords

### **2. Heroku with Authentication**

**Additional setup**:
1. **Environment variables** (for production):
   ```bash
   heroku config:set AUTH_COOKIE_KEY=your_production_key_here
   ```

2. **Update config.yaml** with production credentials

### **3. Docker with Authentication**

**Security considerations**:
- Use environment variables for secrets
- Mount `config.yaml` as volume
- Use HTTPS in production

## 🔧 **Customization Options**

### **Add New Users**

Edit `config.yaml`:
```yaml
credentials:
  usernames:
    newuser:
      email: newuser@company.com
      name: New User
      password: $2b$12$hashed_password_here
```

### **Change Permissions**

Edit `auth.py` - `check_user_permissions()` function:
```python
permissions = {
    'admin': ['create', 'read', 'update', 'delete', 'run_simulations', 'view_all'],
    'analyst': ['read', 'run_simulations', 'view_all'],
    'viewer': ['read'],
    'newrole': ['read', 'run_simulations']  # Add new role
}
```

### **Customize Login Page**

Edit `auth.py` - `render_login_page()` function to match your branding.

## 🛡️ **Security Best Practices**

1. **Change default passwords** before production deployment
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Enable HTTPS** for all production deployments
4. **Regular password updates** for admin accounts
5. **Monitor access logs** if available
6. **Backup user configurations** securely

## 🔄 **Alternative Authentication Methods**

### **OAuth Integration** (Advanced)
For enterprise SSO integration:
- Google OAuth
- Microsoft Azure AD
- Okta
- Custom OAuth providers

### **LDAP Integration** (Enterprise)
For corporate directory integration:
- Active Directory
- OpenLDAP
- Custom LDAP servers

## 📋 **Production Checklist**

- [ ] Change all default passwords
- [ ] Configure HTTPS/SSL
- [ ] Set up proper secrets management
- [ ] Test all user roles and permissions
- [ ] Configure backup for user data
- [ ] Set up monitoring and logging
- [ ] Document user management procedures

## 🆘 **Troubleshooting**

**Login issues**:
- Check password hashing in `config.yaml`
- Verify cookie settings
- Clear browser cache/cookies

**Permission errors**:
- Check user role in `config.yaml`
- Verify permissions in `auth.py`
- Restart application

**Deployment issues**:
- Ensure `streamlit-authenticator` is in requirements.txt
- Check file permissions for `config.yaml`
- Verify environment variables

Your app is now ready for secure deployment with professional authentication! 🎉
