"""
Monitoring Service - ZombieCoder Local AI
Real-time System Metrics and Monitoring
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import asyncio
import psutil
import json
import logging
import time
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('zombiecoder_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('zombiecoder_request_duration_seconds', 'Request duration')
CPU_USAGE = Gauge('zombiecoder_cpu_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('zombiecoder_memory_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('zombiecoder_disk_percent', 'Disk usage percentage')


@dataclass
class SystemMetrics:
    """System metrics data"""
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_percent: float
    disk_free: int
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime


@dataclass
class RequestMetrics:
    """Request metrics data"""
    total_requests: int
    error_count: int
    avg_response_time: float
    requests_per_second: float


class MetricsCollector:
    """Collect and manage system metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_requests = 0
        self.error_count = 0
        self.response_times: List[float] = []
        self.websocket_connections = 0
        
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free = disk.free
            
            # Network
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv
            
            # Update Prometheus gauges
            CPU_USAGE.set(cpu_percent)
            MEMORY_USAGE.set(memory_percent)
            DISK_USAGE.set(disk_percent)
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available=memory_available,
                disk_percent=disk_percent,
                disk_free=disk_free,
                network_bytes_sent=bytes_sent,
                network_bytes_recv=bytes_recv,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                memory_available=0,
                disk_percent=0,
                disk_free=0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                timestamp=datetime.now()
            )
    
    async def record_request(self, duration: float, success: bool = True):
        """Record request metrics"""
        self.total_requests += 1
        self.response_times.append(duration)
        
        if not success:
            self.error_count += 1
        
        # Update Prometheus metrics
        REQUEST_COUNT.inc()
        REQUEST_DURATION.observe(duration)
    
    async def get_request_metrics(self) -> RequestMetrics:
        """Get request metrics"""
        if not self.response_times:
            avg_response_time = 0
            requests_per_second = 0
        else:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            uptime = time.time() - self.start_time
            requests_per_second = self.total_requests / max(uptime, 1)
        
        return RequestMetrics(
            total_requests=self.total_requests,
            error_count=self.error_count,
            avg_response_time=avg_response_time,
            requests_per_second=requests_per_second
        )
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get complete metrics summary"""
        system_metrics = await self.collect_system_metrics()
        request_metrics = await self.get_request_metrics()
        
        return {
            'system': {
                'cpu_percent': system_metrics.cpu_percent,
                'memory_percent': system_metrics.memory_percent,
                'memory_available_mb': round(system_metrics.memory_available / (1024 * 1024), 2),
                'disk_percent': system_metrics.disk_percent,
                'disk_free_gb': round(system_metrics.disk_free / (1024 * 1024 * 1024), 2),
                'timestamp': system_metrics.timestamp.isoformat()
            },
            'requests': {
                'total': request_metrics.total_requests,
                'errors': request_metrics.error_count,
                'error_rate': request_metrics.error_count / max(request_metrics.total_requests, 1),
                'avg_response_time': request_metrics.avg_response_time,
                'requests_per_second': request_metrics.requests_per_second
            },
            'connections': {
                'websocket_connections': self.websocket_connections
            }
        }


class MonitoringService:
    """Monitoring service for ZombieCoder"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 3002):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="ZombieCoder Monitoring Service",
            description="Real-time System Metrics and Monitoring"
        )
        self.metrics_collector = MetricsCollector()
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.running = False
        
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
        
        @self.app.get("/")
        async def root():
            return {
                "message": "📈 ZombieCoder Monitoring Service",
                "status": "running",
                "port": self.port
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            system_metrics = await self.metrics_collector.collect_system_metrics()
            
            return {
                "status": "healthy",
                "system": {
                    "cpu_percent": system_metrics.cpu_percent,
                    "memory_percent": system_metrics.memory_percent,
                    "disk_percent": system_metrics.disk_percent
                },
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/metrics/system")
        async def get_system_metrics():
            """Get system metrics"""
            return await self.metrics_collector.collect_system_metrics().__dict__
        
        @self.app.get("/metrics/requests")
        async def get_request_metrics():
            """Get request metrics"""
            return await self.metrics_collector.get_request_metrics().__dict__
        
        @self.app.get("/metrics/summary")
        async def get_metrics_summary():
            """Get complete metrics summary"""
            return await self.metrics_collector.get_metrics_summary()
        
        @self.app.get("/metrics/prometheus")
        async def prometheus_metrics():
            """Prometheus metrics endpoint"""
            return generate_latest()
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time metrics"""
            await websocket.accept()
            connection_id = str(id(websocket))
            self.websocket_connections[connection_id] = websocket
            self.metrics_collector.websocket_connections = len(self.websocket_connections)
            
            try:
                while True:
                    # Send metrics every 2 seconds
                    metrics = await self.metrics_collector.get_metrics_summary()
                    await websocket.send_json(metrics)
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if connection_id in self.websocket_connections:
                    del self.websocket_connections[connection_id]
                self.metrics_collector.websocket_connections = len(self.websocket_connections)
                await websocket.close()
    
    async def _metrics_broadcast_loop(self):
        """Broadcast metrics to all WebSocket connections"""
        while self.running:
            try:
                if self.websocket_connections:
                    metrics = await self.metrics_collector.get_metrics_summary()
                    # Send to all connections
                    for connection in list(self.websocket_connections.values()):
                        try:
                            await connection.send_json(metrics)
                        except Exception as e:
                            logger.error(f"Error sending metrics to WebSocket: {e}")
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics broadcast loop: {e}")
                await asyncio.sleep(2)
    
    async def start(self):
        """Start the monitoring service"""
        if self.running:
            logger.warning("Monitoring service is already running")
            return
        
        self.running = True
        
        # Start metrics broadcast loop
        asyncio.create_task(self._metrics_broadcast_loop())
        
        try:
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            self.server = uvicorn.Server(config)
            
            logger.info(f"📈 Starting monitoring service on {self.host}:{self.port}")
            await self.server.serve()
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring service: {e}")
            raise
    
    async def stop(self):
        """Stop the monitoring service"""
        if not self.running:
            logger.warning("Monitoring service is not running")
            return
        
        logger.info("🛑 Stopping monitoring service...")
        self.running = False
        
        if hasattr(self, 'server'):
            await self.server.shutdown()


async def create_monitoring_service(host: str = "0.0.0.0", port: int = 3002) -> MonitoringService:
    """Factory function to create monitoring service"""
    return MonitoringService(host, port)


if __name__ == "__main__":
    # Run monitoring service
    async def main():
        service = MonitoringService()
        await service.start()
    
    asyncio.run(main())