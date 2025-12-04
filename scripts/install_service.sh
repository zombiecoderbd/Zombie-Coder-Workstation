#!/bin/bash

# ZombieCoder Local AI - Service Installation Script (Linux)
# Install as systemd service for auto-start on boot

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configuration
SERVICE_NAME="zombiecoder"
SERVICE_USER=$(whoami)
INSTALL_DIR="$(pwd)"
VENV_DIR="$INSTALL_DIR/zombie_env"

# Check if running as root for service installation
if [ "$EUID" -ne 0 ]; then
    print_error "Please run with sudo to install system service"
    exit 1
fi

print_status "🧠 Installing ZombieCoder Local AI as system service..."
print_status "Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'"

# Check if service already exists
if systemctl is-active --quiet $SERVICE_NAME; then
    print_warning "Service $SERVICE_NAME is already running"
    print_status "Stopping existing service..."
    systemctl stop $SERVICE_NAME
fi

if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    print_status "Removing existing service..."
    systemctl disable $SERVICE_NAME
    rm -f /etc/systemd/system/$SERVICE_NAME.service
    systemctl daemon-reload
fi

# Create systemd service file
print_status "Creating systemd service file..."

cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=ZombieCoder Local AI - Agent Workstation Layer
Documentation=https://zombiecoder.my.id/
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$VENV_DIR/bin
Environment=PYTHONPATH=$INSTALL_DIR/server
Environment=LOG_LEVEL=INFO
ExecStart=$VENV_DIR/bin/python server/main.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/service.log
StandardError=append:$INSTALL_DIR/logs/service_error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/logs $INSTALL_DIR/data $INSTALL_DIR/workspace

[Install]
WantedBy=multi-user.target
EOF

print_success "Service file created"

# Set proper permissions
chown root:root /etc/systemd/system/$SERVICE_NAME.service
chmod 644 /etc/systemd/system/$SERVICE_NAME.service

# Reload systemd
print_status "Reloading systemd..."
systemctl daemon-reload

# Enable service to start on boot
print_status "Enabling service to start on boot..."
systemctl enable $SERVICE_NAME

# Start the service
print_status "Starting ZombieCoder service..."
systemctl start $SERVICE_NAME

# Wait a moment and check status
sleep 3

if systemctl is-active --quiet $SERVICE_NAME; then
    print_success "ZombieCoder service started successfully!"
    print_status "Service status: $(systemctl is-active $SERVICE_NAME)"
    print_status "Dashboard: http://localhost:8000"
    print_status "API docs: http://localhost:8000/docs"
    print_status "Logs: tail -f $INSTALL_DIR/logs/service.log"
    
    # Show service status
    echo
    systemctl status $SERVICE_NAME --no-pager
else
    print_error "Failed to start ZombieCoder service"
    print_status "Check logs with: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

print_success "Installation complete!"
print_status "Useful commands:"
echo "  Start service:   sudo systemctl start $SERVICE_NAME"
echo "  Stop service:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart service:  sudo systemctl restart $SERVICE_NAME"
echo "  Check status:     sudo systemctl status $SERVICE_NAME"
echo "  View logs:       sudo journalctl -u $SERVICE_NAME -f"
echo "  View file logs:   tail -f $INSTALL_DIR/logs/service.log"