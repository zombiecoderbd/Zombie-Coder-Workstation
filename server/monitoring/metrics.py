"""
Metrics Collector - Prometheus-based monitoring system
Tracks performance, usage, and system health metrics
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
from datetime import datetime, timedelta


@dataclass
class MetricValue:
    """Represents a metric value with timestamp"""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    session_id: str
    agent_id: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    input_length: int = 0
    output_length: int = 0
    tokens_used: int = 0
    tools_used: List[str] = field(default_factory=list)
    model_used: str = ""
    error: Optional[str] = None


class MetricsCollector:
    """
    Collects and manages system metrics
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Metric storage
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.request_metrics: List[RequestMetrics] = []
        
        # Active requests tracking
        self.active_requests: Dict[str, RequestMetrics] = {}
        
        # Time windows for aggregation
        self.time_windows = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600
        }
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize the metrics collector"""
        try:
            self.logger.info("Initializing Metrics Collector...")
            
            # Start background cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
            
            # Initialize basic metrics
            self._initialize_basic_metrics()
            
            self.logger.info("Metrics Collector initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Metrics Collector: {e}")
            return False
    
    def _initialize_basic_metrics(self):
        """Initialize basic system metrics"""
        # System metrics
        self.set_gauge('system_start_time', time.time())
        self.set_gauge('system_version', 1.0)
        
        # Agent metrics
        self.set_gauge('agents_registered', 0)
        self.set_gauge('agents_active', 0)
        
        # Request metrics
        self.set_counter('requests_total', 0)
        self.set_counter('requests_success', 0)
        self.set_counter('requests_error', 0)
        
        # Tool metrics
        self.set_counter('tool_calls_total', 0)
        self.set_counter('tool_calls_success', 0)
        self.set_counter('tool_calls_error', 0)
    
    async def start_request(self, session_id: str) -> str:
        """Start tracking a new request"""
        request_id = f"{session_id}_{int(time.time() * 1000)}"
        
        with self.lock:
            metric = RequestMetrics(
                session_id=session_id,
                agent_id="",
                start_time=time.time()
            )
            self.active_requests[request_id] = metric
            
        self.increment_counter('requests_total')
        self.set_gauge('active_requests', len(self.active_requests))
        
        return request_id
    
    async def end_request(self, 
                         request_id: str, 
                         agent_id: str, 
                         success: bool):
        """End tracking a request"""
        with self.lock:
            if request_id not in self.active_requests:
                return
            
            metric = self.active_requests[request_id]
            metric.end_time = time.time()
            metric.agent_id = agent_id
            metric.success = success
            
            # Move to completed metrics
            self.request_metrics.append(metric)
            del self.active_requests[request_id]
        
        # Update counters
        if success:
            self.increment_counter('requests_success')
        else:
            self.increment_counter('requests_error')
        
        self.set_gauge('active_requests', len(self.active_requests))
        
        # Record response time
        if metric.end_time:
            response_time = metric.end_time - metric.start_time
            self.record_histogram('request_duration_seconds', response_time)
    
    async def record_agent_interaction(self, 
                                      agent_id: str, 
                                      session_id: str,
                                      input_length: int,
                                      output_length: int,
                                      tools_used: List[str]):
        """Record detailed agent interaction metrics"""
        with self.lock:
            # Find the most recent request for this session
            for metric in reversed(self.request_metrics):
                if metric.session_id == session_id and metric.end_time:
                    metric.input_length = input_length
                    metric.output_length = output_length
                    metric.tools_used = tools_used
                    break
        
        # Record agent-specific metrics
        self.increment_counter(f'agent_interactions_total', labels={'agent_id': agent_id})
        self.record_histogram('input_length_bytes', input_length, labels={'agent_id': agent_id})
        self.record_histogram('output_length_bytes', output_length, labels={'agent_id': agent_id})
        
        # Record tool usage
        for tool in tools_used:
            self.increment_counter('tool_calls_total', labels={'tool_name': tool, 'agent_id': agent_id})
    
    async def record_model_usage(self, 
                                agent_id: str, 
                                model: str, 
                                tokens: int, 
                                cost: float = 0.0):
        """Record model usage metrics"""
        self.increment_counter('model_tokens_total', tokens, 
                             labels={'model': model, 'agent_id': agent_id})
        self.increment_counter('model_cost_total', cost, 
                             labels={'model': model, 'agent_id': agent_id})
        
        # Record model-specific metrics
        self.record_histogram('model_request_tokens', tokens, 
                            labels={'model': model, 'agent_id': agent_id})
    
    async def record_error(self, session_id: str, error: str):
        """Record an error"""
        self.increment_counter('errors_total', labels={'error_type': self._categorize_error(error)})
        
        # Find and update the request metric
        with self.lock:
            for metric in reversed(self.request_metrics):
                if metric.session_id == session_id:
                    metric.error = error
                    break
    
    def _categorize_error(self, error: str) -> str:
        """Categorize error type"""
        error_lower = error.lower()
        
        if 'timeout' in error_lower:
            return 'timeout'
        elif 'api' in error_lower or 'network' in error_lower:
            return 'api_error'
        elif 'validation' in error_lower:
            return 'validation_error'
        elif 'permission' in error_lower or 'access' in error_lower:
            return 'permission_error'
        else:
            return 'unknown_error'
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value"""
        with self.lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(MetricValue(value, time.time(), labels or {}))
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a metric key with labels"""
        if not labels:
            return name
        
        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self.gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = [mv.value for mv in self.histograms.get(key, [])]
        
        if not values:
            return {}
        
        values.sort()
        count = len(values)
        
        return {
            'count': count,
            'sum': sum(values),
            'min': values[0],
            'max': values[-1],
            'mean': sum(values) / count,
            'p50': values[int(count * 0.5)],
            'p90': values[int(count * 0.9)],
            'p95': values[int(count * 0.95)],
            'p99': values[int(count * 0.99)]
        }
    
    async def get_metrics_summary(self, time_window: str = '5m') -> Dict[str, Any]:
        """Get metrics summary for a time window"""
        current_time = time.time()
        window_seconds = self.time_windows.get(time_window, 300)
        cutoff_time = current_time - window_seconds
        
        with self.lock:
            # Filter recent metrics
            recent_requests = [
                m for m in self.request_metrics 
                if m.start_time >= cutoff_time
            ]
        
        # Calculate summary statistics
        total_requests = len(recent_requests)
        successful_requests = sum(1 for m in recent_requests if m.success)
        error_rate = (total_requests - successful_requests) / total_requests if total_requests > 0 else 0
        
        # Response time statistics
        response_times = [
            m.end_time - m.start_time 
            for m in recent_requests 
            if m.end_time is not None
        ]
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Agent usage
        agent_usage = defaultdict(int)
        for m in recent_requests:
            agent_usage[m.agent_id] += 1
        
        # Tool usage
        tool_usage = defaultdict(int)
        for m in recent_requests:
            for tool in m.tools_used:
                tool_usage[tool] += 1
        
        return {
            'time_window': time_window,
            'timestamp': current_time,
            'requests': {
                'total': total_requests,
                'successful': successful_requests,
                'error_rate': error_rate,
                'avg_response_time': avg_response_time
            },
            'agents': dict(agent_usage),
            'tools': dict(tool_usage),
            'system': {
                'active_requests': len(self.active_requests),
                'uptime': current_time - self.gauges.get('system_start_time', current_time)
            }
        }
    
    async def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        with self.lock:
            # Counters
            for key, value in self.counters.items():
                name = key.split('{')[0]
                labels = self._extract_labels(key)
                label_str = self._format_labels(labels)
                lines.append(f"{name}{label_str} {value}")
            
            # Gauges
            for key, value in self.gauges.items():
                name = key.split('{')[0]
                labels = self._extract_labels(key)
                label_str = self._format_labels(labels)
                lines.append(f"{name}{label_str} {value}")
            
            # Histograms
            for key, values in self.histograms.items():
                name = key.split('{')[0]
                labels = self._extract_labels(key)
                label_str = self._format_labels(labels)
                
                if values:
                    # Basic histogram metrics
                    count = len(values)
                    sum_val = sum(mv.value for mv in values)
                    
                    lines.append(f"{name}_count{label_str} {count}")
                    lines.append(f"{name}_sum{label_str} {sum_val}")
        
        return '\\n'.join(lines)
    
    def _extract_labels(self, key: str) -> Dict[str, str]:
        """Extract labels from metric key"""
        if '{' not in key or '}' not in key:
            return {}
        
        label_part = key.split('{')[1].split('}')[0]
        labels = {}
        
        for pair in label_part.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                labels[k.strip()] = v.strip()
        
        return labels
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus"""
        if not labels:
            return ""
        
        label_str = ','.join(f'{k}="{v}"' for k, v in labels.items())
        return f"{{{label_str}}}"
    
    async def _cleanup_old_metrics(self):
        """Background task to cleanup old metrics"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = time.time()
                cutoff_time = current_time - 3600  # Keep 1 hour of data
                
                with self.lock:
                    # Cleanup old histogram values
                    for key in list(self.histograms.keys()):
                        values = self.histograms[key]
                        self.histograms[key] = deque(
                            [mv for mv in values if mv.timestamp >= cutoff_time],
                            maxlen=1000
                        )
                    
                    # Cleanup old request metrics
                    self.request_metrics = [
                        m for m in self.request_metrics 
                        if m.start_time >= cutoff_time
                    ]
                
                self.logger.debug("Cleaned up old metrics")
                
            except Exception as e:
                self.logger.error(f"Error in metrics cleanup: {e}")
    
    async def shutdown(self):
        """Shutdown the metrics collector"""
        self.logger.info("Shutting down Metrics Collector...")
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear metrics
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.request_metrics.clear()
            self.active_requests.clear()
        
        self.logger.info("Metrics Collector shutdown complete")