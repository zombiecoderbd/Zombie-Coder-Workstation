"""
Agent Workstation - ZombieCoder Local AI
Main orchestration layer for agent management and request processing
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from .agent_manager import AgentManager
from .agent_base import AgentBase

logger = logging.getLogger(__name__)


class AgentWorkstation:
    """Main agent workstation orchestrator"""
    
    def __init__(self):
        self.agent_manager = AgentManager()
        self.is_initialized = False
        self.session_storage = {}
        
    async def initialize(self) -> bool:
        """Initialize the agent workstation"""
        try:
            await self.agent_manager.initialize()
            self.is_initialized = True
            logger.info("🧠 Agent workstation initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent workstation: {e}")
            return False
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request through appropriate agent"""
        if not self.is_initialized:
            return {"success": False, "error": "Workstation not initialized"}
        
        try:
            agent_id = request.get('agent_id', 'virtual_sir')
            user_input = request.get('input', '')
            session_id = request.get('session_id', 'default')
            tools_enabled = request.get('tools_enabled', True)
            
            # Get agent
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                return {"success": False, "error": f"Agent {agent_id} not found"}
            
            # Process with agent
            response = await agent.process_request(user_input, session_id, tools_enabled)
            
            return {
                "success": True,
                "response": response,
                "agent_id": agent_id,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        if not self.is_initialized:
            return {"initialized": False}
        
        return await self.agent_manager.get_agent_status()
    
    async def shutdown(self):
        """Shutdown the workstation"""
        if self.agent_manager:
            await self.agent_manager.shutdown()
        self.is_initialized = False
        logger.info("🛑 Agent workstation shutdown")


async def create_workstation() -> AgentWorkstation:
    """Factory function to create agent workstation"""
    workstation = AgentWorkstation()
    await workstation.initialize()
    return workstation