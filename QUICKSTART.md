# 🚀 Quick Start Guide - ZombieCoder Local AI

## 🎯 Quick Setup (5 Minutes)

### For Linux/macOS Users:
```bash
# 1. Navigate to zombiecoder directory
cd zombiecoder

# 2. Run the startup script
./scripts/start_server.sh

# 3. Open your browser and go to:
http://localhost:8000
```

### For Windows Users:
```cmd
# 1. Navigate to zombiecoder directory
cd zombiecoder

# 2. Run the startup script
scripts\\start_server.bat

# 3. Open your browser and go to:
http://localhost:8000
```

## 🔧 Manual Setup

### Step 1: Install Dependencies
```bash
# Create virtual environment
python3 -m venv zombie_env

# Activate (Linux/macOS)
source zombie_env/bin/activate

# Activate (Windows)
zombie_env\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start Server
```bash
cd server
python main.py
```

### Step 3: Access Dashboard
- **Main Interface:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **System Status:** http://localhost:8000/api/status

## 🤖 Available Agents

### 1. Virtual Sir (Teaching Agent)
- **Purpose:** Educational assistance and concept explanation
- **Specialties:** Programming fundamentals, step-by-step learning
- **Tools:** Code analysis, documentation lookup, web search

### 2. Coding Agent (Development Assistant)
- **Purpose:** Code generation, debugging, and development tasks
- **Specialties:** Multiple programming languages, system analysis
- **Tools:** File operations, terminal commands, code review

## 📱 Usage Examples

### Chat with Virtual Sir:
```
Input: "Explain what a function is in Python"
Response: Step-by-step explanation with examples and practice suggestions
```

### Chat with Coding Agent:
```
Input: "Create a Python function to sort a list"
Response: Working code with error handling and best practices
```

## 🔐 Configuration

### Environment Variables (.env file):
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
LOG_LEVEL=INFO
```

### Key Configuration Files:
- `config/config.yaml` - Main system configuration
- `config/registry.yaml` - Agent definitions
- `config/personality.yaml` - Agent behaviors

## 🐳 Docker Setup (Optional)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access services
# Main App: http://localhost:8000
# Grafana: http://localhost:3001 (admin/admin123)
# Prometheus: http://localhost:9090
```

## 📊 Monitoring

### System Metrics:
- Total requests and success rate
- Average response time
- Active sessions
- Agent performance

### Access Points:
- **Web Dashboard:** Built-in metrics display
- **Prometheus:** http://localhost:9090/metrics
- **Grafana:** http://localhost:3001 (if using Docker)

## 🛠️ Troubleshooting

### Common Issues:
1. **Port 8000 in use:** Change port in main.py
2. **Redis connection:** Install Redis or disable in config
3. **Module not found:** Activate virtual environment
4. **Permission denied:** Check file permissions

### Get Help:
```bash
# Check logs
tail -f logs/zombiecoder.log

# Check system status
curl http://localhost:8000/api/status

# View detailed errors
grep ERROR logs/zombiecoder.log
```

## 🎯 Next Steps

1. **Explore Features:** Try both agents with different queries
2. **Customize:** Modify configuration files for your needs
3. **Extend:** Add custom tools and agents
4. **Deploy:** Set up as system service for auto-start

---

**🎉 Congratulations! Your ZombieCoder Local AI is ready!**

*"যেখানে কোড ও কথা বলে" - Where code and conversation meet.*

For detailed documentation, see [README.md](README.md)