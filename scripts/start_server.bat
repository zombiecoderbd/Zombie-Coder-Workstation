@echo off
REM ZombieCoder Local AI - Windows Startup Script
REM "যেখানে কোড ও কথা বলে"

setlocal enabledelayedexpansion

echo [INFO] 🧠 Starting ZombieCoder Local AI...
echo [INFO] Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'

REM Check if running from correct directory
if not exist "server\main.py" (
    echo [ERROR] Please run this script from zombiecoder root directory
    pause
    exit /b 1
)

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [INFO] Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python version check passed: %PYTHON_VERSION%

REM Check if virtual environment exists
if not exist "zombie_env" (
    echo [INFO] Creating virtual environment...
    python -m venv zombie_env
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call zombie_env\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
if exist "requirements.txt" (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed
) else (
    echo [INFO] Installing core dependencies...
    pip install fastapi uvicorn aiohttp pyyaml chromadb redis sentence-transformers prometheus-client
    if errorlevel 1 (
        echo [ERROR] Failed to install core dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Core dependencies installed
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "workspace" mkdir workspace
echo [SUCCESS] Directories created

REM Check Redis
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Redis is not running
    echo [INFO] Install Redis for better performance
    echo [INFO] Download from: https://github.com/microsoftarchive/redis/releases
) else (
    echo [SUCCESS] Redis is running
)

REM Check configuration files
set CONFIG_FILES=config\config.yaml config\registry.yaml config\personality.yaml
for %%f in (%CONFIG_FILES%) do (
    if not exist "%%f" (
        echo [ERROR] Configuration file missing: %%f
        pause
        exit /b 1
    )
)
echo [SUCCESS] Configuration files found

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%CD%\server
if "%LOG_LEVEL%"=="" set LOG_LEVEL=INFO

REM Start server
echo [INFO] Starting ZombieCoder server...
echo [INFO] Dashboard will be available at: http://localhost:8000
echo [INFO] API documentation: http://localhost:8000/docs
echo [INFO] Press Ctrl+C to stop server
echo.
echo [INFO] 🚀 Starting server...

cd server
python main.py

if errorlevel 1 (
    echo [ERROR] Server failed to start
    pause
    exit /b 1
)

echo [SUCCESS] ZombieCoder server stopped
pause