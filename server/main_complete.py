"""
Enhanced Main Server - Complete ZombieCoder Local AI Integration
Integrates all components: database, cache, security, monitoring, mini services
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import json
from datetime import datetime

# Add server directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import all components
from server.core import AgentWorkstation, create_workstation
from server.database import create_database_manager, create_chroma_manager
from server.cache import create_cache_manager, generate_query_hash
from server.security import create_security_manager
from server.environment import create_environment_manager
from server.monitoring import MetricsCollector
from server.proxy import create_proxy_server

from mini_services import create_chat_service, create_monitoring_service, create_rag_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/zombiecoder.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global variables
workstation: Optional[AgentWorkstation] = None
env_manager: Optional = None
security_manager: Optional = None
cache_manager: Optional = None
db_manager: Optional = None
chroma_manager: Optional = None
metrics_collector: Optional[MetricsCollector] = None
proxy_server: Optional = None

# Mini services
chat_service: Optional = None
monitoring_service: Optional = None
rag_service: Optional = None

# FastAPI app
app = FastAPI(
    title="ZombieCoder Local AI - Complete System",
    description="Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize complete ZombieCoder system"""
    global workstation, env_manager, security_manager, cache_manager
    global db_manager, chroma_manager, metrics_collector
    global proxy_server, chat_service, monitoring_service, rag_service
    
    logger.info("🧠 Starting Complete ZombieCoder Local AI System...")
    logger.info("Agent Workstation Layer - 'যেখানে কোড ও কথা বলে'")
    
    try:
        # Ensure directories exist
        os.makedirs("./logs", exist_ok=True)
        os.makedirs("./data", exist_ok=True)
        os.makedirs("./workspace", exist_ok=True)
        
        # 1. Initialize Environment Manager
        logger.info("🔧 Initializing Environment Manager...")
        env_manager = create_environment_manager()
        await env_manager.initialize()
        config = env_manager.get_config()
        
        # 2. Initialize Security Manager
        logger.info("🔐 Initializing Security Manager...")
        security_config = env_manager.get_security_config()
        security_manager = create_security_manager()
        await security_manager.initialize()
        
        # 3. Initialize Cache Manager
        logger.info("💾 Initializing Cache Manager...")
        cache_config = {
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'default_ttl': config.cache_ttl
        }
        cache_manager = create_cache_manager(cache_config)
        
        # 4. Initialize Database Layer
        logger.info("🗄️ Initializing Database Layer...")
        db_config = env_manager.get_database_config()
        db_manager = await create_database_manager(db_config.get('url', './data/zombiecoder.db'))
        chroma_manager = await create_chroma_manager(
            db_config.get('chroma_path', './data/chroma'),
            'zombiecoder_knowledge'
        )
        
        # 5. Initialize Metrics Collector
        logger.info("📊 Initializing Metrics Collector...")
        monitoring_config = {
            'prometheus': {'enabled': True, 'port': 9090},
            'logging': {'level': config.log_level}
        }
        metrics_collector = MetricsCollector(monitoring_config)
        await metrics_collector.initialize()
        
        # 6. Initialize Mini Services
        logger.info("🔧 Initializing Mini Services...")
        server_config = env_manager.get_server_config()
        
        chat_service = await create_chat_service(server_config.get('chat_service_port', 3003))
        monitoring_service = await create_monitoring_service(server_config.get('monitoring_service_port', 3002))
        rag_service = await create_rag_service(server_config.get('rag_service_port', 3001))
        
        # 7. Initialize Proxy Server
        logger.info("🌐 Initializing Proxy Server...")
        proxy_server = create_proxy_server(
            server_config.get('proxy_host', '0.0.0.0'),
            server_config.get('proxy_port', 3000)
        )
        
        # 8. Initialize Main Workstation
        logger.info("🧠 Initializing Agent Workstation...")
        workstation = await create_workstation()
        
        # Start mini services in background
        asyncio.create_task(chat_service.start())
        asyncio.create_task(monitoring_service.start())
        asyncio.create_task(rag_service.start())
        asyncio.create_task(proxy_server.start())
        
        logger.info("✅ Complete ZombieCoder Local AI System Started Successfully!")
        logger.info("🚀 All services are running")
        logger.info(f"📊 Dashboard: http://localhost:{server_config.get('port', 8000)}")
        logger.info(f"🌐 Proxy Server: http://localhost:{server_config.get('proxy_port', 3000)}")
        logger.info(f"💬 Chat Service: http://localhost:{server_config.get('chat_service_port', 3003)}")
        logger.info(f"📈 Monitoring: http://localhost:{server_config.get('monitoring_service_port', 3002)}")
        logger.info(f"📚 RAG Service: http://localhost:{server_config.get('rag_service_port', 3001)}")
        
    except Exception as e:
        logger.error(f"❌ Failed to start ZombieCoder system: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown complete ZombieCoder system"""
    global workstation, env_manager, security_manager, cache_manager
    global db_manager, chroma_manager, metrics_collector
    global proxy_server, chat_service, monitoring_service, rag_service
    
    logger.info("🛑 Shutting Down Complete ZombieCoder Local AI System...")
    
    try:
        if workstation:
            await workstation.shutdown()
        
        if proxy_server:
            await proxy_server.stop()
        
        if chat_service:
            await chat_service.stop()
        
        if monitoring_service:
            await monitoring_service.stop()
        
        if rag_service:
            await rag_service.stop()
        
        if cache_manager:
            await cache_manager.close()
        
        if db_manager:
            await db_manager.close()
        
        if chroma_manager:
            await chroma_manager.close()
        
        if metrics_collector:
            await metrics_collector.shutdown()
        
        logger.info("✅ Complete ZombieCoder Local AI System Shutdown Complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Enhanced main dashboard with complete system status"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧟‍♂️ ZombieCoder Local AI - Complete System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; color: #333; 
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { 
            background: white; border-radius: 15px; padding: 25px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
            transition: transform 0.3s ease, box-shadow 0.3s ease; 
        }
        .card:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.3); }
        .card h3 { color: #4a5568; margin-bottom: 15px; font-size: 1.4em; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-online { background-color: #48bb78; animation: pulse 2s infinite; }
        .status-offline { background-color: #f56565; }
        .status-warning { background-color: #ed8936; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        .service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .service-item { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .service-item h4 { margin-bottom: 8px; color: #2d3748; }
        .service-item p { color: #718096; font-size: 0.9em; }
        .chat-container { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .agent-selector { display: flex; gap: 10px; margin-bottom: 20px; }
        .agent-btn { 
            padding: 10px 20px; border: none; border-radius: 8px; 
            background: #667eea; color: white; cursor: pointer; 
            transition: background 0.3s ease; 
        }
        .agent-btn:hover { background: #5a6fd8; }
        .agent-btn.active { background: #764ba2; }
        .chat-messages { 
            height: 400px; overflow-y: auto; border: 1px solid #e2e8f0; 
            border-radius: 8px; padding: 15px; margin-bottom: 15px; 
            background: #f7fafc; 
        }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user-message { background: #e6fffa; border-left: 4px solid #38b2ac; }
        .agent-message { background: #f0fff4; border-left: 4px solid #48bb78; }
        .input-container { display: flex; gap: 10px; }
        .message-input { 
            flex: 1; padding: 12px; border: 1px solid #e2e8f0; 
            border-radius: 8px; font-size: 16px; 
        }
        .send-btn { 
            padding: 12px 24px; background: #48bb78; color: white; 
            border: none; border-radius: 8px; cursor: pointer; 
            transition: background 0.3s ease; 
        }
        .send-btn:hover { background: #38a169; }
        .loading { display: none; text-align: center; color: #718096; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 15px; }
        .stat-item { text-align: center; padding: 10px; background: #f7fafc; border-radius: 8px; }
        .stat-value { font-size: 1.5em; font-weight: bold; color: #4a5568; }
        .stat-label { font-size: 0.9em; color: #718096; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧟‍♂️ ZombieCoder Local AI</h1>
            <p>Complete Agent Workstation System - "যেখানে কোড ও কথা বলে"</p>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3><span class="status-indicator status-online"></span>Main System Status</h3>
                <div id="system-status">
                    <p><strong>Workstation:</strong> <span id="workstation-status">Initializing...</span></p>
                    <p><strong>Security:</strong> <span id="security-status">Initializing...</span></p>
                    <p><strong>Database:</strong> <span id="database-status">Initializing...</span></p>
                    <p><strong>Cache:</strong> <span id="cache-status">Initializing...</span></p>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="status-indicator status-online"></span>Mini Services</h3>
                <div class="service-grid">
                    <div class="service-item">
                        <h4>🌐 Proxy Server</h4>
                        <p id="proxy-status">Port 3000</p>
                    </div>
                    <div class="service-item">
                        <h4>💬 Chat Service</h4>
                        <p id="chat-service-status">Port 3003</p>
                    </div>
                    <div class="service-item">
                        <h4>📈 Monitoring</h4>
                        <p id="monitoring-status">Port 3002</p>
                    </div>
                    <div class="service-item">
                        <h4>📚 RAG Service</h4>
                        <p id="rag-status">Port 3001</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="status-indicator status-online"></span>Available Agents</h3>
                <div id="agents-list">
                    <p>Loading agents...</p>
                </div>
            </div>
            
            <div class="card">
                <h3><span class="status-indicator status-online"></span>System Metrics</h3>
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-value" id="total-requests">0</div>
                        <div class="stat-label">Total Requests</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="success-rate">0%</div>
                        <div class="stat-label">Success Rate</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="avg-response">0ms</div>
                        <div class="stat-label">Avg Response</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="cache-hit-rate">0%</div>
                        <div class="stat-label">Cache Hit Rate</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="active-sessions">0</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="chat-container">
            <h3>💬 Chat with Agents</h3>
            <div class="agent-selector">
                <button class="agent-btn active" data-agent="virtual_sir">Virtual Sir</button>
                <button class="agent-btn" data-agent="coding_agent">Coding Agent</button>
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message agent-message">
                    <strong>Virtual Sir:</strong> Hello! I'm Virtual Sir. How can I help you learn today?
                </div>
            </div>
            
            <div class="loading" id="loading">
                <p>🤔 Thinking...</p>
            </div>
            
            <div class="input-container">
                <input type="text" class="message-input" id="message-input" placeholder="Type your message here..." />
                <button class="send-btn" id="send-btn">Send</button>
            </div>
        </div>
    </div>

    <script>
        let currentAgent = 'virtual_sir';
        let sessionId = 'session_' + Date.now();
        
        // Agent selection
        document.querySelectorAll('.agent-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.agent-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentAgent = this.dataset.agent;
                
                const greeting = currentAgent === 'virtual_sir' 
                    ? 'Hello! I\\'m Virtual Sir. How can I help you learn today?'
                    : 'Ready to code! What development task can I help with?';
                
                addMessage('agent', greeting, currentAgent);
            });
        });
        
        // Send message
        document.getElementById('send-btn').addEventListener('click', sendMessage);
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        input: message,
                        agent_id: currentAgent,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage('agent', data.response.response, currentAgent);
                } else {
                    addMessage('agent', `Error: ${data.error}`, currentAgent);
                }
            } catch (error) {
                addMessage('agent', `Connection error: ${error.message}`, currentAgent);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function addMessage(type, content, agent = null) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            
            const agentName = agent === 'virtual_sir' ? 'Virtual Sir' : 'Coding Agent';
            const sender = type === 'user' ? 'You' : agentName;
            
            messageDiv.innerHTML = `<strong>${sender}:</strong> ${content}`;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Load system status
        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update system status
                document.getElementById('workstation-status').textContent = 
                    data.workstation?.initialized ? 'Online' : 'Offline';
                document.getElementById('security-status').textContent = 
                    data.security?.enabled ? 'Active' : 'Disabled';
                document.getElementById('database-status').textContent = 
                    data.database?.connected ? 'Connected' : 'Disconnected';
                document.getElementById('cache-status').textContent = 
                    data.cache?.connected ? 'Active' : 'Inactive';
                
                // Update agents list
                if (data.workstation?.agents?.agents) {
                    const agentsList = document.getElementById('agents-list');
                    agentsList.innerHTML = '';
                    
                    Object.entries(data.workstation.agents.agents).forEach(([id, info]) => {
                        const agentDiv = document.createElement('div');
                        agentDiv.innerHTML = `
                            <p><strong>${info.config?.display_name || id}</strong></p>
                            <p><small>${info.config?.description || 'No description'}</small></p>
                            <p><small>Status: ${info.agent_status?.is_initialized ? 'Active' : 'Inactive'}</small></p>
                        `;
                        agentsList.appendChild(agentDiv);
                    });
                }
                
                // Update metrics
                if (data.metrics) {
                    document.getElementById('total-requests').textContent = 
                        data.metrics.requests?.total || 0;
                    document.getElementById('success-rate').textContent = 
                        Math.round((1 - (data.metrics.requests?.error_rate || 0)) * 100) + '%';
                    document.getElementById('avg-response').textContent = 
                        Math.round((data.metrics.requests?.avg_response_time || 0) * 1000) + 'ms';
                    document.getElementById('cache-hit-rate').textContent = 
                        Math.round((data.metrics.cache?.hit_rate_percent || 0)) + '%';
                    document.getElementById('active-sessions').textContent = 
                        data.metrics.system?.active_sessions || 0;
                }
                
            } catch (error) {
                console.error('Error loading status:', error);
            }
        }
        
        // Initial load and periodic updates
        loadSystemStatus();
        setInterval(loadSystemStatus, 5000);
    </script>
</body>
</html>
    """)


@app.get("/api/status")
async def get_status():
    """Get complete system status"""
    global workstation, env_manager, security_manager, cache_manager
    global db_manager, chroma_manager, metrics_collector
    
    if not workstation:
        return JSONResponse(
            {"error": "System not initialized"},
            status_code=503
        )
    
    try:
        # Get workstation status
        agent_status = await workstation.get_agent_status()
        
        # Get metrics summary
        metrics_summary = {}
        if metrics_collector:
            metrics_summary = await metrics_collector.get_metrics_summary()
        
        # Get cache stats
        cache_stats = {}
        if cache_manager:
            cache_stats = await cache_manager.get_stats()
        
        # Get security stats
        security_stats = {}
        if security_manager:
            security_stats = security_manager.get_security_stats()
        
        # Get database stats
        database_stats = {
            'connected': db_manager is not None,
            'chroma_connected': chroma_manager is not None
        }
        
        return {
            "workstation": {
                "initialized": workstation.is_initialized,
                "agents": agent_status
            },
            "security": security_stats,
            "database": database_stats,
            "cache": cache_stats,
            "metrics": metrics_summary,
            "services": {
                "proxy_server": {"port": 3000, "status": "running"},
                "chat_service": {"port": 3003, "status": "running"},
                "monitoring_service": {"port": 3002, "status": "running"},
                "rag_service": {"port": 3001, "status": "running"}
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@app.post("/api/chat")
async def chat(request: dict):
    """Enhanced chat endpoint with complete integration"""
    global workstation, security_manager, cache_manager
    
    if not workstation:
        return JSONResponse(
            {"error": "System not initialized"},
            status_code=503
        )
    
    try:
        user_input = request.get('input', '')
        agent_id = request.get('agent_id', 'virtual_sir')
        session_id = request.get('session_id', 'default')
        
        if not user_input:
            return JSONResponse(
                {"error": "Input is required"},
                status_code=400
            )
        
        # Security validation
        if security_manager:
            is_valid, security_result = await security_manager.validate_request(
                user_input, session_id
            )
            
            if not is_valid:
                return JSONResponse({
                    "error": "Security validation failed",
                    "issues": security_result.get('issues', [])
                }, status_code=400)
            
            user_input = security_result.get('sanitized_content', user_input)
        
        # Check cache first
        query_hash = generate_query_hash(user_input, agent_id)
        cached_response = None
        
        if cache_manager:
            cached_response = await cache_manager.get_agent_response(agent_id, query_hash)
        
        if cached_response:
            logger.info(f"Cache hit for query: {query_hash[:8]}...")
            return {
                "success": True,
                "response": cached_response,
                "agent_id": agent_id,
                "session_id": session_id,
                "cached": True
            }
        
        # Process through workstation
        response = await workstation.process_request({
            'input': user_input,
            'agent_id': agent_id,
            'session_id': session_id,
            'tools_enabled': True
        })
        
        # Cache the response
        if cache_manager and response.get('success'):
            await cache_manager.cache_agent_response(
                agent_id, query_hash, response
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@app.get("/api/agents")
async def get_agents():
    """Get list of available agents"""
    global workstation
    
    if not workstation:
        return JSONResponse(
            {"error": "System not initialized"},
            status_code=503
        )
    
    try:
        agent_status = await workstation.get_agent_status()
        return agent_status
        
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    global metrics_collector
    
    if not metrics_collector:
        return JSONResponse(
            {"error": "Metrics not available"},
            status_code=503
        )
    
    try:
        metrics_summary = await metrics_collector.get_metrics_summary()
        return metrics_summary
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    global metrics_collector
    
    if not metrics_collector:
        return "# No metrics available\\n"
    
    try:
        metrics = await metrics_collector.get_prometheus_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting prometheus metrics: {e}")
        return "# Error getting metrics\\n"


@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check main components
    global workstation, env_manager, security_manager, cache_manager
    global db_manager, chroma_manager, metrics_collector
    
    health_status["services"]["workstation"] = {
        "status": "healthy" if workstation and workstation.is_initialized else "unhealthy"
    }
    
    health_status["services"]["security"] = {
        "status": "healthy" if security_manager else "unhealthy"
    }
    
    health_status["services"]["cache"] = {
        "status": "healthy" if cache_manager else "unhealthy"
    }
    
    health_status["services"]["database"] = {
        "status": "healthy" if db_manager and chroma_manager else "unhealthy"
    }
    
    health_status["services"]["metrics"] = {
        "status": "healthy" if metrics_collector else "unhealthy"
    }
    
    return JSONResponse(health_status)


if __name__ == "__main__":
    # Run complete server
    server_config = None
    if env_manager:
        server_config = env_manager.get_server_config()
    
    uvicorn.run(
        "main:app",
        host=server_config.get('host', '0.0.0.0') if server_config else '0.0.0.0',
        port=server_config.get('port', 8000) if server_config else 8000,
        reload=True,
        log_level="info"
    )