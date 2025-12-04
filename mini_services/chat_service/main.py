"""
Chat Service - ZombieCoder Local AI
Real-time chat handling service
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, WebSocket
import uvicorn

logger = logging.getLogger(__name__)


class ChatService:
    """Chat service for real-time communication"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 3003):
        self.host = host
        self.port = port
        self.app = FastAPI(title="ZombieCoder Chat Service")
        self.websocket_connections = {}
        self.running = False
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "💬 ZombieCoder Chat Service", "status": "running"}
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "port": self.port}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            connection_id = str(id(websocket))
            self.websocket_connections[connection_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_text()
                    # Echo back for now
                    await websocket.send_text(f"Echo: {data}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if connection_id in self.websocket_connections:
                    del self.websocket_connections[connection_id]
                await websocket.close()
    
    async def start(self):
        """Start the chat service"""
        if self.running:
            return
        
        try:
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            self.server = uvicorn.Server(config)
            self.running = True
            logger.info(f"💬 Chat service started on {self.host}:{self.port}")
            await self.server.serve()
        except Exception as e:
            logger.error(f"Failed to start chat service: {e}")
            raise
    
    async def stop(self):
        """Stop the chat service"""
        if not self.running:
            return
        
        logger.info("🛑 Stopping chat service...")
        self.running = False
        if hasattr(self, 'server'):
            await self.server.shutdown()


async def create_chat_service(host: str = "0.0.0.0", port: int = 3003) -> ChatService:
    """Factory function to create chat service"""
    return ChatService(host, port)