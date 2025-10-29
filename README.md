# Merak Capital - VC Fund Simulation Platform

A comprehensive Streamlit application for Monte Carlo simulation of venture capital fund performance.

## 🚀 Quick Start

### Local Development
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Streamlit Community Cloud Deployment

1. **Fork this repository**
2. **Go to [Streamlit Community Cloud](https://share.streamlit.io)**
3. **Click "New app"**
4. **Connect your GitHub repository**
5. **Set the following secrets in Streamlit Cloud:**

#### Required Secrets:
```
ADMIN_PASSWORD = "YourSecureAdminPassword123!"
USER_PASSWORD = "YourSecureUserPassword123!"
```

#### Optional Secrets (for email reset):
```
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-gmail-app-password"
BASE_URL = "https://your-app-name.streamlit.app"
```

## 🔐 Authentication

- **Admin User**: Full access to all features including user management
- **Regular User**: Can run simulations and view results

## 📊 Features

- **Monte Carlo Simulation**: Advanced VC fund performance modeling
- **Scenario Management**: Create, save, and compare different scenarios
- **Interactive Analysis**: Real-time charts and visualizations
- **User Management**: Role-based access control
- **Password Reset**: Email-based password recovery

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Authentication**: Custom implementation

## 📁 Project Structure

```
├── streamlit_app.py          # Main application
├── run_tab.py               # Simulation and analysis
├── setup_tab.py             # Scenario management
├── compare_tab.py           # Scenario comparison
├── auth.py                  # Authentication system
├── user_management.py       # User management
├── ui_components.py         # Reusable UI components
├── engine.py                # Monte Carlo engine
├── parameters.py            # Fund parameters
├── config.yaml              # Default configuration
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration

The application uses environment variables for configuration. See `secrets.toml.example` for all available options.

## 📞 Support

For issues or questions, please contact the development team.