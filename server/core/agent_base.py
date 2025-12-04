"""
Base Agent Class - Foundation for all agents
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import time
import uuid

from server.routing.model_router import ModelRouter
from server.tools.tool_orchestrator import ToolOrchestrator
from server.rag.rag_pipeline import RAGPipeline
from server.monitoring.metrics import MetricsCollector


class AgentBase(ABC):
    """
    Base class for all agents in the ZombieCoder system
    """
    
    def __init__(self,
                 agent_id: str,
                 config: Dict[str, Any],
                 personality: Dict[str, Any],
                 model_router: ModelRouter,
                 tool_orchestrator: ToolOrchestrator,
                 rag_pipeline: RAGPipeline,
                 metrics_collector: MetricsCollector):
        
        self.agent_id = agent_id
        self.config = config
        self.personality = personality
        self.model_router = model_router
        self.tool_orchestrator = tool_orchestrator
        self.rag_pipeline = rag_pipeline
        self.metrics_collector = metrics_collector
        
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Agent state
        self.is_initialized = False
        self.session_context: Dict[str, Dict] = {}
        
        # Personality traits
        self.name = personality.get('name', agent_id)
        self.tone = personality.get('personality', {}).get('tone', 'neutral')
        self.communication_style = personality.get('personality', {}).get('communication_style', 'balanced')
        
        # Capabilities and restrictions
        self.allowed_tools = personality.get('allowed_tools', [])
        self.restricted_tools = personality.get('restricted_tools', [])
        self.model_preferences = personality.get('model_preferences', {})
        
    async def initialize(self) -> bool:
        """Initialize the agent"""
        try:
            self.logger.info(f"Initializing agent: {self.name}")
            
            # Perform agent-specific initialization
            await self._initialize_agent()
            
            self.is_initialized = True
            self.logger.info(f"Agent {self.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {self.name}: {e}")
            return False
    
    @abstractmethod
    async def _initialize_agent(self):
        """Agent-specific initialization logic"""
        pass
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user request
        """
        if not self.is_initialized:
            raise RuntimeError(f"Agent {self.agent_id} not initialized")
        
        session_id = request.get('session_id', str(uuid.uuid4()))
        user_input = request.get('input', '')
        context = request.get('context', {})
        tools_enabled = request.get('tools_enabled', True)
        
        try:
            # Get or create session context
            session_context = self._get_session_context(session_id)
            
            # Pre-process input
            processed_input = await self._preprocess_input(user_input, session_context)
            
            # Retrieve relevant context from RAG
            rag_context = ""
            if self.rag_pipeline:
                rag_context = await self.rag_pipeline.retrieve_context(
                    query=processed_input,
                    agent_id=self.agent_id,
                    session_context=session_context
                )
            
            # Build prompt with personality and context
            prompt = await self._build_prompt(
                processed_input, 
                rag_context, 
                session_context
            )
            
            # Get model response
            model_response = await self._get_model_response(prompt, session_context)
            
            # Process tools if enabled
            tool_results = {}
            if tools_enabled and self.allowed_tools:
                tool_results = await self._process_tools(
                    model_response, 
                    session_context
                )
            
            # Post-process response
            final_response = await self._postprocess_response(
                model_response, 
                tool_results, 
                session_context
            )
            
            # Update session context
            self._update_session_context(session_id, {
                'last_input': user_input,
                'last_response': final_response,
                'tool_results': tool_results,
                'timestamp': time.time()
            })
            
            # Record metrics
            if self.metrics_collector:
                await self.metrics_collector.record_agent_interaction(
                    agent_id=self.agent_id,
                    session_id=session_id,
                    input_length=len(user_input),
                    output_length=len(final_response),
                    tools_used=list(tool_results.keys())
                )
            
            return {
                'response': final_response,
                'agent_name': self.name,
                'session_id': session_id,
                'tools_used': list(tool_results.keys()),
                'rag_context_used': bool(rag_context),
                'model_used': session_context.get('last_model', 'unknown')
            }
            
        except Exception as e:
            self.logger.error(f"Error processing request in agent {self.agent_id}: {e}")
            return {
                'error': str(e),
                'agent_name': self.name,
                'session_id': session_id
            }
    
    async def _preprocess_input(self, user_input: str, context: Dict) -> str:
        """Pre-process user input"""
        # Basic cleaning and validation
        processed = user_input.strip()
        
        # Add personality-specific preprocessing
        if self.communication_style == "step-by-step":
            # Look for educational patterns
            if "?" in processed or "how to" in processed.lower():
                processed = f"Please explain step by step: {processed}"
        
        return processed
    
    async def _build_prompt(self, 
                          user_input: str, 
                          rag_context: str, 
                          session_context: Dict) -> str:
        """Build the complete prompt for the model"""
        
        # System prompt based on personality
        system_prompt = self._build_system_prompt()
        
        # Context from previous interactions
        conversation_context = self._build_conversation_context(session_context)
        
        # RAG context
        rag_section = f"\\n\\nRelevant Information:\\n{rag_context}" if rag_context else ""
        
        # Complete prompt
        full_prompt = f"""{system_prompt}

{conversation_context}{rag_section}

User: {user_input}

Assistant:"""
        
        return full_prompt
    
    def _build_system_prompt(self) -> str:
        """Build system prompt based on personality"""
        personality_traits = self.personality.get('personality', {})
        behavior = self.personality.get('behavior', {})
        
        system_prompt = f"""You are {self.name}, an AI assistant.

Personality:
- Tone: {self.tone}
- Communication Style: {self.communication_style}

Behavior Guidelines:
- Response Length: {behavior.get('response_length', 'medium')}
- Explanation Depth: {behavior.get('explanation_depth', 'moderate')}
- Example Usage: {behavior.get('example_usage', 'occasional')}"""

        # Add personality-specific instructions
        if self.agent_id == "virtual_sir":
            system_prompt += """

Teaching Guidelines:
- Always provide step-by-step explanations
- Use simple, clear language
- Include relevant examples
- Be patient and encouraging
- Focus on educational value
- Never provide harmful or dangerous instructions"""
        
        elif self.agent_id == "coding_agent":
            system_prompt += """

Coding Guidelines:
- Provide clean, efficient code
- Include proper error handling
- Follow best practices
- Add helpful comments when necessary
- Consider security implications
- Focus on practical, working solutions"""

        # Add tool usage guidelines
        if self.allowed_tools:
            system_prompt += f"""

Available Tools: {', '.join(self.allowed_tools)}
You may use these tools when they would be helpful for the user's request."""

        return system_prompt
    
    def _build_conversation_context(self, session_context: Dict) -> str:
        """Build conversation context from session history"""
        history = session_context.get('history', [])
        if not history:
            return ""
        
        context_lines = ["\\nRecent Conversation:"]
        for item in history[-3:]:  # Last 3 interactions
            context_lines.append(f"User: {item.get('input', '')}")
            context_lines.append(f"Assistant: {item.get('response', '')[:100]}...")
        
        return "\\n".join(context_lines)
    
    async def _get_model_response(self, prompt: str, session_context: Dict) -> str:
        """Get response from the appropriate model"""
        
        # Select model based on preferences
        model_config = self.model_preferences.copy()
        model_config['agent_id'] = self.agent_id
        
        response = await self.model_router.get_completion(
            prompt=prompt,
            config=model_config
        )
        
        # Store model used in session context
        session_context['last_model'] = response.get('model', 'unknown')
        
        return response.get('content', '')
    
    async def _process_tools(self, 
                           model_response: str, 
                           session_context: Dict) -> Dict[str, Any]:
        """Process any tool calls in the model response"""
        if not self.tool_orchestrator or not self.allowed_tools:
            return {}
        
        try:
            # Extract tool calls from response (simplified)
            tool_results = await self.tool_orchestrator.process_response(
                response=model_response,
                allowed_tools=self.allowed_tools,
                restricted_tools=self.restricted_tools,
                session_context=session_context
            )
            
            return tool_results
            
        except Exception as e:
            self.logger.error(f"Error processing tools: {e}")
            return {}
    
    async def _postprocess_response(self, 
                                  model_response: str, 
                                  tool_results: Dict[str, Any], 
                                  session_context: Dict) -> str:
        """Post-process the model response"""
        response = model_response
        
        # Add tool results to response if any
        if tool_results:
            tool_summary = "\\n\\n[Tool Results]\\n"
            for tool_name, result in tool_results.items():
                tool_summary += f"- {tool_name}: {result}\\n"
            response += tool_summary
        
        # Apply personality-specific post-processing
        if self.agent_id == "virtual_sir":
            response = self._add_educational_touches(response)
        elif self.agent_id == "coding_agent":
            response = self._add_coding_touches(response)
        
        return response
    
    def _add_educational_touches(self, response: str) -> str:
        """Add educational touches to Virtual Sir responses"""
        if not response.endswith(('!', '.')):
            response += '.'
        
        # Add encouraging closing if not present
        if not any(word in response.lower() for word in ['keep learning', 'practice', 'good job']):
            response += "\\n\\nKeep practicing and learning!"
        
        return response
    
    def _add_coding_touches(self, response: str) -> str:
        """Add coding-specific touches to Coding Agent responses"""
        # Ensure code blocks are properly formatted
        if '```' not in response and any(word in response.lower() for word in ['function', 'class', 'def', 'import']):
            # Simple heuristic - wrap code-like content in code blocks
            lines = response.split('\\n')
            in_code_section = False
            formatted_lines = []
            
            for line in lines:
                if any(keyword in line.strip() for keyword in ['def ', 'class ', 'function', 'import ', 'from ']):
                    if not in_code_section:
                        formatted_lines.append('```python')
                        in_code_section = True
                    formatted_lines.append(line)
                elif in_code_section and line.strip() == '':
                    formatted_lines.append('```')
                    formatted_lines.append(line)
                    in_code_section = False
                else:
                    formatted_lines.append(line)
            
            if in_code_section:
                formatted_lines.append('```')
            
            response = '\\n'.join(formatted_lines)
        
        return response
    
    def _get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get or create session context"""
        if session_id not in self.session_context:
            self.session_context[session_id] = {
                'created_at': time.time(),
                'history': [],
                'last_model': None
            }
        return self.session_context[session_id]
    
    def _update_session_context(self, session_id: str, update_data: Dict[str, Any]):
        """Update session context"""
        context = self._get_session_context(session_id)
        
        # Add to history
        if 'last_input' in update_data and 'last_response' in update_data:
            context['history'].append({
                'input': update_data['last_input'],
                'response': update_data['last_response'],
                'timestamp': update_data.get('timestamp', time.time()),
                'tools_used': update_data.get('tool_results', {}).keys()
            })
            
            # Limit history size
            if len(context['history']) > 10:
                context['history'] = context['history'][-10:]
        
        # Update other fields
        context.update(update_data)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'is_initialized': self.is_initialized,
            'active_sessions': len(self.session_context),
            'allowed_tools': self.allowed_tools,
            'restricted_tools': self.restricted_tools,
            'model_preferences': self.model_preferences,
            'personality': {
                'tone': self.tone,
                'communication_style': self.communication_style
            }
        }
    
    async def cleanup(self):
        """Cleanup agent resources"""
        self.logger.info(f"Cleaning up agent: {self.name}")
        self.session_context.clear()
        self.is_initialized = False