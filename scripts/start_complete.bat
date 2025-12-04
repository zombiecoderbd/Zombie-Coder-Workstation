@echo off
REM ZombieCoder Local AI - Complete Production Startup Script for Windows
REM "যেখানে কোড ও কথা বলে" - Full Production System

setlocal enabledelayedexpansion

echo [INFO] 🧟‍♂️ Starting Complete ZombieCoder Local AI System
echo [INFO] Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'

REM Check if running from correct directory
if not exist "server\main_complete.py" (
    echo [ERROR] Please run this script from zombiecoder root directory
    echo [ERROR] Expected file: server\main_complete.py
    pause
    exit /b 1
)

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [ERROR] Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2,3" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo [SUCCESS] Python version check passed: %python_version%

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
echo [INFO] Upgrading pip and installing core dependencies...
python -m pip install --upgrade pip setuptools wheel

REM Install production dependencies
echo [INFO] Installing complete production dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Production dependencies installed
) else (
    echo [WARNING] requirements.txt not found, installing core dependencies...
    pip install fastapi uvicorn aiohttp pyyaml python-dotenv
    pip install chromadb redis
    pip install prometheus-client psutil
    pip install cryptography aiofiles
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "workspace" mkdir workspace
if not exist "config\local" mkdir config\local
if not exist "config\production" mkdir config\production
if not exist "static" mkdir static
if not exist "mini-services\chat-service" mkdir mini-services\chat-service
if not exist "mini-services\monitoring-service" mkdir mini-services\monitoring-service
if not exist "mini-services\rag-service" mkdir mini-services\rag-service
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
        echo [ERROR] Please ensure all configuration files exist
        pause
        exit /b 1
    )
)
echo [SUCCESS] Configuration files found

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%CD%\server
set ZOMBIECODER_ENV=production
set LOG_LEVEL=INFO

REM Start mini services in background
echo [INFO] Starting mini services...
start /B "RAG Service" cmd /c "cd mini-services\rag-service && python index.ts"
start /B "Monitoring Service" cmd /c "cd mini-services\monitoring-service && python index.ts"
start /B "Chat Service" cmd /c "cd mini-services\chat-service && python index.ts"

REM Wait for services to start
timeout /t 3 /nobreak >nul

REM Start main server
echo [INFO] Starting main ZombieCoder server...
echo [INFO] Dashboard will be available at: http://localhost:8000
echo [INFO] API documentation: http://localhost:8000/docs
echo [INFO] System health: http://localhost:8000/api/health
echo [INFO] Proxy server: http://localhost:3000
echo [INFO] Press Ctrl+C to stop all services
echo.

cd server
python main_complete.py

if errorlevel 1 (
    echo [ERROR] Failed to start main server
    pause
    exit /b 1
)

echo [SUCCESS] ZombieCoder Local AI Complete System is running!
echo [INFO] Use 'tasklist' to see running processes
echo [INFO] Use 'taskkill /f python.exe' to stop services
pause