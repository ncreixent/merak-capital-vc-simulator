# Production Deployment Guide

## 🔐 **Credential Management for Production**

### **1. Environment Variables (Recommended)**

Set these environment variables in your production environment:

```bash
# Admin User
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password_here
ADMIN_EMAIL=admin@merakcapital.com
ADMIN_NAME=Admin User

# Standard User
USER_USERNAME=user
USER_PASSWORD=your_secure_user_password_here
USER_EMAIL=user@merakcapital.com
USER_NAME=Investment Analyst
```

### **2. Deployment Platforms**

#### **Streamlit Community Cloud**
```bash
# Create .streamlit/secrets.toml
[credentials]
admin_password = "your_secure_admin_password"
user_password = "your_secure_user_password"
```

#### **Heroku**
```bash
# Set environment variables
heroku config:set ADMIN_PASSWORD=your_secure_password
heroku config:set USER_PASSWORD=your_secure_password
```

#### **Docker**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Run with environment variables
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Run with environment variables
docker run -e ADMIN_PASSWORD=your_password -e USER_PASSWORD=your_password -p 8501:8501 your-app
```

### **3. Security Best Practices**

#### **Password Requirements**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words
- Unique per environment

#### **Example Strong Passwords**
```
Admin: M3r@kC@p1t@l2024!Adm1n
User:  Inv3stm3nt@n@lyst2024!
```

### **4. Advanced Security Options**

#### **Database-Backed Authentication**
```python
# For enterprise deployments, consider:
# - PostgreSQL/MySQL user tables
# - LDAP/Active Directory integration
# - OAuth providers (Google, Microsoft)
# - SAML SSO
```

#### **Session Security**
```python
# Add to your Streamlit config
[server]
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
```

### **5. Monitoring & Logging**

#### **Add Security Logging**
```python
import logging
from datetime import datetime

def log_auth_attempt(username, success, ip_address=None):
    """Log authentication attempts"""
    status = "SUCCESS" if success else "FAILED"
    timestamp = datetime.now().isoformat()
    
    logging.info(f"AUTH {status}: {username} at {timestamp} from {ip_address}")
```

### **6. Environment-Specific Configs**

#### **Development (.env)**
```bash
# .env file for local development
ADMIN_PASSWORD=admin123
USER_PASSWORD=user123
```

#### **Production**
```bash
# Production environment variables
ADMIN_PASSWORD=your_production_admin_password
USER_PASSWORD=your_production_user_password
```

### **7. Deployment Checklist**

- [ ] Set strong, unique passwords for each environment
- [ ] Use environment variables, not hardcoded credentials
- [ ] Enable HTTPS in production
- [ ] Set up proper logging and monitoring
- [ ] Regular password rotation (quarterly)
- [ ] Access audit logs
- [ ] Backup authentication configuration
- [ ] Test authentication in staging environment

### **8. Quick Start Commands**

#### **Local Development**
```bash
# No environment variables needed - uses default demo credentials
streamlit run streamlit_app.py
```

#### **Production Deployment**
```bash
# Set environment variables first
export ADMIN_PASSWORD="your_secure_password"
export USER_PASSWORD="your_secure_password"

# Then run
streamlit run streamlit_app.py
```

### **9. Troubleshooting**

#### **Common Issues**
- **Credentials not working**: Check environment variable names and values
- **Session issues**: Clear browser cache and cookies
- **Permission errors**: Verify user roles and permissions

#### **Debug Mode**
```python
# Add to auth.py for debugging
def debug_auth_status():
    """Debug authentication status"""
    st.write("Debug Info:")
    st.write(f"Environment: {'Production' if os.getenv('ADMIN_PASSWORD') else 'Development'}")
    st.write(f"Users configured: {len(auth_config['users'])}")
```

This approach ensures your credentials are secure, environment-specific, and easily manageable across different deployment scenarios.
