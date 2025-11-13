# 🚀 Complete Guide: Deploying to Streamlit Cloud

This guide will walk you through deploying your Merak Capital VC Fund Simulator to Streamlit Cloud and setting up email password recovery.

---

## 📋 Prerequisites

Before you begin, make sure you have:
- ✅ A GitHub account
- ✅ Your code pushed to a GitHub repository
- ✅ A Gmail account (for email recovery)
- ✅ Access to Streamlit Cloud (free at https://share.streamlit.io)

---

## Part 1: Prepare Your Repository

### Step 1.1: Verify Required Files

Make sure your repository has these files in the root directory:

```
├── streamlit_app.py          ✅ Main application file
├── requirements.txt          ✅ Python dependencies
├── config.yaml               ✅ Default configuration
├── auth_config.yaml          ✅ Authentication config (optional)
├── users.json                ✅ User database (optional)
└── .gitignore               ✅ (should exclude sensitive files)
```

### Step 1.2: Check requirements.txt

Your `requirements.txt` should include:
```txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0
pyyaml>=6.0
pathlib
```

**Note**: If you have additional dependencies, add them here.

### Step 1.3: Create .gitignore (if not exists)

Create a `.gitignore` file to exclude sensitive files:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/

# Streamlit
.streamlit/secrets.toml

# Sensitive files
users.json
reset_tokens.json
*.pkl
*.xlsx

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### Step 1.4: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Ready for Streamlit Cloud deployment"

# Add your GitHub remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Push to GitHub
git push -u origin main
```

---

## Part 2: Deploy to Streamlit Cloud

### Step 2.1: Sign Up / Log In

1. Go to **https://share.streamlit.io**
2. Click **"Sign in"** (use your GitHub account)
3. Authorize Streamlit Cloud to access your GitHub repositories

### Step 2.2: Create New App

1. Click **"New app"** button
2. Fill in the form:
   - **Repository**: Select your repository from the dropdown
   - **Branch**: `main` (or `master` if that's your default branch)
   - **Main file path**: `streamlit_app.py`
   - **App URL**: Choose a unique name (e.g., `merak-capital-vc-simulator`)
3. Click **"Deploy"**

### Step 2.3: Wait for Initial Deployment

- Streamlit Cloud will automatically install dependencies and deploy your app
- This usually takes 2-5 minutes
- You'll see a progress indicator
- Once complete, you'll see: **"Your app is live!"**

### Step 2.4: Get Your App URL

After deployment, note your app URL:
```
https://your-app-name.streamlit.app
```
**Save this URL** - you'll need it for email configuration!

---

## Part 3: Configure Secrets (Authentication & Email)

### Step 3.1: Access Secrets Manager

1. In Streamlit Cloud, click on your app
2. Click the **⚙️ Settings** button (top right)
3. Click **"Secrets"** in the left sidebar

### Step 3.2: Add Authentication Secrets

Add these **REQUIRED** secrets:

```toml
ADMIN_PASSWORD = "YourSecureAdminPassword123!"
USER_PASSWORD = "YourSecureUserPassword123!"
```

**Security Tips:**
- Use strong passwords (12+ characters)
- Mix uppercase, lowercase, numbers, and symbols
- Use different passwords for admin and user accounts

### Step 3.3: Set Up Email Recovery (Optional but Recommended)

#### Option A: Gmail Setup (Recommended)

1. **Enable 2-Step Verification**:
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification" if not already enabled

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select "Other (Custom name)" → Enter "Merak Capital"
   - Click "Generate"
   - **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)

3. **Add Email Secrets to Streamlit Cloud**:
   ```toml
   SMTP_SERVER = "smtp.gmail.com"
   SMTP_PORT = "587"
   SMTP_USERNAME = "your-email@gmail.com"
   SMTP_PASSWORD = "abcdefghijklmnop"
   BASE_URL = "https://your-app-name.streamlit.app"
   ```

   **Important Notes:**
   - `SMTP_PASSWORD`: Use the 16-character App Password (remove spaces)
   - `SMTP_USERNAME`: Your full Gmail address
   - `BASE_URL`: Your exact Streamlit Cloud app URL from Step 2.4

#### Option B: Outlook/Hotmail Setup

```toml
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@outlook.com"
SMTP_PASSWORD = "your-outlook-password"
BASE_URL = "https://your-app-name.streamlit.app"
```

#### Option C: Yahoo Setup

```toml
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@yahoo.com"
SMTP_PASSWORD = "your-yahoo-app-password"
BASE_URL = "https://your-app-name.streamlit.app"
```

### Step 3.4: Save Secrets

1. Click **"Save"** at the bottom of the secrets page
2. Your app will automatically restart with the new secrets
3. Wait for the restart to complete (usually 30-60 seconds)

---

## Part 4: Verify Deployment

### Step 4.1: Test Authentication

1. Open your app URL: `https://your-app-name.streamlit.app`
2. You should see the login page
3. Try logging in with:
   - **Admin**: Username from your auth config + ADMIN_PASSWORD
   - **User**: Username from your auth config + USER_PASSWORD

### Step 4.2: Test Email Recovery (if configured)

1. Click **"Forgot Password?"** on the login page
2. Enter a registered email address
3. Check your email inbox for the reset link
4. Click the reset link
5. Set a new password
6. Try logging in with the new password

### Step 4.3: Test App Functionality

- ✅ Create a new scenario
- ✅ Run a simulation
- ✅ View results
- ✅ Compare scenarios

---

## Part 5: Troubleshooting

### Issue: App Won't Deploy

**Symptoms**: Deployment fails or shows errors

**Solutions**:
1. Check `requirements.txt` - ensure all dependencies are listed
2. Check logs in Streamlit Cloud (click "Manage app" → "Logs")
3. Verify `streamlit_app.py` is in the root directory
4. Check Python version compatibility (Streamlit Cloud uses Python 3.11)

### Issue: Authentication Not Working

**Symptoms**: Can't log in, or wrong credentials

**Solutions**:
1. Verify secrets are set correctly in Streamlit Cloud
2. Check that `ADMIN_PASSWORD` and `USER_PASSWORD` match your expectations
3. Clear browser cache and cookies
4. Check `auth_config.yaml` or `users.json` for correct usernames

### Issue: Email Not Sending

**Symptoms**: Password reset emails not received

**Solutions**:
1. **Verify App Password**: Make sure you're using the 16-character App Password, not your regular Gmail password
2. **Check 2FA**: Ensure 2-Step Verification is enabled on your Gmail account
3. **Verify Secrets**: Double-check all email secrets in Streamlit Cloud:
   - `SMTP_SERVER`
   - `SMTP_PORT`
   - `SMTP_USERNAME` (full email address)
   - `SMTP_PASSWORD` (App Password, no spaces)
   - `BASE_URL` (exact app URL)
4. **Check Logs**: Look at Streamlit Cloud logs for error messages
5. **Test SMTP Connection**: Try sending a test email manually

### Issue: App Crashes or Errors

**Symptoms**: App loads but shows errors or crashes

**Solutions**:
1. Check Streamlit Cloud logs for error messages
2. Verify all required files are in the repository
3. Check that `config.yaml` is valid YAML
4. Ensure all Python imports are available in `requirements.txt`

---

## Part 6: Updating Your App

### Step 6.1: Make Changes Locally

1. Make your code changes
2. Test locally: `streamlit run streamlit_app.py`
3. Commit changes: `git add . && git commit -m "Description of changes"`

### Step 6.2: Push to GitHub

```bash
git push origin main
```

### Step 6.3: Streamlit Cloud Auto-Deploys

- Streamlit Cloud automatically detects the push
- It will redeploy your app automatically
- Usually takes 2-5 minutes
- You'll see a notification when complete

### Step 6.4: Manual Redeploy (if needed)

1. Go to your app in Streamlit Cloud
2. Click **"⋮"** (three dots) → **"Redeploy"**
3. Wait for deployment to complete

---

## Part 7: Best Practices

### Security

- ✅ Use strong, unique passwords
- ✅ Never commit secrets to GitHub
- ✅ Use App Passwords for email (not regular passwords)
- ✅ Regularly rotate passwords
- ✅ Monitor access logs

### Performance

- ✅ Optimize large data files (consider pre-processing)
- ✅ Use caching for expensive computations
- ✅ Limit file upload sizes
- ✅ Optimize images and assets

### Maintenance

- ✅ Keep dependencies updated
- ✅ Monitor app performance
- ✅ Review logs regularly
- ✅ Backup important configurations

---

## 📞 Quick Reference

### Your App URL
```
https://your-app-name.streamlit.app
```

### Streamlit Cloud Dashboard
```
https://share.streamlit.io
```

### Secrets Configuration
```
Settings → Secrets → Add secrets → Save
```

### Gmail App Passwords
```
https://myaccount.google.com/apppasswords
```

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Repository connected to Streamlit Cloud
- [ ] App deployed successfully
- [ ] `ADMIN_PASSWORD` secret set
- [ ] `USER_PASSWORD` secret set
- [ ] Email secrets configured (if using email recovery)
- [ ] `BASE_URL` matches app URL exactly
- [ ] Authentication tested and working
- [ ] Email recovery tested (if configured)
- [ ] App functionality verified

---

## 🎉 You're All Set!

Your Merak Capital VC Fund Simulator is now live on Streamlit Cloud!

**Next Steps:**
1. Share the app URL with your team
2. Set up user accounts as needed
3. Monitor usage and performance
4. Iterate and improve based on feedback

**Need Help?**
- Check Streamlit Cloud logs for errors
- Review the troubleshooting section above
- Consult Streamlit documentation: https://docs.streamlit.io

---

**Last Updated**: 2025-01-26
**Version**: 1.0

