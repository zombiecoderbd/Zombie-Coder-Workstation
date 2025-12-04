#!/bin/bash

# ZombieCoder Local AI - Linux/macOS Startup Script
# "যেখানে কোড ও কথা বলে"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "server/main.py" ]; then
    print_error "Please run this script from the zombiecoder root directory"
    exit 1
fi

print_status "🧠 Starting ZombieCoder Local AI..."
print_status "Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8+ required. Found: $python_version"
    exit 1
fi

print_success "Python version check passed: $python_version"

# Check if virtual environment exists
if [ ! -d "zombie_env" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv zombie_env
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source zombie_env/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_status "Installing core dependencies..."
    pip install fastapi uvicorn aiohttp pyyaml chromadb redis sentence-transformers prometheus-client
    print_success "Core dependencies installed"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data workspace
print_success "Directories created"

# Check Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis is installed but not running"
        print_status "Starting Redis..."
        if command -v systemctl &> /dev/null; then
            sudo systemctl start redis || print_warning "Could not start Redis with systemctl"
        else
            redis-server --daemonize yes || print_warning "Could not start Redis daemon"
        fi
    fi
else
    print_warning "Redis not found. Install Redis for better performance"
fi

# Check configuration files
config_files=("config/config.yaml" "config/registry.yaml" "config/personality.yaml")
for config_file in "${config_files[@]}"; do
    if [ ! -f "$config_file" ]; then
        print_error "Configuration file missing: $config_file"
        exit 1
    fi
done
print_success "Configuration files found"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/server"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down ZombieCoder..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    print_success "Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the server
print_status "Starting ZombieCoder server..."
print_status "Dashboard will be available at: http://localhost:8000"
print_status "API documentation: http://localhost:8000/docs"
print_status "Press Ctrl+C to stop the server"

cd server
python main.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    print_success "ZombieCoder server started successfully (PID: $SERVER_PID)"
    print_status "🚀 System is ready!"
    
    # Wait for server process
    wait $SERVER_PID
else
    print_error "Failed to start server"
    exit 1
fi