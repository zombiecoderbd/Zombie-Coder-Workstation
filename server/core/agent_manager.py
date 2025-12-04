"""
Agent Manager - Manages all agent instances
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

from .agent_base import AgentBase
from server.routing.model_router import ModelRouter
from server.tools.tool_orchestrator import ToolOrchestrator
from server.rag.rag_pipeline import RAGPipeline
from server.monitoring.metrics import MetricsCollector


@dataclass
class AgentInstance:
    """Represents an active agent instance"""
    agent_id: str
    agent: AgentBase
    created_at: float
    last_used: float
    request_count: int
    is_active: bool


class AgentManager:
    """
    Manages lifecycle and operations of all agents
    """
    
    def __init__(self, 
                 config: Optional[Dict[str, Any]] = None,
                 model_router: Optional[ModelRouter] = None,
                 tool_orchestrator: Optional[ToolOrchestrator] = None,
                 rag_pipeline: Optional[RAGPipeline] = None,
                 metrics_collector: Optional[MetricsCollector] = None):
        
        self.config = config
        self.model_router = model_router
        self.tool_orchestrator = tool_orchestrator
        self.rag_pipeline = rag_pipeline
        self.metrics_collector = metrics_collector
        
        self.logger = logging.getLogger(__name__)
        
        # Agent storage
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_configs: Dict[str, Dict] = {}
        
        # Configuration
        self.max_concurrent_agents = config.get('max_concurrent_agents', 5)
        self.agent_timeout = config.get('agent_timeout', 60)
        self.default_agent = config.get('default_agent', 'virtual_sir')
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize the agent manager"""
        self.logger.info("Initializing Agent Manager...")
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_inactive_agents())
        
        self.logger.info("Agent Manager initialized")
    
    async def register_agent(self, 
                           agent_id: str, 
                           agent_info: Dict[str, Any], 
                           personality: Dict[str, Any]) -> bool:
        """Register a new agent"""
        try:
            # Check if agent already exists
            if agent_id in self.agents:
                self.logger.warning(f"Agent {agent_id} already registered")
                return False
            
            # Check concurrent agent limit
            if len(self.agents) >= self.max_concurrent_agents:
                self.logger.error(f"Maximum concurrent agents ({self.max_concurrent_agents}) reached")
                return False
            
            # Create agent instance
            agent = AgentBase(
                agent_id=agent_id,
                config=agent_info,
                personality=personality,
                model_router=self.model_router,
                tool_orchestrator=self.tool_orchestrator,
                rag_pipeline=self.rag_pipeline,
                metrics_collector=self.metrics_collector
            )
            
            # Initialize agent
            await agent.initialize()
            
            # Store agent instance
            agent_instance = AgentInstance(
                agent_id=agent_id,
                agent=agent,
                created_at=time.time(),
                last_used=time.time(),
                request_count=0,
                is_active=True
            )
            
            self.agents[agent_id] = agent_instance
            self.agent_configs[agent_id] = agent_info
            
            self.logger.info(f"Successfully registered agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[AgentBase]:
        """Get an agent instance by ID"""
        agent_instance = self.agents.get(agent_id)
        if agent_instance and agent_instance.is_active:
            # Update last used time
            agent_instance.last_used = time.time()
            agent_instance.request_count += 1
            return agent_instance.agent
        
        return None
    
    async def get_all_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        status = {
            'total_agents': len(self.agents),
            'active_agents': sum(1 for a in self.agents.values() if a.is_active),
            'agents': {}
        }
        
        for agent_id, instance in self.agents.items():
            try:
                agent_status = await instance.agent.get_status()
                status['agents'][agent_id] = {
                    'instance_info': {
                        'created_at': instance.created_at,
                        'last_used': instance.last_used,
                        'request_count': instance.request_count,
                        'is_active': instance.is_active
                    },
                    'agent_status': agent_status,
                    'config': self.agent_configs.get(agent_id, {})
                }
            except Exception as e:
                status['agents'][agent_id] = {
                    'error': str(e),
                    'is_active': False
                }
        
        return status
    
    async def deactivate_agent(self, agent_id: str) -> bool:
        """Deactivate an agent"""
        agent_instance = self.agents.get(agent_id)
        if agent_instance:
            agent_instance.is_active = False
            try:
                await agent_instance.agent.cleanup()
                self.logger.info(f"Deactivated agent: {agent_id}")
                return True
            except Exception as e:
                self.logger.error(f"Error deactivating agent {agent_id}: {e}")
                return False
        return False
    
    async def reactivate_agent(self, agent_id: str) -> bool:
        """Reactivate a deactivated agent"""
        agent_instance = self.agents.get(agent_id)
        if agent_instance and not agent_instance.is_active:
            try:
                await agent_instance.agent.initialize()
                agent_instance.is_active = True
                agent_instance.last_used = time.time()
                self.logger.info(f"Reactivated agent: {agent_id}")
                return True
            except Exception as e:
                self.logger.error(f"Error reactivating agent {agent_id}: {e}")
                return False
        return False
    
    async def _cleanup_inactive_agents(self):
        """Background task to cleanup inactive agents"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = time.time()
                timeout_threshold = self.agent_timeout * 60  # Convert to seconds
                
                for agent_id, instance in list(self.agents.items()):
                    if (not instance.is_active or 
                        (current_time - instance.last_used) > timeout_threshold):
                        
                        self.logger.info(f"Cleaning up inactive agent: {agent_id}")
                        await self.deactivate_agent(agent_id)
                        
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
    
    async def shutdown(self):
        """Shutdown the agent manager"""
        self.logger.info("Shutting down Agent Manager...")
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown all agents
        for agent_id, instance in self.agents.items():
            try:
                await instance.agent.cleanup()
            except Exception as e:
                self.logger.error(f"Error shutting down agent {agent_id}: {e}")
        
        self.agents.clear()
        self.agent_configs.clear()
        
        self.logger.info("Agent Manager shutdown complete")