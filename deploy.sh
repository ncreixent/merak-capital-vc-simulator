#!/bin/bash

# Production Deployment Script for Merak Capital Investment Analysis Platform

echo "🚀 Merak Capital - Production Deployment Script"
echo "================================================"

# Check if environment variables are set
if [ -z "$ADMIN_PASSWORD" ] || [ -z "$USER_PASSWORD" ]; then
    echo "❌ Error: Required environment variables not set!"
    echo ""
    echo "Please set the following environment variables:"
    echo "  export ADMIN_PASSWORD='your_secure_admin_password'"
    echo "  export USER_PASSWORD='your_secure_user_password'"
    echo ""
    echo "Example:"
    echo "  export ADMIN_PASSWORD='M3r@kC@p1t@l2024!Adm1n'"
    echo "  export USER_PASSWORD='Inv3stm3nt@n@lyst2024!'"
    echo ""
    exit 1
fi

echo "✅ Environment variables configured"
echo "📦 Installing dependencies..."

# Install Python dependencies
pip install -r requirements.txt

echo "🔧 Configuring Streamlit..."

# Create Streamlit config directory
mkdir -p .streamlit

# Create production Streamlit config
cat > .streamlit/config.toml << EOF
[server]
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
port = 8501
address = "0.0.0.0"

[browser]
gatherUsageStats = false
EOF

echo "🔐 Security configuration complete"
echo "🌐 Starting application..."

# Start the application
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0

echo "✅ Application started successfully!"
echo "🌍 Access your app at: http://localhost:8501"
