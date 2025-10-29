@echo off
REM Production Deployment Script for Merak Capital Investment Analysis Platform (Windows)

echo 🚀 Merak Capital - Production Deployment Script
echo ================================================

REM Check if environment variables are set
if "%ADMIN_PASSWORD%"=="" (
    echo ❌ Error: ADMIN_PASSWORD environment variable not set!
    goto :error
)
if "%USER_PASSWORD%"=="" (
    echo ❌ Error: USER_PASSWORD environment variable not set!
    goto :error
)

echo ✅ Environment variables configured
echo 📦 Installing dependencies...

REM Install Python dependencies
pip install -r requirements.txt

echo 🔧 Configuring Streamlit...

REM Create Streamlit config directory
if not exist .streamlit mkdir .streamlit

REM Create production Streamlit config
echo [server] > .streamlit\config.toml
echo headless = true >> .streamlit\config.toml
echo enableCORS = false >> .streamlit\config.toml
echo enableXsrfProtection = true >> .streamlit\config.toml
echo maxUploadSize = 200 >> .streamlit\config.toml
echo port = 8501 >> .streamlit\config.toml
echo address = "0.0.0.0" >> .streamlit\config.toml
echo. >> .streamlit\config.toml
echo [browser] >> .streamlit\config.toml
echo gatherUsageStats = false >> .streamlit\config.toml

echo 🔐 Security configuration complete
echo 🌐 Starting application...

REM Start the application
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0

echo ✅ Application started successfully!
echo 🌍 Access your app at: http://localhost:8501
goto :end

:error
echo.
echo Please set the following environment variables:
echo   set ADMIN_PASSWORD=your_secure_admin_password
echo   set USER_PASSWORD=your_secure_user_password
echo.
echo Example:
echo   set ADMIN_PASSWORD=M3r@kC@p1t@l2024!Adm1n
echo   set USER_PASSWORD=Inv3stm3nt@n@lyst2024!
echo.
pause
exit /b 1

:end
pause
