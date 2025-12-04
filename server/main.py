"""
Main ZombieCoder Server Application
FastAPI-based server for the Agent Workstation Layer
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
import yaml
import json
from datetime import datetime

# Add the server directory to Python path
sys.path.append(str(Path(__file__).parent))

from server.core import AgentWorkstation, create_workstation
from server.monitoring.metrics import MetricsCollector


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
metrics_collector: Optional[MetricsCollector] = None
app = FastAPI(
    title="ZombieCoder Local AI",
    description="Agent Workstation Layer for Local AI Development",
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

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global workstation, metrics_collector
    
    logger.info("Starting ZombieCoder Local AI Server...")
    
    try:
        # Ensure directories exist
        os.makedirs("./logs", exist_ok=True)
        os.makedirs("./data", exist_ok=True)
        
        # Initialize workstation
        config_path = "./config/config.yaml"
        if os.path.exists(config_path):
            workstation = await create_workstation(config_path)
            logger.info("Agent Workstation initialized successfully")
        else:
            logger.error(f"Configuration file not found: {config_path}")
            return
        
        # Get metrics collector
        if workstation:
            metrics_collector = workstation.metrics_collector
        
        logger.info("ZombieCoder Local AI Server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global workstation
    
    logger.info("Shutting down ZombieCoder Local AI Server...")
    
    if workstation:
        await workstation.shutdown()
    
    logger.info("Server shutdown complete")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard page"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZombieCoder Local AI - Agent Workstation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        
        .card h3 {
            color: #4a5568;
            margin-bottom: 15px;
            font-size: 1.4em;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online {
            background-color: #48bb78;
            animation: pulse 2s infinite;
        }
        
        .status-offline {
            background-color: #f56565;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .chat-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .agent-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .agent-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: #667eea;
            color: white;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .agent-btn:hover {
            background: #5a6fd8;
        }
        
        .agent-btn.active {
            background: #764ba2;
        }
        
        .chat-messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background: #f7fafc;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
        }
        
        .user-message {
            background: #e6fffa;
            border-left: 4px solid #38b2ac;
        }
        
        .agent-message {
            background: #f0fff4;
            border-left: 4px solid #48bb78;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        .message-input {
            flex: 1;
            padding: 12px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
        }
        
        .send-btn {
            padding: 12px 24px;
            background: #48bb78;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .send-btn:hover {
            background: #38a169;
        }
        
        .loading {
            display: none;
            text-align: center;
            color: #718096;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-item {
            text-align: center;
            padding: 10px;
            background: #f7fafc;
            border-radius: 8px;
        }
        
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #4a5568;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #718096;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 ZombieCoder Local AI</h1>
            <p>Agent Workstation Layer - "যেখানে কোড ও কথা বলে"</p>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3><span class="status-indicator status-online"></span>System Status</h3>
                <div id="system-status">
                    <p><strong>Workstation:</strong> <span id="workstation-status">Loading...</span></p>
                    <p><strong>Agents:</strong> <span id="agents-status">Loading...</span></p>
                    <p><strong>Models:</strong> <span id="models-status">Loading...</span></p>
                </div>
            </div>
            
            <div class="card">
                <h3>Available Agents</h3>
                <div id="agents-list">
                    <p>Loading agents...</p>
                </div>
            </div>
            
            <div class="card">
                <h3>System Metrics</h3>
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
                        <div class="stat-value" id="active-sessions">0</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="chat-container">
            <h3>Chat with Agents</h3>
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
                
                // Add greeting message
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
                
                document.getElementById('workstation-status').textContent = 
                    data.workstation?.initialized ? 'Online' : 'Offline';
                document.getElementById('agents-status').textContent = 
                    `${data.workstation?.agents?.total_agents || 0} agents`;
                document.getElementById('models-status').textContent = 
                    'Available';
                
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
                    document.getElementById('active-sessions').textContent = 
                        data.metrics.system?.active_requests || 0;
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
    """Get system status"""
    global workstation
    
    if not workstation:
        return JSONResponse(
            {"error": "Workstation not initialized"},
            status_code=503
        )
    
    try:
        # Get workstation status
        agent_status = await workstation.get_agent_status()
        
        # Get metrics summary
        metrics_summary = {}
        if workstation.metrics_collector:
            metrics_summary = await workstation.metrics_collector.get_metrics_summary()
        
        return {
            "workstation": {
                "initialized": workstation.is_initialized,
                "agents": agent_status
            },
            "metrics": metrics_summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@app.post("/api/chat")
async def chat(request: Dict[str, Any]):
    """Process chat request"""
    global workstation
    
    if not workstation:
        return JSONResponse(
            {"error": "Workstation not initialized"},
            status_code=503
        )
    
    try:
        user_input = request.get('input', '')
        agent_id = request.get('agent_id')
        session_id = request.get('session_id', 'default')
        
        if not user_input:
            return JSONResponse(
                {"error": "Input is required"},
                status_code=400
            )
        
        # Process request through workstation
        response = await workstation.process_request({
            'input': user_input,
            'agent_id': agent_id,
            'session_id': session_id,
            'tools_enabled': True
        })
        
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
            {"error": "Workstation not initialized"},
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
    global workstation
    
    if not workstation or not workstation.metrics_collector:
        return JSONResponse(
            {"error": "Metrics not available"},
            status_code=503
        )
    
    try:
        metrics_summary = await workstation.metrics_collector.get_metrics_summary()
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
    global workstation
    
    if not workstation or not workstation.metrics_collector:
        return "# No metrics available\\n"
    
    try:
        metrics = await workstation.metrics_collector.get_prometheus_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting prometheus metrics: {e}")
        return "# Error getting metrics\\n"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process the message and send back response
            await manager.send_personal_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )