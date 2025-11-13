# ⚡ Quick Start: Deploy in 5 Minutes

## 🚀 Fast Track Deployment

### 1️⃣ Push to GitHub (2 min)
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2️⃣ Deploy on Streamlit Cloud (2 min)
1. Go to: https://share.streamlit.io
2. Click "New app"
3. Select your repository
4. Main file: `streamlit_app.py`
5. Click "Deploy"

### 3️⃣ Set Secrets (1 min)
Go to: Settings → Secrets → Add:

```toml
ADMIN_PASSWORD = "YourSecurePassword123!"
USER_PASSWORD = "YourSecurePassword123!"
```

Click "Save" → Done! ✅

---

## 📧 Email Setup (Optional - 5 min)

### Gmail Quick Setup:
1. Enable 2FA: https://myaccount.google.com/security
2. Get App Password: https://myaccount.google.com/apppasswords
3. Add to Secrets:
```toml
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-16-char-app-password"
BASE_URL = "https://your-app-name.streamlit.app"
```

---

## 🔗 Your App URL
After deployment, your app will be at:
```
https://your-app-name.streamlit.app
```

---

## ❓ Need More Details?
See `STREAMLIT_CLOUD_DEPLOYMENT_GUIDE.md` for complete instructions.

