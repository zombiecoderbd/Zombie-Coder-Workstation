"""
Coding Agent - Cursor-style Developer Assistant
Specialized in code generation, debugging, and system analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import re
import json

from ..core.agent_base import AgentBase
from ..routing.model_router import ModelRouter
from ..tools.tool_orchestrator import ToolOrchestrator
from ..rag.rag_pipeline import RAGPipeline
from ..monitoring.metrics import MetricsCollector


class CodingAgent(AgentBase):
    """
    Coding Agent - Cursor-style Developer Assistant
    Focuses on code generation, debugging, refactoring, and system analysis
    """
    
    def __init__(self,
                 model_router: ModelRouter,
                 tool_orchestrator: ToolOrchestrator,
                 rag_pipeline: RAGPipeline,
                 metrics_collector: MetricsCollector):
        
        # Coding Agent specific configuration
        config = {
            "display_name": "Coding Agent",
            "description": "Professional development assistant for code generation and debugging",
            "category": "development",
            "status": "active",
            "version": "1.0.0"
        }
        
        personality = {
            "name": "Coding Agent",
            "personality": {
                "tone": "technical, efficient, precise",
                "communication_style": "concise, code-focused",
                "greeting_message": "Ready to code! What development task can I help with?",
                "closing_message": "Code complete! Let me know if you need any refinements."
            },
            "behavior": {
                "response_length": "concise",
                "explanation_depth": "technical",
                "example_usage": "code_examples",
                "efficiency_priority": True
            },
            "coding_preferences": {
                "code_style": "best_practices",
                "documentation_inclusion": True,
                "error_handling": "comprehensive",
                "testing_suggestions": True,
                "optimization_tips": True
            },
            "allowed_tools": [
                "file_reader",
                "file_writer",
                "code_analyzer",
                "terminal",
                "web_search",
                "documentation_lookup",
                "git_operations",
                "package_manager"
            ],
            "restricted_tools": [
                "system_modify_critical",
                "network_admin"
            ],
            "model_preferences": {
                "primary_model": "claude-3-sonnet-20240229",
                "temperature": 0.1,
                "max_tokens": 4000,
                "response_format": "code_focused"
            }
        }
        
        super().__init__(
            agent_id="coding_agent",
            config=config,
            personality=personality,
            model_router=model_router,
            tool_orchestrator=tool_orchestrator,
            rag_pipeline=rag_pipeline,
            metrics_collector=metrics_collector
        )
        
        self.coding_patterns = {
            "generate": [
                "create", "generate", "write", "implement", "build", "develop"
            ],
            "debug": [
                "debug", "fix", "error", "issue", "problem", "broken", "not working"
            ],
            "refactor": [
                "refactor", "improve", "optimize", "clean up", "reorganize"
            ],
            "review": [
                "review", "analyze", "check", "examine", "audit"
            ],
            "explain": [
                "explain", "how does", "what does", "understand", "clarify"
            ]
        }
        
        self.language_patterns = {
            "python": [".py", "def ", "import ", "from ", "print(", "python"],
            "javascript": [".js", ".jsx", "function", "const ", "let ", "var ", "=>"],
            "typescript": [".ts", ".tsx", "interface ", "type ", "as ", "typescript"],
            "java": [".java", "public class", "private ", "protected ", "java"],
            "cpp": [".cpp", ".cxx", ".cc", "#include", "namespace", "cpp"],
            "html": [".html", ".htm", "<div", "<html", "<body", "html"],
            "css": [".css", "{", "}", "margin:", "padding:", "color:"],
            "sql": [".sql", "SELECT", "FROM", "WHERE", "INSERT", "UPDATE"]
        }
    
    async def _initialize_agent(self):
        """Initialize Coding Agent specific components"""
        self.logger.info("Initializing Coding Agent...")
        
        # Load code templates and patterns
        await self._load_code_templates()
        
        # Initialize best practices database
        await self._initialize_best_practices()
        
        # Load debugging strategies
        await self._load_debugging_strategies()
        
        self.logger.info("Coding Agent initialized successfully")
    
    async def _load_code_templates(self):
        """Load code templates for common patterns"""
        self.code_templates = {
            "python": {
                "function": '''def {function_name}({parameters}):
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {return_doc}
    """
    {body}''',
                "class": '''class {class_name}:
    """
    {description}
    """
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}''',
                "script": '''#!/usr/bin/env python3
"""
{description}
"""

import sys
import os

{imports}

def main():
    """Main function"""
    {main_body}

if __name__ == "__main__":
    main()''',
                "error_handling": '''try:
    {risky_code}
except {exception_type} as e:
    print(f"Error: {e}")
    {error_handling}
finally:
    {cleanup_code}'''
            },
            "javascript": {
                "function": '''function {function_name}({parameters}) {{
    /**
     * {description}
     * {param_doc}
     * @returns {{{return_type}}} {return_doc}
     */
    {body}
}}''',
                "class": '''class {class_name} {{
    /**
     * {description}
     */
    constructor({constructor_params}) {{
        {constructor_body}
    }}
    
    {methods}
}}''',
                "module": '''// {description}
{imports}

{constants}

{functions}

export {exports};''',
                "async": '''async function {function_name}({parameters}) {{
    try {{
        {body}
    }} catch (error) {{
        console.error("Error:", error);
        {error_handling}
    }}
}}'''
            }
        }
    
    async def _initialize_best_practices(self):
        """Initialize best practices for different languages"""
        self.best_practices = {
            "python": [
                "Use meaningful variable and function names",
                "Write docstrings for functions and classes",
                "Follow PEP 8 style guidelines",
                "Use list comprehensions instead of loops when appropriate",
                "Handle exceptions properly",
                "Avoid using wildcard imports",
                "Use type hints for better code documentation",
                "Keep functions small and focused on one task"
            ],
            "javascript": [
                "Use const and let instead of var",
                "Use arrow functions for callbacks",
                "Handle promises properly with async/await",
                "Use meaningful variable names",
                "Add JSDoc comments for functions",
                "Avoid global variables",
                "Use ESLint for code quality",
                "Test your code thoroughly"
            ],
            "general": [
                "Write clean, readable code",
                "Add appropriate comments",
                "Follow consistent naming conventions",
                "Handle errors gracefully",
                "Write unit tests",
                "Keep code DRY (Don't Repeat Yourself)",
                "Use version control",
                "Document your code"
            ]
        }
    
    async def _load_debugging_strategies(self):
        """Load debugging strategies and common solutions"""
        self.debugging_strategies = {
            "syntax_errors": [
                "Check for missing brackets, parentheses, or quotes",
                "Verify proper indentation",
                "Check for typos in keywords",
                "Ensure proper statement termination"
            ],
            "runtime_errors": [
                "Check variable values before use",
                "Verify array/list bounds",
                "Check for null/undefined values",
                "Verify function parameters"
            ],
            "logic_errors": [
                "Add debug prints or logging",
                "Use a debugger to step through code",
                "Check algorithm logic",
                "Verify conditional statements"
            ],
            "performance_issues": [
                "Profile your code to find bottlenecks",
                "Optimize loops and algorithms",
                "Check for memory leaks",
                "Consider caching expensive operations"
            ]
        }
    
    async def _preprocess_input(self, user_input: str, context: Dict) -> str:
        """Pre-process input with development focus"""
        processed = await super()._preprocess_input(user_input, context)
        
        # Detect coding intent
        intent = self._detect_coding_intent(processed)
        context['coding_intent'] = intent
        
        # Detect programming language
        language = self._detect_programming_language(processed)
        context['programming_language'] = language
        
        # Identify code patterns
        patterns = self._identify_code_patterns(processed)
        context['code_patterns'] = patterns
        
        # Adjust input based on detected patterns
        if intent == "generate":
            processed = f"Generate code for: {processed}"
        elif intent == "debug":
            processed = f"Debug and fix: {processed}"
        elif intent == "refactor":
            processed = f"Refactor and improve: {processed}"
        elif intent == "review":
            processed = f"Review and analyze: {processed}"
        elif intent == "explain":
            processed = f"Explain the code: {processed}"
        
        return processed
    
    def _detect_coding_intent(self, text: str) -> str:
        """Detect the user's coding intent"""
        text_lower = text.lower()
        
        for intent, patterns in self.coding_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return intent
        
        return "general"
    
    def _detect_programming_language(self, text: str) -> str:
        """Detect the programming language being discussed"""
        text_lower = text.lower()
        
        language_scores = {}
        for language, patterns in self.language_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            language_scores[language] = score
        
        if language_scores:
            best_language = max(language_scores, key=language_scores.get)
            if language_scores[best_language] > 0:
                return best_language
        
        return "general"
    
    def _identify_code_patterns(self, text: str) -> List[str]:
        """Identify specific code patterns mentioned"""
        patterns = []
        
        # Common programming patterns
        pattern_keywords = {
            "function": ["function", "def", "method", "procedure"],
            "class": ["class", "object", "instance"],
            "loop": ["loop", "for", "while", "iterate"],
            "condition": ["if", "else", "switch", "case"],
            "error_handling": ["try", "catch", "except", "error"],
            "async": ["async", "await", "promise", "callback"],
            "database": ["database", "sql", "query", "table"],
            "api": ["api", "endpoint", "request", "response"],
            "testing": ["test", "unit", "mock", "assert"]
        }
        
        text_lower = text.lower()
        for pattern, keywords in pattern_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                patterns.append(pattern)
        
        return patterns
    
    async def _build_system_prompt(self) -> str:
        """Build specialized system prompt for Coding Agent"""
        base_prompt = super()._build_system_prompt()
        
        coding_guidelines = """

Coding Agent Development Guidelines:

CODE QUALITY STANDARDS:
- Write clean, readable, and maintainable code
- Follow language-specific best practices and conventions
- Include proper error handling and validation
- Add meaningful comments and documentation
- Use appropriate design patterns

RESPONSE STRUCTURE:
1. Direct answer or solution
2. Code implementation (if applicable)
3. Explanation of key concepts
4. Best practices and improvements
5. Testing suggestions
6. Potential edge cases

DEVELOPMENT FOCUS:
- Provide working, tested solutions
- Explain technical decisions and trade-offs
- Suggest optimizations and alternatives
- Include security considerations
- Recommend testing strategies

CODE REVIEW PRINCIPLES:
- Check for correctness and efficiency
- Verify proper error handling
- Assess code readability and maintainability
- Identify potential security issues
- Suggest improvements and refactoring opportunities

DEBUGGING APPROACH:
- Identify the root cause of issues
- Provide step-by-step solutions
- Explain why the error occurs
- Suggest prevention strategies
- Recommend debugging tools and techniques

Remember: Your goal is to help developers write better code through practical, efficient solutions and expert guidance."""
        
        return base_prompt + coding_guidelines
    
    def _add_coding_touches(self, response: str) -> str:
        """Add coding-specific enhancements to responses"""
        enhanced = response
        
        # Ensure code is properly formatted
        enhanced = self._format_code_blocks(enhanced)
        
        # Add best practices reminder if not present
        if "best practice" not in enhanced.lower() and len(enhanced) > 300:
            practices = self._suggest_best_practices(enhanced)
            if practices:
                enhanced += f"\\n\\n**Best Practices:**\\n{practices}"
        
        # Add testing suggestions
        if "test" not in enhanced.lower() and "function" in enhanced.lower():
            testing = self._suggest_testing(enhanced)
            if testing:
                enhanced += f"\\n\\n**Testing Suggestions:**\\n{testing}"
        
        # Add optimization tips
        if "optimize" not in enhanced.lower() and "performance" not in enhanced.lower():
            optimization = self._suggest_optimizations(enhanced)
            if optimization:
                enhanced += f"\\n\\n**Optimization Tips:**\\n{optimization}"
        
        # Add security considerations
        if "security" not in enhanced.lower() and ("input" in enhanced.lower() or "data" in enhanced.lower()):
            security = self._suggest_security_considerations(enhanced)
            if security:
                enhanced += f"\\n\\n**Security Considerations:**\\n{security}"
        
        return enhanced
    
    def _format_code_blocks(self, response: str) -> str:
        """Ensure code is properly formatted in code blocks"""
        lines = response.split('\\n')
        formatted_lines = []
        in_code_block = False
        code_language = None
        
        for line in lines:
            stripped = line.strip()
            
            # Detect code start
            if not in_code_block and (
                any(keyword in stripped for keyword in ['def ', 'function', 'class ', 'import ', 'const ', 'let ']) or
                stripped.startswith(('if ', 'for ', 'while ', 'try {', 'catch (')) or
                any(stripped.endswith(suffix) for suffix in ['{', '(', ':'])
            ):
                if not any(line.startswith('```') for line in formatted_lines[-5:] if line.strip()):
                    # Determine language
                    code_language = self._detect_code_language_context(response)
                    formatted_lines.append(f'```{code_language}')
                    in_code_block = True
            
            formatted_lines.append(line)
            
            # Detect code end
            if in_code_block and stripped == '' and len(formatted_lines) > 1:
                next_line_idx = len(formatted_lines)
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    if next_line and not any(keyword in next_line for keyword in ['def ', 'function', 'class ', 'import ', 'const ', 'let ']):
                        formatted_lines.append('```')
                        in_code_block = False
        
        # Close any remaining code block
        if in_code_block:
            formatted_lines.append('```')
        
        return '\\n'.join(formatted_lines)
    
    def _detect_code_language_context(self, text: str) -> str:
        """Detect the most likely programming language from context"""
        language_scores = {}
        text_lower = text.lower()
        
        for language, patterns in self.language_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            language_scores[language] = score
        
        if language_scores:
            best_language = max(language_scores, key=language_scores.get)
            if language_scores[best_language] > 0:
                return best_language
        
        return ""
    
    def _suggest_best_practices(self, response: str) -> str:
        """Suggest relevant best practices"""
        language = self._detect_code_language_context(response)
        practices = self.best_practices.get(language, self.best_practices["general"])
        
        return '\\n'.join(f"- {practice}" for practice in practices[:5])
    
    def _suggest_testing(self, response: str) -> str:
        """Suggest testing approaches"""
        suggestions = [
            "Write unit tests for individual functions",
            "Test edge cases and error conditions",
            "Use integration tests for component interactions",
            "Consider property-based testing for complex logic",
            "Set up continuous integration for automated testing"
        ]
        
        return '\\n'.join(f"- {suggestion}" for suggestion in suggestions[:3])
    
    def _suggest_optimizations(self, response: str) -> str:
        """Suggest performance optimizations"""
        suggestions = [
            "Profile your code to identify bottlenecks",
            "Use appropriate data structures for your use case",
            "Consider caching expensive computations",
            "Optimize database queries and indexes",
            "Minimize memory allocations in hot paths"
        ]
        
        return '\\n'.join(f"- {suggestion}" for suggestion in suggestions[:3])
    
    def _suggest_security_considerations(self, response: str) -> str:
        """Suggest security considerations"""
        suggestions = [
            "Validate and sanitize all user inputs",
            "Use parameterized queries to prevent SQL injection",
            "Implement proper authentication and authorization",
            "Encrypt sensitive data at rest and in transit",
            "Keep dependencies updated and scan for vulnerabilities"
        ]
        
        return '\\n'.join(f"- {suggestion}" for suggestion in suggestions[:3])
    
    async def get_coding_metrics(self) -> Dict[str, Any]:
        """Get coding-specific metrics"""
        base_status = await self.get_status()
        
        coding_metrics = {
            "supported_languages": list(self.language_patterns.keys()),
            "code_templates": {
                lang: list(templates.keys()) 
                for lang, templates in self.code_templates.items()
            },
            "coding_style": "best_practices_focused",
            "specializations": [
                "web_development",
                "python",
                "javascript", 
                "typescript",
                "system_architecture"
            ],
            "capabilities": [
                "code_generation",
                "debugging",
                "code_review",
                "refactoring",
                "documentation",
                "file_operations",
                "terminal_commands"
            ],
            "safety_features": [
                "code_validation",
                "security_check",
                "dependency_safety",
                "system_protection"
            ]
        }
        
        base_status.update(coding_metrics)
        return base_status