"""
Proxy Server - ZombieCoder Local AI
WebSocket/REST Bridge for Mini Services
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import websockets
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a registered service"""
    name: str
    url: str
    websocket_url: Optional[str]
    health_url: str
    status: str = "unknown"
    last_check: Optional[datetime] = None


class ProxyServer:
    """WebSocket/REST proxy server for bridging services"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 3000):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="ZombieCoder Proxy Server",
            description="WebSocket/REST Bridge for Mini Services"
        )
        self.services: Dict[str, ServiceInfo] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.running = False
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.on_event("startup")
        async def startup_event():
            await self._initialize()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self._cleanup()
        
        @self.app.get("/")
        async def root():
            return {
                "message": "🧟‍♂️ ZombieCoder Proxy Server",
                "status": "running",
                "services": {name: info.__dict__ for name, info in self.services.items()},
                "websocket_connections": len(self.websocket_connections)
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            service_health = {}
            for name, service in self.services.items():
                service_health[name] = {
                    "status": service.status,
                    "last_check": service.last_check.isoformat() if service.last_check else None
                }
            
            return {
                "status": "healthy" if all(s.status == "healthy" for s in self.services.values()) else "degraded",
                "services": service_health,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/services")
        async def list_services():
            """List all registered services"""
            return {name: info.__dict__ for name, info in self.services.items()}
        
        @self.app.post("/proxy/{service_name}/{endpoint:path}")
        async def proxy_rest_request(service_name: str, endpoint: str, request: Dict[str, Any]):
            """Proxy REST requests to services"""
            if service_name not in self.services:
                raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
            
            service = self.services[service_name]
            target_url = f"{service.url}/{endpoint}"
            
            try:
                if not self.http_session:
                    self.http_session = aiohttp.ClientSession()
                
                async with self.http_session.request(
                    "POST", target_url, json=request
                ) as response:
                    response_data = await response.json()
                    return response_data
                    
            except Exception as e:
                logger.error(f"Error proxying request to {service_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws/{service_name}")
        async def websocket_proxy(websocket: WebSocket, service_name: str):
            """WebSocket proxy for real-time communication"""
            if service_name not in self.services:
                await websocket.close(code=4004, reason=f"Service {service_name} not found")
                return
            
            service = self.services[service_name]
            if not service.websocket_url:
                await websocket.close(code=4005, reason=f"Service {service_name} doesn't support WebSocket")
                return
            
            # Accept the WebSocket connection
            await websocket.accept()
            connection_id = f"{service_name}_{id(websocket)}"
            self.websocket_connections[connection_id] = websocket
            
            try:
                # Connect to the target service
                async with websockets.connect(service.websocket_url) as target_ws:
                    # Forward messages in both directions
                    async def forward_to_target():
                        try:
                            while True:
                                data = await websocket.receive_text()
                                await target_ws.send(data)
                        except Exception as e:
                            logger.error(f"Error forwarding to target: {e}")
                    
                    async def forward_to_client():
                        try:
                            while True:
                                data = await target_ws.recv()
                                await websocket.send_text(data)
                        except Exception as e:
                            logger.error(f"Error forwarding to client: {e}")
                    
                    # Run both forwarders concurrently
                    await asyncio.gather(
                        forward_to_target(),
                        forward_to_client(),
                        return_exceptions=True
                    )
                    
            except Exception as e:
                logger.error(f"WebSocket proxy error for {service_name}: {e}")
            finally:
                # Clean up connection
                if connection_id in self.websocket_connections:
                    del self.websocket_connections[connection_id]
                await websocket.close()
    
    async def _initialize(self):
        """Initialize proxy server"""
        # Register default services
        await self._register_default_services()
        
        # Start health check loop
        asyncio.create_task(self._health_check_loop())
        
        self.running = True
        logger.info(f"🌐 Proxy server initialized on {self.host}:{self.port}")
    
    async def _register_default_services(self):
        """Register default mini services"""
        default_services = {
            "chat": ServiceInfo(
                name="chat",
                url="http://localhost:3003",
                websocket_url="ws://localhost:3003/ws",
                health_url="http://localhost:3003/health"
            ),
            "monitoring": ServiceInfo(
                name="monitoring",
                url="http://localhost:3002",
                websocket_url=None,
                health_url="http://localhost:3002/health"
            ),
            "rag": ServiceInfo(
                name="rag",
                url="http://localhost:3001",
                websocket_url="ws://localhost:3001/ws",
                health_url="http://localhost:3001/health"
            )
        }
        
        self.services.update(default_services)
        logger.info("📝 Registered default services")
    
    async def register_service(self, name: str, url: str, websocket_url: Optional[str] = None, health_url: Optional[str] = None):
        """Register a new service"""
        service_info = ServiceInfo(
            name=name,
            url=url,
            websocket_url=websocket_url,
            health_url=health_url or f"{url}/health"
        )
        
        self.services[name] = service_info
        logger.info(f"📝 Registered service: {name} -> {url}")
    
    async def _health_check_loop(self):
        """Periodic health check for services"""
        while self.running:
            try:
                await self._check_service_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(30)
    
    async def _check_service_health(self):
        """Check health of all registered services"""
        if not self.http_session:
            self.http_session = aiohttp.ClientSession()
        
        for service_name, service in self.services.items():
            try:
                async with self.http_session.get(service.health_url, timeout=5) as response:
                    if response.status == 200:
                        service.status = "healthy"
                    else:
                        service.status = "unhealthy"
            except Exception as e:
                logger.warning(f"Health check failed for {service_name}: {e}")
                service.status = "unhealthy"
            
            service.last_check = datetime.now()
    
    async def _cleanup(self):
        """Cleanup resources"""
        self.running = False
        
        if self.http_session:
            await self.http_session.close()
        
        # Close all WebSocket connections
        for connection in list(self.websocket_connections.values()):
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
        
        self.websocket_connections.clear()
        logger.info("🔌 Proxy server cleanup completed")
    
    async def start(self):
        """Start the proxy server"""
        if self.running:
            logger.warning("Proxy server is already running")
            return
        
        try:
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            self.server = uvicorn.Server(config)
            
            logger.info(f"🚀 Starting proxy server on {self.host}:{self.port}")
            await self.server.serve()
            
        except Exception as e:
            logger.error(f"❌ Failed to start proxy server: {e}")
            raise
    
    async def stop(self):
        """Stop the proxy server"""
        if not self.running:
            logger.warning("Proxy server is not running")
            return
        
        logger.info("🛑 Stopping proxy server...")
        self.running = False
        
        if hasattr(self, 'server'):
            await self.server.shutdown()
        
        await self._cleanup()


def create_proxy_server(host: str = "0.0.0.0", port: int = 3000) -> ProxyServer:
    """Factory function to create proxy server"""
    return ProxyServer(host, port)