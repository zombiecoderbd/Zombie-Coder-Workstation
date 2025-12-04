@echo off
REM ZombieCoder Model Server Launcher
REM Uses Python 3.11 virtual environment

setlocal enabledelayedexpansion

echo [INFO] 🧠 Starting ZombieCoder Model Server...
echo [INFO] Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'

REM Check if running from correct directory
if not exist "server\main_complete.py" (
    echo [ERROR] Please run this script from zombiecoder root directory
    pause
    exit /b 1
)

REM Check Python 3.11 installation
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11 is not installed
    echo [INFO] Please install Python 3.11 from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('py -3.11 --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python 3.11 version check passed: %PYTHON_VERSION%

REM Check if virtual environment exists
if not exist ".venv" (
    echo [INFO] Creating virtual environment with Python 3.11...
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "workspace" mkdir workspace
echo [SUCCESS] Directories created

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%CD%\server
set LOG_LEVEL=INFO

REM Start model server on port 8157
echo [INFO] Starting ZombieCoder Model Server...
echo [INFO] Model Server will be available at: http://127.0.0.1:8157
echo [INFO] Press Ctrl+C to stop server
echo.
echo [INFO] 🚀 Starting model server...

REM Run the model server
python model_server.py

if errorlevel 1 (
    echo [ERROR] Model server failed to start
    pause
    exit /b 1
)

echo [SUCCESS] ZombieCoder model server stopped
pause