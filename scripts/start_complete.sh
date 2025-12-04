#!/bin/bash

# ZombieCoder Local AI - Complete Production Startup Script
# "যেখানে কোড ও কথা বলে" - Full Production System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Check if running from correct directory
if [ ! -f "server/main_complete.py" ]; then
    print_error "Please run this script from zombiecoder root directory"
    print_error "Expected file: server/main_complete.py"
    exit 1
fi

print_header "🧟‍♂️ ZombieCoder Local AI - Complete Production System"
print_status "Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'"
print_status "Starting complete system initialization..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8+ required. Found: $python_version"
    print_error "Please install Python 3.8 or higher"
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
print_status "Upgrading pip and installing core dependencies..."
python -m pip install --upgrade pip setuptools wheel

# Install production dependencies
print_status "Installing complete production dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Production dependencies installed"
else
    print_warning "requirements.txt not found, installing core dependencies..."
    pip install fastapi uvicorn aiohttp pyyaml python-dotenv
    pip install chromadb redis redis[hiredis]
    pip install prometheus-client psutil
    pip install cryptography aiofiles
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data workspace config/{local,production} static
mkdir -p mini-services/{chat-service,monitoring-service,rag-service}
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
    print_status "To install Redis: sudo apt install redis-server (Ubuntu) or brew install redis (macOS)"
fi

# Check configuration files
config_files=("config/config.yaml" "config/registry.yaml" "config/personality.yaml")
for config_file in "${config_files[@]}"; do
    if [ ! -f "$config_file" ]; then
        print_error "Configuration file missing: $config_file"
        print_error "Please ensure all configuration files exist"
        exit 1
    fi
done
print_success "Configuration files found"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/server"
export ZOMBIECODER_ENV="production"
export LOG_LEVEL="INFO"

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down ZombieCoder services..."
    
    # Kill background processes
    pkill -f "python.*main_complete.py" 2>/dev/null || true
    pkill -f "python.*index.ts" 2>/dev/null || true
    
    print_success "Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Function to start mini services
start_mini_services() {
    print_status "Starting mini services..."
    
    # Start RAG Service
    cd mini-services/rag-service
    python main.py &
    RAG_PID=$!
    cd ../..
    
    # Start Monitoring Service
    cd mini-services/monitoring-service
    python main.py &
    MONITORING_PID=$!
    cd ../..
    
    # Start Chat Service
    cd mini-services/chat-service
    python index.ts &
    CHAT_PID=$!
    cd ../..
    
    # Wait a moment for services to start
    sleep 3
    
    print_success "Mini services started"
    print_status "RAG Service: PID $RAG_PID (Port 3001)"
    print_status "Monitoring Service: PID $MONITORING_PID (Port 3002)"
    print_status "Chat Service: PID $CHAT_PID (Port 3003)"
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Check main server
    if curl -s http://localhost:8000/api/health > /dev/null; then
        print_success "Main server is healthy"
    else
        print_warning "Main server is not responding"
    fi
    
    # Check mini services
    for port in 3001 3002 3003; do
        if curl -s http://localhost:$port/health > /dev/null; then
            print_success "Service on port $port is healthy"
        else
            print_warning "Service on port $port is not responding"
        fi
    done
}

# Function to show system status
show_system_status() {
    print_header "📊 System Status"
    
    echo -e "${CYAN}Services Running:${NC}"
    ps aux | grep python | grep -E "(main_complete|index.ts)" | grep -v grep || echo "No services running"
    
    echo -e "${CYAN}Port Usage:${NC}"
    netstat -tlnp 2>/dev/null | grep -E ":(8000|3001|3002|3003)" || echo "No ports in use"
    
    echo -e "${CYAN}Resource Usage:${NC}"
    echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2 " (" int($3/$2 * 100) "%)"}')" 2>/dev/null || echo "N/A")"
    echo "Disk: $(df -h . | awk 'NR==2 {print $3 " / " $2 " (" int($3/$2 * 100) "%)"}')" 2>/dev/null || echo "N/A")"
}

# Main execution
main() {
    print_header "🚀 Starting Complete ZombieCoder Local AI System"
    
    # Start mini services in background
    start_mini_services
    
    # Wait for services to initialize
    sleep 5
    
    # Start main server
    print_status "Starting main ZombieCoder server..."
    print_status "Dashboard will be available at: http://localhost:8000"
    print_status "API documentation: http://localhost:8000/docs"
    print_status "System health: http://localhost:8000/api/health"
    print_status "Proxy server: http://localhost:3000"
    print_status "Press Ctrl+C to stop all services"
    echo
    
    cd server
    python main_complete.py &
    MAIN_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Check if server started successfully
    if kill -0 $MAIN_PID 2>/dev/null; then
        print_success "Main server started successfully (PID: $MAIN_PID)"
        
        # Show service health
        check_service_health
        
        # Show system status
        show_system_status
        
        # Wait for user interrupt
        wait $MAIN_PID
    else
        print_error "Failed to start main server"
        exit 1
    fi
}

# Show help
show_help() {
    echo "ZombieCoder Local AI - Complete Production System"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start       Start the complete system (default)"
    echo "  stop        Stop all services"
    echo "  status      Show system status"
    echo "  restart     Restart all services"
    echo "  health      Check service health"
    echo "  help        Show this help message"
    echo ""
    echo "Services:"
    echo "  Main Server:      http://localhost:8000"
    echo "  Proxy Server:     http://localhost:3000"
    echo "  RAG Service:      http://localhost:3001"
    echo "  Monitoring:        http://localhost:3002"
    echo "  Chat Service:     http://localhost:3003"
    echo ""
    echo "Examples:"
    echo "  $0 start          # Start complete system"
    echo "  $0 status         # Check system status"
    echo "  $0 health         # Check service health"
}

# Parse command line arguments
case "${1:-start}" in
    start)
        main
        ;;
    stop)
        cleanup
        ;;
    status)
        show_system_status
        ;;
    restart)
        cleanup
        sleep 2
        main
        ;;
    health)
        check_service_health
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac