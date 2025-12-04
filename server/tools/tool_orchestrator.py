"""
Tool Orchestrator - Manages and executes tool calls from agents
"""

import asyncio
import logging
import os
import subprocess
import json
import re
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
import aiohttp
from pathlib import Path


@dataclass
class ToolCall:
    """Represents a tool call request"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: str


@dataclass
class ToolResult:
    """Result of a tool call"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class ToolBase(ABC):
    """Abstract base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate tool parameters"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for documentation"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameter_schema()
        }
    
    @abstractmethod
    def _get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema"""
        pass


class FileReaderTool(ToolBase):
    """Tool for reading files"""
    
    def __init__(self):
        super().__init__("file_reader", "Read contents of a file")
        self.allowed_extensions = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.html', '.css']
        self.max_file_size = 1024 * 1024  # 1MB
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Read file content"""
        start_time = time.time()
        
        try:
            file_path = parameters.get('file_path')
            if not file_path:
                return ToolResult(False, None, "file_path parameter is required")
            
            # Security checks
            full_path = Path(file_path).resolve()
            
            # Prevent directory traversal
            if '..' in file_path or str(full_path).startswith('/etc'):
                return ToolResult(False, None, "Access to this path is not allowed")
            
            # Check file extension
            if not any(file_path.endswith(ext) for ext in self.allowed_extensions):
                return ToolResult(False, None, f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}")
            
            # Check file size
            if full_path.exists() and full_path.stat().st_size > self.max_file_size:
                return ToolResult(False, None, "File too large (max 1MB)")
            
            # Read file
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return ToolResult(
                    True,
                    {"content": content, "file_path": str(full_path)},
                    execution_time=time.time() - start_time
                )
            else:
                return ToolResult(False, None, "File not found", time.time() - start_time)
                
        except Exception as e:
            return ToolResult(False, None, str(e), time.time() - start_time)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters"""
        return 'file_path' in parameters and isinstance(parameters['file_path'], str)
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["file_path"]
        }


class FileWriterTool(ToolBase):
    """Tool for writing files"""
    
    def __init__(self):
        super().__init__("file_writer", "Write content to a file")
        self.allowed_extensions = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.html', '.css']
        self.allowed_directories = ['/tmp', './workspace', './data']
        self.max_file_size = 1024 * 1024  # 1MB
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Write content to file"""
        start_time = time.time()
        
        try:
            file_path = parameters.get('file_path')
            content = parameters.get('content', '')
            
            if not file_path:
                return ToolResult(False, None, "file_path parameter is required")
            
            # Security checks
            full_path = Path(file_path).resolve()
            
            # Prevent directory traversal
            if '..' in file_path:
                return ToolResult(False, None, "Directory traversal not allowed")
            
            # Check if path is in allowed directory
            path_allowed = False
            for allowed_dir in self.allowed_directories:
                try:
                    if str(full_path).startswith(str(Path(allowed_dir).resolve())):
                        path_allowed = True
                        break
                except:
                    continue
            
            if not path_allowed:
                return ToolResult(False, None, f"Writing to this directory not allowed. Allowed: {', '.join(self.allowed_directories)}")
            
            # Check file extension
            if not any(file_path.endswith(ext) for ext in self.allowed_extensions):
                return ToolResult(False, None, f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}")
            
            # Check content size
            if len(content.encode('utf-8')) > self.max_file_size:
                return ToolResult(False, None, "Content too large (max 1MB)")
            
            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                True,
                {"file_path": str(full_path), "bytes_written": len(content.encode('utf-8'))},
                execution_time=time.time() - start_time
            )
                
        except Exception as e:
            return ToolResult(False, None, str(e), time.time() - start_time)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters"""
        return ('file_path' in parameters and isinstance(parameters['file_path'], str) and
                'content' in parameters and isinstance(parameters['content'], str))
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }


class CodeAnalyzerTool(ToolBase):
    """Tool for analyzing code"""
    
    def __init__(self):
        super().__init__("code_analyzer", "Analyze code for quality, complexity, and suggestions")
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Analyze code"""
        start_time = time.time()
        
        try:
            code = parameters.get('code', '')
            language = parameters.get('language', 'python')
            
            if not code:
                return ToolResult(False, None, "code parameter is required")
            
            analysis = await self._analyze_code(code, language)
            
            return ToolResult(
                True,
                analysis,
                execution_time=time.time() - start_time
            )
                
        except Exception as e:
            return ToolResult(False, None, str(e), time.time() - start_time)
    
    async def _analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Perform code analysis"""
        analysis = {
            "language": language,
            "lines": len(code.split('\\n')),
            "characters": len(code),
            "complexity": "medium",
            "suggestions": [],
            "issues": []
        }
        
        # Basic analysis based on language
        if language == 'python':
            analysis.update(await self._analyze_python(code))
        elif language in ['javascript', 'typescript']:
            analysis.update(await self._analyze_javascript(code))
        
        return analysis
    
    async def _analyze_python(self, code: str) -> Dict[str, Any]:
        """Analyze Python code"""
        suggestions = []
        issues = []
        
        # Check for common issues
        if 'import *' in code:
            issues.append("Avoid using 'import *' - it's better to import specific modules")
        
        if code.count('print(') > 5:
            suggestions.append("Consider using logging instead of multiple print statements")
        
        # Check function definitions
        func_count = len(re.findall(r'def\\s+\\w+', code))
        if func_count == 0 and len(code) > 100:
            suggestions.append("Consider breaking down this code into functions")
        
        return {
            "functions": func_count,
            "suggestions": suggestions,
            "issues": issues
        }
    
    async def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code"""
        suggestions = []
        issues = []
        
        # Check for common issues
        if 'var ' in code:
            suggestions.append("Consider using 'let' or 'const' instead of 'var'")
        
        if '==' in code and '===' not in code:
            suggestions.append("Consider using '===' for strict equality checks")
        
        # Check function definitions
        func_count = len(re.findall(r'(function|const|let)\\s+\\w+\\s*=', code))
        
        return {
            "functions": func_count,
            "suggestions": suggestions,
            "issues": issues
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters"""
        return 'code' in parameters and isinstance(parameters['code'], str)
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code to analyze"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (python, javascript, typescript, etc.)",
                    "default": "python"
                }
            },
            "required": ["code"]
        }


class WebSearchTool(ToolBase):
    """Tool for web searching"""
    
    def __init__(self):
        super().__init__("web_search", "Search the web for information")
        self.search_engines = {
            "duckduckgo": "https://duckduckgo.com/html/?q=",
            "brave": "https://search.brave.com/search?q="
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Perform web search"""
        start_time = time.time()
        
        try:
            query = parameters.get('query', '')
            max_results = parameters.get('max_results', 5)
            
            if not query:
                return ToolResult(False, None, "query parameter is required")
            
            # For now, return a placeholder result
            # In a real implementation, you'd use a search API
            results = [
                {
                    "title": f"Search result for: {query}",
                    "url": "https://example.com",
                    "snippet": f"This is a placeholder search result for the query: {query}"
                }
            ]
            
            return ToolResult(
                True,
                {"query": query, "results": results[:max_results]},
                execution_time=time.time() - start_time
            )
                
        except Exception as e:
            return ToolResult(False, None, str(e), time.time() - start_time)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters"""
        return 'query' in parameters and isinstance(parameters['query'], str)
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }


class CalculatorTool(ToolBase):
    """Tool for mathematical calculations"""
    
    def __init__(self):
        super().__init__("calculator", "Perform mathematical calculations")
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Perform calculation"""
        start_time = time.time()
        
        try:
            expression = parameters.get('expression', '')
            
            if not expression:
                return ToolResult(False, None, "expression parameter is required")
            
            # Safe evaluation of mathematical expressions
            result = await self._safe_eval(expression)
            
            return ToolResult(
                True,
                {"expression": expression, "result": result},
                execution_time=time.time() - start_time
            )
                
        except Exception as e:
            return ToolResult(False, None, str(e), time.time() - start_time)
    
    async def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression"""
        # Only allow safe mathematical operations
        allowed_chars = set('0123456789+-*/().^ ')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        # Use eval with restricted globals
        return eval(expression, {"__builtins__": {}}, {})
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters"""
        return 'expression' in parameters and isinstance(parameters['expression'], str)
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }


class TerminalTool(ToolBase):
    """Tool for executing terminal commands (restricted)"""
    
    def __init__(self):
        super().__init__("terminal", "Execute safe terminal commands")
        self.allowed_commands = ['ls', 'pwd', 'echo', 'cat', 'grep', 'find', 'wc', 'head', 'tail']
    
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute terminal command"""
        start_time = time.time()
        
        try:
            command = parameters.get('command', '')
            
            if not command:
                return ToolResult(False, None, "command parameter is required")
            
            # Security check - only allow allowed commands
            first_word = command.split()[0] if command.split() else ''
            if first_word not in self.allowed_commands:
                return ToolResult(False, None, f"Command '{first_word}' not allowed. Allowed: {', '.join(self.allowed_commands)}")
            
            # Execute command
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return ToolResult(
                True,
                {
                    "command": command,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                },
                execution_time=time.time() - start_time
            )
                
        except subprocess.TimeoutExpired:
            return ToolResult(False, None, "Command execution timed out", time.time() - start_time)
        except Exception as e:
            return ToolResult(False, None, str(e), time.time() - start_time)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate parameters"""
        return 'command' in parameters and isinstance(parameters['command'], str)
    
    def _get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Terminal command to execute"
                }
            },
            "required": ["command"]
        }


class ToolOrchestrator:
    """
    Main tool orchestrator that manages tool execution
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize tools
        self.tools: Dict[str, ToolBase] = {}
        self.enabled_tools = config.get('enabled_tools', [])
        self.restricted_tools = config.get('restricted_tools', [])
        self.tool_limits = config.get('tool_limits', {})
        
        # Session tracking
        self.session_tool_counts: Dict[str, Dict[str, int]] = {}
        
    async def initialize(self) -> bool:
        """Initialize the tool orchestrator"""
        try:
            self.logger.info("Initializing Tool Orchestrator...")
            
            # Register all available tools
            await self._register_tools()
            
            # Enable configured tools
            await self._enable_tools()
            
            self.logger.info(f"Tool Orchestrator initialized with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Tool Orchestrator: {e}")
            return False
    
    async def _register_tools(self):
        """Register all available tools"""
        available_tools = [
            FileReaderTool(),
            FileWriterTool(),
            CodeAnalyzerTool(),
            WebSearchTool(),
            CalculatorTool(),
            TerminalTool()
        ]
        
        for tool in available_tools:
            self.tools[tool.name] = tool
        
        self.logger.info(f"Registered {len(self.tools)} tools")
    
    async def _enable_tools(self):
        """Enable configured tools"""
        # If no specific tools configured, enable all non-restricted tools
        if not self.enabled_tools:
            self.enabled_tools = [name for name in self.tools.keys() 
                                if name not in self.restricted_tools]
        
        # Log enabled tools
        self.logger.info(f"Enabled tools: {', '.join(self.enabled_tools)}")
    
    async def process_response(self, 
                             response: str, 
                             allowed_tools: List[str], 
                             restricted_tools: List[str],
                             session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process agent response to extract and execute tool calls
        """
        session_id = session_context.get('session_id', 'default')
        
        try:
            # Extract tool calls from response
            tool_calls = await self._extract_tool_calls(response)
            
            if not tool_calls:
                return {}
            
            # Filter tools based on agent permissions
            filtered_calls = await self._filter_tool_calls(
                tool_calls, allowed_tools, restricted_tools
            )
            
            if not filtered_calls:
                return {}
            
            # Check tool limits
            if not await self._check_tool_limits(session_id, filtered_calls):
                return {"error": "Tool call limit exceeded for this session"}
            
            # Execute tool calls
            results = {}
            for tool_call in filtered_calls:
                try:
                    result = await self._execute_tool_call(tool_call)
                    results[tool_call.call_id] = result
                    
                    # Update session tool count
                    await self._update_session_tool_count(session_id, tool_call.tool_name)
                    
                except Exception as e:
                    self.logger.error(f"Error executing tool {tool_call.tool_name}: {e}")
                    results[tool_call.call_id] = ToolResult(False, None, str(e))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing tool calls: {e}")
            return {"error": str(e)}
    
    async def _extract_tool_calls(self, response: str) -> List[ToolCall]:
        """
        Extract tool calls from agent response
        This is a simplified implementation - in practice you'd use more sophisticated parsing
        """
        tool_calls = []
        
        # Simple pattern matching for tool calls
        # Format: [TOOL:tool_name(parameters)]
        pattern = r'\\[TOOL:(\\w+)\\((.*?)\\)\\]'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for i, (tool_name, params_str) in enumerate(matches):
            try:
                # Parse parameters (simplified JSON parsing)
                if params_str.strip():
                    parameters = json.loads(f"{{{params_str}}}")
                else:
                    parameters = {}
                
                tool_call = ToolCall(
                    tool_name=tool_name,
                    parameters=parameters,
                    call_id=f"call_{i}_{int(time.time())}"
                )
                tool_calls.append(tool_call)
                
            except Exception as e:
                self.logger.warning(f"Failed to parse tool call: {e}")
        
        return tool_calls
    
    async def _filter_tool_calls(self, 
                               tool_calls: List[ToolCall], 
                               allowed_tools: List[str], 
                               restricted_tools: List[str]) -> List[ToolCall]:
        """Filter tool calls based on agent permissions"""
        filtered = []
        
        for call in tool_calls:
            # Check if tool is allowed
            if call.tool_name not in allowed_tools:
                self.logger.warning(f"Tool {call.tool_name} not in allowed tools for agent")
                continue
            
            # Check if tool is restricted
            if call.tool_name in restricted_tools:
                self.logger.warning(f"Tool {call.tool_name} is restricted")
                continue
            
            # Check if tool is globally enabled
            if call.tool_name not in self.enabled_tools:
                self.logger.warning(f"Tool {call.tool_name} not globally enabled")
                continue
            
            filtered.append(call)
        
        return filtered
    
    async def _check_tool_limits(self, session_id: str, tool_calls: List[ToolCall]) -> bool:
        """Check if tool calls exceed session limits"""
        max_calls = self.tool_limits.get('max_calls_per_session', 20)
        
        if session_id not in self.session_tool_counts:
            self.session_tool_counts[session_id] = {}
        
        total_calls = sum(self.session_tool_counts[session_id].values())
        
        return total_calls + len(tool_calls) <= max_calls
    
    async def _execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call"""
        tool = self.tools.get(tool_call.tool_name)
        if not tool:
            return ToolResult(False, None, f"Tool {tool_call.tool_name} not found")
        
        # Validate parameters
        if not tool.validate_parameters(tool_call.parameters):
            return ToolResult(False, None, f"Invalid parameters for tool {tool_call.tool_name}")
        
        # Execute tool
        return await tool.execute(tool_call.parameters)
    
    async def _update_session_tool_count(self, session_id: str, tool_name: str):
        """Update tool usage count for session"""
        if session_id not in self.session_tool_counts:
            self.session_tool_counts[session_id] = {}
        
        self.session_tool_counts[session_id][tool_name] = \
            self.session_tool_counts[session_id].get(tool_name, 0) + 1
    
    async def get_tool_status(self) -> Dict[str, Any]:
        """Get status of all tools"""
        status = {
            "total_tools": len(self.tools),
            "enabled_tools": len(self.enabled_tools),
            "restricted_tools": len(self.restricted_tools),
            "tools": {}
        }
        
        for tool_name, tool in self.tools.items():
            status["tools"][tool_name] = {
                "name": tool.name,
                "description": tool.description,
                "enabled": tool_name in self.enabled_tools,
                "restricted": tool_name in self.restricted_tools,
                "schema": tool.get_schema()
            }
        
        return status
    
    async def shutdown(self):
        """Shutdown the tool orchestrator"""
        self.logger.info("Shutting down Tool Orchestrator...")
        self.session_tool_counts.clear()
        self.logger.info("Tool Orchestrator shutdown complete")