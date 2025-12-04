# 🧟‍♂️ ZombieCoder Local AI - Complete Production System
## Agent Workstation Layer - "যেখানে কোড ও কথা বলে"

**🎯 MISSION ACCOMPLISHED - Complete Production-Ready System**

---

## 📋 **Table of Contents**
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Installation Guide](#installation-guide)
4. [Configuration](#configuration)
5. [Services](#services)
6. [Usage](#usage)
7. [API Documentation](#api-documentation)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Development](#development)

---

## 🏗️ **System Overview**

### **Complete Component Integration:**
✅ **Agent Workstation Layer** - Core orchestration  
✅ **Database Layer** - SQLite + ChromaDB integration  
✅ **Cache Layer** - Redis integration with intelligent caching  
✅ **Security Layer** - Comprehensive validation and protection  
✅ **Environment Manager** - Secure configuration and API key management  
✅ **Proxy Server** - WebSocket/REST bridge (Port 3000)  
✅ **Mini Services** - Separate services for scalability  
✅ **Monitoring System** - Prometheus + Grafana integration  
✅ **Production Agents** - Virtual Sir + Coding Agent  
✅ **Multi-Model Support** - OpenAI, Anthropic, Local models  

### **Production Features:**
🔐 **Security-First Design** - Multiple validation layers  
📊 **Real-Time Monitoring** - Comprehensive metrics  
🚀 **High Performance** - Intelligent caching and optimization  
🔧 **Easy Configuration** - Environment-based management  
🌐 **Scalable Architecture** - Microservices design  
💾 **Persistent Storage** - SQLite + ChromaDB  
🔄 **Smart Routing** - Automatic model fallback  

---

## 🏛️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                ZombieCoder Local AI System               │
├─────────────────────────────────────────────────────┤
│  Web Dashboard (Port 8000)                        │
│  ├─ Enhanced UI with real-time status               │
│  ├─ Agent selection and chat interface               │
│  └─ System metrics and monitoring                  │
├─────────────────────────────────────────────────────┤
│  Proxy Server (Port 3000)                         │
│  ├─ WebSocket/REST bridge                         │
│  ├─ Request routing and load balancing             │
│  └─ Service discovery and health checking           │
├─────────────────────────────────────────────────────┤
│  Mini Services Architecture                        │
│  ├─ Chat Service (Port 3003)                    │
│  ├─ Monitoring Service (Port 3002)                │
│  ├─ RAG Service (Port 3001)                      │
│  └─ Independent, scalable components             │
├─────────────────────────────────────────────────────┤
│  Agent Workstation Layer (Core)                   │
│  ├─ Virtual Sir (Teaching Agent)                │
│  ├─ Coding Agent (Development Assistant)           │
│  ├─ Model Router (Multi-provider support)        │
│  ├─ Tool Orchestrator (Secure execution)         │
│  ├─ RAG Pipeline (ChromaDB integration)       │
│  ├─ Security Manager (Validation & filtering)    │
│  └─ Metrics Collector (Prometheus integration)   │
├─────────────────────────────────────────────────────┤
│  Data Layer                                         │
│  ├─ SQLite (Sessions, Metrics, Metadata)           │
│  ├─ ChromaDB (Vector storage for RAG)            │
│  ├─ Redis (Caching and session storage)           │
│  └─ File System (Logs, Data, Workspace)        │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 **Installation Guide**

### **System Requirements:**
- **RAM:** 8GB+ (16GB recommended)
- **Storage:** 20GB+ free space
- **Python:** 3.8+ (3.11+ recommended)
- **Redis:** 5.0+ (for caching)
- **OS:** Windows 10/11, Ubuntu 18.04+, macOS 10.15+

### **Quick Start (5 Minutes):**

#### **Linux/macOS:**
```bash
# Clone and navigate to zombiecoder directory
cd zombiecoder

# Run complete production startup script
chmod +x scripts/start_complete.sh
./scripts/start_complete.sh

# System will be available at:
# Main Dashboard: http://localhost:8000
# Proxy Server: http://localhost:3000
# Mini Services: Ports 3001, 3002, 3003
```

#### **Windows:**
```cmd
# Navigate to zombiecoder directory
cd zombiecoder

# Run complete production startup script
scripts\start_complete.bat

# System will be available at:
# Main Dashboard: http://localhost:8000
# Proxy Server: http://localhost:3000
# Mini Services: Ports 3001, 3002, 3003
```

### **Manual Installation:**
```bash
# 1. Create virtual environment
python3 -m venv zombie_env
source zombie_env/bin/activate  # Linux/macOS
# zombie_env\Scripts\activate.bat  # Windows

# 2. Install complete dependencies
pip install -r requirements.txt

# 3. Create environment file (.env)
cp config/config.yaml.example config/config.yaml
# Edit with your API keys and settings

# 4. Start complete system
python server/main_complete.py
```

---

## ⚙️ **Configuration**

### **Environment Variables (.env):**
```env
# Production Environment
ZOMBIECODER_ENV=production
ZOMBIECODER_DEBUG=false
ZOMBIECODER_LOG_LEVEL=INFO

# Security
ZOMBIECODER_SECRET_KEY=your-secret-key-here
ZOMBIECODER_SESSION_TIMEOUT=1800

# Database
ZOMBIECODER_DATABASE_URL=sqlite:///data/zombiecoder.db
ZOMBIECODER_REDIS_URL=redis://localhost:6379/0
ZOMBIECODER_CHROMA_PATH=./data/chroma

# API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Server Configuration
ZOMBIECODER_HOST=0.0.0.0
ZOMBIECODER_PORT=8000
ZOMBIECODER_PROXY_PORT=3000
```

### **Configuration Files:**
- `config/config.yaml` - Main system configuration
- `config/registry.yaml` - Agent definitions and routing
- `config/personality.yaml` - Agent personalities and behaviors
- `config/config.production.yaml` - Production overrides
- `config/config.local.yaml` - Local development overrides

---

## 🌐 **Services**

### **Main Services:**
| Service | Port | Description | Status |
|---------|------|-------------|--------|
| Main Dashboard | 8000 | Primary web interface | ✅ Running |
| Proxy Server | 3000 | WebSocket/REST bridge | ✅ Running |
| API Documentation | 8000/docs | Interactive API docs | ✅ Available |

### **Mini Services:**
| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| Chat Service | 3003 | Real-time chat handling | `/health` |
| Monitoring Service | 3002 | Metrics and alerts | `/health` |
| RAG Service | 3001 | Document retrieval | `/health` |

### **Service Management:**
```bash
# Check all services status
./scripts/start_complete.sh health

# View system status
./scripts/start_complete.sh status

# Restart services
./scripts/start_complete.sh restart

# Stop all services
./scripts/start_complete.sh stop
```

---

## 💬 **Usage**

### **Web Dashboard:**
1. **Agent Selection:** Choose between Virtual Sir and Coding Agent
2. **Real-time Chat:** Interactive conversation with both agents
3. **System Monitoring:** Live metrics and service status
4. **Configuration:** Easy access to all system settings

### **API Usage:**
```bash
# Chat with Virtual Sir
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "Explain machine learning",
       "agent_id": "virtual_sir",
       "session_id": "user_session_123"
     }'

# Chat with Coding Agent
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "Create a Python sorting algorithm",
       "agent_id": "coding_agent",
       "session_id": "dev_session_456"
     }'

# Get system status
curl -X GET "http://localhost:8000/api/status"

# Get available agents
curl -X GET "http://localhost:8000/api/agents"

# Get metrics
curl -X GET "http://localhost:8000/api/metrics"
```

### **Agent Capabilities:**

#### **Virtual Sir (Teaching Agent):**
- ✅ Step-by-step explanations
- ✅ Learning style adaptation
- ✅ Educational content filtering
- ✅ Practice exercises and suggestions
- ✅ Encouragement and feedback
- ✅ Safe, educational-only responses

#### **Coding Agent (Development Assistant):**
- ✅ Multi-language code generation
- ✅ Debugging and troubleshooting
- ✅ Code review and optimization
- ✅ File operations and terminal access
- ✅ Security-focused coding practices
- ✅ Best practices and documentation

---

## 📚 **API Documentation**

### **Authentication:**
All API requests include session management and security validation.

### **Endpoints:**

#### **Chat API:**
```http
POST /api/chat
Content-Type: application/json

{
  "input": "Your message here",
  "agent_id": "virtual_sir | coding_agent",
  "session_id": "unique_session_id",
  "tools_enabled": true
}

Response:
{
  "success": true,
  "response": {
    "response": "Agent response here",
    "agent_name": "Virtual Sir",
    "session_id": "unique_session_id",
    "tools_used": ["code_analyzer"],
    "cached": false
  }
}
```

#### **Status API:**
```http
GET /api/status

Response:
{
  "workstation": {
    "initialized": true,
    "agents": { ... }
  },
  "security": { ... },
  "database": { ... },
  "cache": { ... },
  "metrics": { ... },
  "services": { ... }
}
```

#### **Health Check:**
```http
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "workstation": { "status": "healthy" },
    "security": { "status": "healthy" },
    "cache": { "status": "healthy" }
  }
}
```

---

## 📊 **Monitoring**

### **Built-in Metrics:**
- **Request Metrics:** Total, success rate, error rate
- **Performance Metrics:** Response time, throughput
- **Agent Metrics:** Usage per agent, tool usage
- **Cache Metrics:** Hit rate, memory usage
- **System Metrics:** CPU, memory, disk usage

### **Prometheus Integration:**
```bash
# Metrics endpoint
curl http://localhost:8000/metrics

# Grafana dashboard (if using Docker)
http://localhost:3001 (admin/admin123)
```

### **Real-time Dashboard:**
- 📈 **Live Request Counter**
- 🎯 **Success Rate Display**
- ⚡ **Average Response Time**
- 💾 **Cache Hit Rate**
- 👥 **Active Sessions**
- 🤖 **Agent Status Overview**

---

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **Port Conflicts:**
```bash
# Check what's using ports
netstat -tlnp | grep -E ":(8000|3000|3001|3002|3003)"

# Kill conflicting processes
sudo kill -9 <PID>

# Or use different ports in config
export ZOMBIECODER_PORT=8080
export ZOMBIECODER_PROXY_PORT=3001
```

#### **Redis Connection:**
```bash
# Check Redis status
redis-cli ping

# Start Redis
sudo systemctl start redis-server

# Install Redis (Ubuntu)
sudo apt update && sudo apt install redis-server

# Install Redis (macOS)
brew install redis
brew services start redis
```

#### **Python Dependencies:**
```bash
# Reinstall all dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Check for broken packages
pip check

# Upgrade specific packages
pip install --upgrade chromadb redis
```

#### **Permission Issues:**
```bash
# Fix directory permissions
chmod 755 logs data workspace
chmod 600 config/config.yaml

# Fix script permissions
chmod +x scripts/start_complete.sh
```

### **Debug Mode:**
```bash
# Enable debug logging
export ZOMBIECODER_DEBUG=true
export ZOMBIECODER_LOG_LEVEL=DEBUG

# Run with verbose output
python server/main_complete.py --verbose
```

### **Log Analysis:**
```bash
# View main log
tail -f logs/zombiecoder.log

# Search for errors
grep ERROR logs/zombiecoder.log

# Monitor in real-time
tail -f logs/zombiecoder.log | grep ERROR
```

---

## 🛠️ **Development**

### **Project Structure:**
```
zombiecoder/
├── config/                 # Configuration files
├── server/                 # Main application
│   ├── core/            # Agent workstation core
│   ├── agents/           # Agent implementations
│   ├── routing/         # Model routing
│   ├── tools/           # Tool orchestration
│   ├── rag/             # RAG pipeline
│   ├── database/        # Database layer
│   ├── cache/           # Cache management
│   ├── security/        # Security layer
│   ├── environment/     # Environment management
│   ├── monitoring/      # Metrics collection
│   └── proxy/           # Proxy server
├── mini-services/         # Microservices
│   ├── chat-service/    # Real-time chat
│   ├── monitoring-service/ # System monitoring
│   └── rag-service/     # Document retrieval
├── scripts/              # Startup and utility scripts
├── logs/                 # Application logs
├── data/                 # Database and cache files
└── workspace/            # Working directory
```

### **Adding New Agents:**
1. Create agent class in `server/agents/`
2. Add personality in `config/personality.yaml`
3. Register in `config/registry.yaml`
4. Implement in `server/core/agent_manager.py`

### **Adding New Tools:**
1. Create tool class in `server/tools/`
2. Add to `server/tools/tool_orchestrator.py`
3. Configure permissions in agent personality
4. Test with security validation

### **Custom Configuration:**
```yaml
# config/config.custom.yaml
agents:
  custom_agent:
    display_name: "My Custom Agent"
    description: "Specialized for my use case"
    
models:
  custom_provider:
    base_url: "https://my-api.com"
    models: ["my-custom-model"]
```

---

## 🎯 **Production Deployment**

### **Docker Deployment:**
```bash
# Build and run complete stack
docker-compose up -d

# Scale services
docker-compose up -d --scale chat-service=2

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **System Service Installation:**
```bash
# Install as system service (Linux)
sudo ./scripts/install_service.sh

# Manage service
sudo systemctl start zombiecoder
sudo systemctl stop zombiecoder
sudo systemctl enable zombiecoder  # Auto-start on boot
sudo systemctl status zombiecoder
```

### **Performance Optimization:**
```yaml
# High-performance configuration
cache:
  redis:
    max_connections: 20
    connection_timeout: 1
    
agents:
  max_concurrent_agents: 10
  agent_timeout: 30
  
models:
  routing:
    cache_responses: true
    parallel_requests: true
```

---

## 🔐 **Security Best Practices**

### **Production Security:**
1. **Environment Variables:** Never commit API keys
2. **Network Security:** Use HTTPS in production
3. **Input Validation:** All inputs are validated
4. **Rate Limiting:** Configurable per client
5. **Session Security:** Timeout-based invalidation
6. **File Access:** Restricted to safe directories
7. **Content Filtering:** Multi-layer validation
8. **Audit Logging:** All actions are logged

### **Monitoring Security:**
- 🚨 **Alert System:** Real-time security alerts
- 📊 **Access Logs:** Complete audit trail
- 🔍 **Threat Detection:** Pattern-based analysis
- 🛡️ **Firewall Rules:** Network protection

---

## 📈 **Scaling Guide**

### **Horizontal Scaling:**
```yaml
# Multiple instances
instances:
  - host: "192.168.1.10" port: 8000
  - host: "192.168.1.11" port: 8000
  - host: "192.168.1.12" port: 8000

load_balancer:
  algorithm: "round_robin"
  health_check: "/api/health"
```

### **Vertical Scaling:**
```yaml
# Resource allocation
resources:
  main_server:
    cpu: "2 cores"
    memory: "4GB"
    
  mini_services:
    cpu: "1 core each"
    memory: "1GB each"
```

---

## 🎉 **Success! Complete Production System**

### **What You Have:**
✅ **Full ZombieCoder System** - All components integrated  
✅ **Production-Ready** - Security, monitoring, scaling  
✅ **Easy Installation** - One-command setup  
✅ **Comprehensive Documentation** - Complete guides  
✅ **Multi-Service Architecture** - Scalable and resilient  
✅ **Real Agents** - Virtual Sir + Coding Agent  
✅ **Professional UI** - Modern, responsive dashboard  
✅ **API Integration** - RESTful + WebSocket  
✅ **Monitoring** - Prometheus + Grafana  
✅ **Security** - Multi-layer protection  
✅ **Caching** - Redis integration  
✅ **Database** - SQLite + ChromaDB  

### **Access Points:**
- **Main Dashboard:** http://localhost:8000
- **Proxy Server:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health
- **Metrics:** http://localhost:8000/metrics

---

**🧟‍♂️ ZombieCoder Local AI - Complete Production System**  
**"যেখানে কোড ও কথা বলে" - Where code and conversation meet**

**🚀 READY FOR PRODUCTION DEPLOYMENT! 🚀**

---

*For support, contact: Developer Zone - +880 1323-626282*  
*Website: https://zombiecoder.my.id/*