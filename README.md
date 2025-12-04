# 🧠 ZombieCoder Local AI - Complete Installation Guide
## Agent Workstation Layer - "যেখানে কোড ও কথা বলে"

**Provider:** Developer Zone  
**Owner:** Sahon Srabon  
**Contact:** +880 1323-626282  
**Website:** https://zombiecoder.my.id/

---

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Windows Installation](#windows-installation)
3. [Linux Installation](#linux-installation)
4. [Configuration Setup](#configuration-setup)
5. [Running the System](#running-the-system)
6. [API Documentation](#api-documentation)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## 🔧 System Requirements

### Minimum Requirements
- **RAM:** 4GB (8GB recommended)
- **Storage:** 10GB free space
- **Python:** 3.8 or higher
- **OS:** Windows 10/11, Ubuntu 18.04+, macOS 10.15+

### Optional Requirements
- **GPU:** NVIDIA GPU with CUDA support (for local models)
- **Redis Server:** For caching (optional but recommended)
- **Docker:** For containerized deployment (optional)

---

## 🪟 Windows Installation

### Step 1: Install Python
1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. Run the installer and **check "Add Python to PATH"**
3. Verify installation:
```cmd
python --version
pip --version
```

### Step 2: Install Git
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Install with default settings
3. Verify installation:
```cmd
git --version
```

### Step 3: Install Visual C++ Build Tools
1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install "C++ build tools" workload
3. This is required for some Python packages

### Step 4: Clone and Setup ZombieCoder
```cmd
# Clone the repository
git clone <repository-url>
cd zombiecoder

# Create virtual environment
python -m venv zombie_env

# Activate virtual environment
zombie_env\\Scripts\\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 5: Install Dependencies
```cmd
# Install core dependencies
pip install fastapi uvicorn aiohttp pyyaml

# Install AI/ML dependencies
pip install chromadb redis sentence-transformers

# Install monitoring dependencies
pip install prometheus-client

# Install additional dependencies
pip install asyncio logging pathlib dataclasses typing
```

### Step 6: Install Redis (Optional but Recommended)
1. Download Redis for Windows from [Microsoft Archive](https://github.com/microsoftarchive/redis/releases)
2. Extract and run `redis-server.exe`
3. Or install via Chocolatey:
```cmd
choco install redis-64
redis-server
```

### Step 7: Configure Environment Variables
Create a `.env` file in the project root:
```env
# OpenAI API Key (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging Level
LOG_LEVEL=INFO
```

---

## 🐧 Linux Installation

### Step 1: Update System
```bash
# For Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# For CentOS/RHEL
sudo yum update -y

# For Fedora
sudo dnf update -y
```

### Step 2: Install Python and Development Tools
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv git build-essential -y

# CentOS/RHEL
sudo yum install python3 python3-pip git gcc -y

# Fedora
sudo dnf install python3 python3-pip python3-venv git gcc -y
```

### Step 3: Clone and Setup ZombieCoder
```bash
# Clone the repository
git clone <repository-url>
cd zombiecoder

# Create virtual environment
python3 -m venv zombie_env

# Activate virtual environment
source zombie_env/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies
```bash
# Install core dependencies
pip install fastapi uvicorn aiohttp pyyaml

# Install AI/ML dependencies
pip install chromadb redis sentence-transformers

# Install monitoring dependencies
pip install prometheus-client

# Install system dependencies
sudo apt install python3-dev -y  # Ubuntu/Debian
# or
sudo yum install python3-devel -y  # CentOS/RHEL
```

### Step 5: Install Redis
```bash
# Ubuntu/Debian
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis

# CentOS/RHEL
sudo yum install redis -y
sudo systemctl start redis
sudo systemctl enable redis

# Verify Redis is running
redis-cli ping
```

### Step 6: Configure Environment Variables
```bash
# Create .env file
cat > .env << EOF
# OpenAI API Key (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging Level
LOG_LEVEL=INFO
EOF

# Set proper permissions
chmod 600 .env
```

---

## ⚙️ Configuration Setup

### Step 1: Verify Configuration Files
Ensure these configuration files exist in `./config/`:
- `config.yaml` - Main system configuration
- `registry.yaml` - Agent registry
- `personality.yaml` - Agent personalities

### Step 2: Create Required Directories
```bash
# Create necessary directories
mkdir -p logs data workspace

# Set proper permissions
chmod 755 logs data workspace
```

### Step 3: Test Configuration
```bash
# Test Python import
python -c "
import sys
sys.path.append('./server')
from core import AgentWorkstation
print('✓ Core modules imported successfully')
"
```

---

## 🚀 Running the System

### Method 1: Direct Python Execution
```bash
# Navigate to server directory
cd server

# Run the server
python main.py
```

### Method 2: Using Uvicorn
```bash
# Install uvicorn if not already installed
pip install uvicorn

# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Using the Provided Script
```bash
# Make the script executable (Linux/macOS)
chmod +x scripts/start_server.sh

# Run the script
./scripts/start_server.sh
```

### Access the System
Once running, access:
- **Main Dashboard:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Prometheus Metrics:** http://localhost:8000/metrics
- **System Status:** http://localhost:8000/api/status

---

## 📚 API Documentation

### Chat Endpoint
```bash
curl -X POST "http://localhost:8000/api/chat" \\
     -H "Content-Type: application/json" \\
     -d '{
       "input": "Explain what a function is in Python",
       "agent_id": "virtual_sir",
       "session_id": "test_session"
     }'
```

### Status Endpoint
```bash
curl -X GET "http://localhost:8000/api/status"
```

### Agents Endpoint
```bash
curl -X GET "http://localhost:8000/api/agents"
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = function(event) {
    console.log('Received:', event.data);
};
ws.send('Hello, ZombieCoder!');
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Python Module Not Found
**Error:** `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows
zombie_env\\Scripts\\activate

# Linux/macOS
source zombie_env/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Redis Connection Failed
**Error:** `Connection refused to Redis`

**Solution:**
```bash
# Install and start Redis
sudo apt install redis-server  # Ubuntu
sudo systemctl start redis
sudo systemctl enable redis

# Or run without Redis (set in config.yaml)
# Set cache.enabled: false
```

#### 3. Port Already in Use
**Error:** `Port 8000 is already in use`

**Solution:**
```bash
# Find process using port 8000
netstat -tulpn | grep :8000

# Kill the process
sudo kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

#### 4. Permission Denied
**Error:** `Permission denied: './logs'`

**Solution:**
```bash
# Create directories with proper permissions
mkdir -p logs data workspace
chmod 755 logs data workspace
```

#### 5. API Key Issues
**Error:** `Invalid API key`

**Solution:**
1. Check `.env` file for correct API keys
2. Ensure API keys have sufficient credits
3. Verify environment variables are loaded

### Debug Mode
Enable debug mode for detailed error messages:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Log Files
Check log files for errors:
```bash
# View main log
tail -f logs/zombiecoder.log

# View recent errors
grep ERROR logs/zombiecoder.log
```

---

## 🔐 Security Configuration

### 1. API Key Security
```bash
# Set proper file permissions
chmod 600 .env

# Never commit .env to version control
echo ".env" >> .gitignore
```

### 2. Network Security
```yaml
# In config.yaml, restrict access
server:
  host: "127.0.0.1"  # Local access only
  # host: "0.0.0.0"   # Network access (use with caution)
```

### 3. Tool Restrictions
```yaml
# In config.yaml, restrict dangerous tools
tools:
  restricted_tools:
    - "system_modify"
    - "network_admin"
    - "database_admin"
```

---

## 🐳 Docker Installation (Optional)

### Step 1: Install Docker
```bash
# Ubuntu
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
```

### Step 2: Build Docker Image
```bash
# Build the image
docker build -t zombiecoder-ai .

# Run with docker-compose
docker-compose up -d
```

### Step 3: Docker Compose Configuration
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  zombiecoder:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - LOG_LEVEL=INFO
      - REDIS_HOST=redis
    depends_on:
      - redis

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

## 📈 Performance Optimization

### 1. Memory Optimization
```yaml
# In config.yaml
cache:
  local:
    max_size: 500  # Reduce cache size
    ttl: 900       # Shorter TTL
```

### 2. Model Optimization
```yaml
# Use smaller models for faster response
models:
  providers:
    openai:
      models:
        - "gpt-3.5-turbo"  # Faster than GPT-4
      max_tokens: 2048     # Reduce token limit
```

### 3. Concurrent Request Handling
```yaml
# Increase concurrent agents
agents:
  max_concurrent_agents: 10
  agent_timeout: 30
```

---

## 🔄 Maintenance

### Daily Tasks
```bash
# Check system status
curl -s http://localhost:8000/api/status | jq .

# Check logs for errors
tail -n 100 logs/zombiecoder.log | grep ERROR

# Monitor resource usage
htop
df -h
```

### Weekly Tasks
```bash
# Clean old logs
find logs/ -name "*.log" -mtime +7 -delete

# Update dependencies
pip list --outdated
pip install --upgrade package-name

# Backup configuration
cp -r config/ config_backup_$(date +%Y%m%d)/
```

---

## 📞 Support

### Getting Help
1. **Documentation:** Check this guide first
2. **Logs:** Review `logs/zombiecoder.log`
3. **Status:** Check `/api/status` endpoint
4. **Community:** Join our Discord/Telegram group
5. **Email:** support@zombiecoder.my.id

### Reporting Issues
When reporting issues, include:
- Operating system and version
- Python version
- Error messages from logs
- Configuration used
- Steps to reproduce

---

## 🎯 Next Steps

After successful installation:

1. **Explore Agents:** Try both Virtual Sir and Coding Agent
2. **Customize Configuration:** Modify `config.yaml` for your needs
3. **Add Custom Tools:** Create your own tools in `server/tools/`
4. **Integrate APIs:** Connect to external services
5. **Scale Up:** Deploy to production environment

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

**🎉 Congratulations! You have successfully installed ZombieCoder Local AI!**

The system is now ready to use. Visit http://localhost:8000 to start using your AI agents.

*"যেখানে কোড ও কথা বলে" - Where code and conversation meet.*# Zombie-Coder-Workstation
