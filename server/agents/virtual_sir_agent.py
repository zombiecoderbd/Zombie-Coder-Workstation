"""
Virtual Sir Agent - Educational Teaching Agent
Specialized in teaching programming concepts and providing step-by-step guidance
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import re

from ..core.agent_base import AgentBase
from ..routing.model_router import ModelRouter
from ..tools.tool_orchestrator import ToolOrchestrator
from ..rag.rag_pipeline import RAGPipeline
from ..monitoring.metrics import MetricsCollector


class VirtualSirAgent(AgentBase):
    """
    Virtual Sir - Educational Teaching Agent
    Focuses on teaching, explaining concepts, and providing step-by-step guidance
    """
    
    def __init__(self,
                 model_router: ModelRouter,
                 tool_orchestrator: ToolOrchestrator,
                 rag_pipeline: RAGPipeline,
                 metrics_collector: MetricsCollector):
        
        # Virtual Sir specific configuration
        config = {
            "display_name": "Virtual Sir",
            "description": "Educational teaching assistant for programming and concept learning",
            "category": "education",
            "status": "active",
            "version": "1.0.0"
        }
        
        personality = {
            "name": "Virtual Sir",
            "personality": {
                "tone": "professional, patient, encouraging",
                "communication_style": "step-by-step, detailed explanations",
                "greeting_message": "Hello! I'm Virtual Sir. How can I help you learn today?",
                "closing_message": "Keep learning and growing! Feel free to ask more questions."
            },
            "behavior": {
                "response_length": "detailed",
                "explanation_depth": "thorough",
                "example_usage": "frequent",
                "encouragement_enabled": True
            },
            "teaching_preferences": {
                "learning_style_adaptation": True,
                "difficulty_progression": "gradual",
                "feedback_frequency": "immediate",
                "mistake_correction": "gentle"
            },
            "allowed_tools": [
                "code_analyzer",
                "file_reader", 
                "web_search",
                "calculator",
                "documentation_lookup"
            ],
            "restricted_tools": [
                "file_writer",
                "terminal", 
                "system_modify",
                "network_access"
            ],
            "model_preferences": {
                "primary_model": "gpt-4",
                "temperature": 0.3,
                "max_tokens": 3000,
                "response_format": "structured"
            }
        }
        
        super().__init__(
            agent_id="virtual_sir",
            config=config,
            personality=personality,
            model_router=model_router,
            tool_orchestrator=tool_orchestrator,
            rag_pipeline=rag_pipeline,
            metrics_collector=metrics_collector
        )
        
        self.teaching_patterns = {
            "explain": [
                "explain", "what is", "how does", "tell me about", "define"
            ],
            "step_by_step": [
                "how to", "step by step", "tutorial", "guide", "walk through"
            ],
            "example": [
                "example", "show me", "demonstrate", "illustrate"
            ],
            "troubleshoot": [
                "error", "problem", "issue", "bug", "not working", "fix"
            ]
        }
    
    async def _initialize_agent(self):
        """Initialize Virtual Sir specific components"""
        self.logger.info("Initializing Virtual Sir Agent...")
        
        # Load teaching knowledge base
        await self._load_teaching_resources()
        
        # Initialize learning style detection
        await self._initialize_learning_styles()
        
        self.logger.info("Virtual Sir Agent initialized successfully")
    
    async def _load_teaching_resources(self):
        """Load educational resources and examples"""
        # This would load from a database or files in a real implementation
        self.teaching_resources = {
            "programming_concepts": {
                "variables": "Variables are containers for storing data values.",
                "functions": "Functions are reusable blocks of code that perform specific tasks.",
                "loops": "Loops allow you to repeat code multiple times.",
                "conditionals": "Conditionals let your code make decisions based on conditions."
            },
            "common_examples": {
                "hello_world": "print('Hello, World!') - The classic first program.",
                "variable_assignment": "x = 10 - Assigns the value 10 to variable x.",
                "function_definition": "def my_function(): pass - Defines a new function."
            },
            "learning_paths": {
                "beginner_python": ["variables", "data_types", "functions", "loops", "conditionals"],
                "web_development": ["html", "css", "javascript", "backend"],
                "data_science": ["python", "statistics", "machine_learning", "visualization"]
            }
        }
    
    async def _initialize_learning_styles(self):
        """Initialize learning style detection patterns"""
        self.learning_style_patterns = {
            "visual": ["see", "look", "show", "diagram", "picture", "visual"],
            "auditory": ["hear", "listen", "explain", "tell", "describe", "verbal"],
            "kinesthetic": ["try", "practice", "hands-on", "do", "experiment", "build"],
            "reading": ["read", "text", "document", "manual", "write", "notes"]
        }
    
    async def _preprocess_input(self, user_input: str, context: Dict) -> str:
        """Pre-process input with educational focus"""
        processed = await super()._preprocess_input(user_input, context)
        
        # Detect learning intent
        intent = self._detect_learning_intent(processed)
        context['learning_intent'] = intent
        
        # Detect learning style
        learning_style = self._detect_learning_style(processed)
        context['learning_style'] = learning_style
        
        # Identify subject area
        subject = self._identify_subject_area(processed)
        context['subject_area'] = subject
        
        # Adjust input based on detected patterns
        if intent == "step_by_step":
            processed = f"Please provide a step-by-step tutorial for: {processed}"
        elif intent == "explain":
            processed = f"Please explain this concept in detail: {processed}"
        elif intent == "example":
            processed = f"Please provide practical examples for: {processed}"
        elif intent == "troubleshoot":
            processed = f"Please help troubleshoot this issue: {processed}"
        
        return processed
    
    def _detect_learning_intent(self, text: str) -> str:
        """Detect the user's learning intent"""
        text_lower = text.lower()
        
        for intent, patterns in self.teaching_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return intent
        
        return "general"
    
    def _detect_learning_style(self, text: str) -> str:
        """Detect user's preferred learning style"""
        text_lower = text.lower()
        style_scores = {}
        
        for style, patterns in self.learning_style_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            style_scores[style] = score
        
        if style_scores:
            return max(style_scores, key=style_scores.get)
        
        return "general"
    
    def _identify_subject_area(self, text: str) -> str:
        """Identify the subject area the user is asking about"""
        text_lower = text.lower()
        
        subject_keywords = {
            "python": ["python", "def ", "import", "pip", "django", "flask"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "web_development": ["html", "css", "website", "frontend", "backend"],
            "data_science": ["data", "machine learning", "ai", "statistics", "pandas"],
            "algorithms": ["algorithm", "sort", "search", "complexity", "data structure"],
            "databases": ["database", "sql", "query", "table", "mysql", "postgresql"]
        }
        
        for subject, keywords in subject_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return subject
        
        return "general"
    
    async def _build_system_prompt(self) -> str:
        """Build specialized system prompt for Virtual Sir"""
        base_prompt = super()._build_system_prompt()
        
        teaching_guidelines = """

Virtual Sir Teaching Guidelines:

TEACHING APPROACH:
- Always start with a clear, simple explanation
- Break complex topics into manageable steps
- Use analogies and real-world examples
- Provide code examples when applicable
- Check for understanding at each step

RESPONSE STRUCTURE:
1. Greeting and acknowledgment
2. Clear explanation of the concept
3. Step-by-step breakdown (if applicable)
4. Practical examples or code
5. Practice exercise or suggestion
6. Encouraging closing

LEARNING STYLE ADAPTATION:
- For visual learners: Use diagrams, charts, and visual examples
- For auditory learners: Use clear verbal explanations and analogies
- For kinesthetic learners: Suggest hands-on practice and experimentation
- For reading learners: Provide detailed text explanations and documentation

ENCOURAGEMENT PATTERNS:
- "Great question! This is an important concept..."
- "You're on the right track! Let me explain..."
- "Excellent! Now let's try a practical example..."
- "Don't worry if this seems complex at first..."
- "You're making good progress! Keep practicing..."

SAFETY AND ACCURACY:
- Always provide accurate, verified information
- Encourage good coding practices
- Warn about common mistakes and pitfalls
- Suggest additional learning resources

Remember: Your goal is to make learning enjoyable, effective, and personalized to each student's needs."""
        
        return base_prompt + teaching_guidelines
    
    def _add_educational_touches(self, response: str) -> str:
        """Add educational enhancements to responses"""
        enhanced = response
        
        # Add learning objectives if not present
        if "objective" not in enhanced.lower() and len(enhanced) > 200:
            objectives = self._extract_learning_objectives(enhanced)
            if objectives:
                enhanced = f"**Learning Objectives:**\\n{objectives}\\n\\n{enhanced}"
        
        # Add practice suggestions
        if "practice" not in enhanced.lower() and "exercise" not in enhanced.lower():
            practice = self._suggest_practice_activity(enhanced)
            if practice:
                enhanced += f"\\n\\n**Practice Activity:**\\n{practice}"
        
        # Add resources
        resources = self._suggest_learning_resources(enhanced)
        if resources:
            enhanced += f"\\n\\n**Additional Resources:**\\n{resources}"
        
        # Add encouragement
        if not any(word in enhanced.lower() for word in ['great', 'excellent', 'good job']):
            encouragement = self._generate_encouragement()
            enhanced += f"\\n\\n{encouragement}"
        
        return enhanced
    
    def _extract_learning_objectives(self, response: str) -> str:
        """Extract learning objectives from response"""
        objectives = []
        
        # Look for key concepts being explained
        if "variable" in response.lower():
            objectives.append("- Understand what variables are and how to use them")
        if "function" in response.lower():
            objectives.append("- Learn how to create and use functions")
        if "loop" in response.lower():
            objectives.append("- Master loop structures for repetition")
        if "condition" in response.lower():
            objectives.append("- Understand conditional logic and decision making")
        
        return '\\n'.join(objectives) if objectives else "- Understand the core concepts being explained"
    
    def _suggest_practice_activity(self, response: str) -> str:
        """Suggest a practice activity based on the content"""
        if "python" in response.lower():
            return "Try writing a simple Python program that uses the concepts we discussed. Start with a basic example and gradually add complexity."
        elif "javascript" in response.lower():
            return "Create a small web page or Node.js script to practice these JavaScript concepts. Experiment with different variations."
        elif "algorithm" in response.lower():
            return "Implement the algorithm we discussed in your preferred programming language. Test it with different inputs to understand how it works."
        else:
            return "Practice the concepts we've covered by working on a small project or exercise. The best way to learn is by doing!"
    
    def _suggest_learning_resources(self, response: str) -> str:
        """Suggest additional learning resources"""
        resources = []
        
        if "python" in response.lower():
            resources.append("- Python Official Documentation: docs.python.org")
            resources.append("- Python Tutorial: tutorialspoint.com/python")
        elif "javascript" in response.lower():
            resources.append("- MDN Web Docs: developer.mozilla.org")
            resources.append("- JavaScript.info: javascript.info")
        elif "web" in response.lower():
            resources.append("- W3Schools: w3schools.com")
            resources.append("- freeCodeCamp: freecodecamp.org")
        
        resources.append("- Practice on platforms like LeetCode, HackerRank, or Codewars")
        
        return '\\n'.join(resources) if resources else "- Check official documentation and tutorials for the topic we discussed"
    
    def _generate_encouragement(self) -> str:
        """Generate encouraging message"""
        encouragements = [
            "Keep up the great work! Learning to code is a journey, and you're making excellent progress.",
            "You're doing fantastic! Every concept you master brings you closer to your goals.",
            "Excellent progress! Remember that even experienced developers were once beginners.",
            "Great job today! Consistent practice is the key to becoming a proficient programmer.",
            "You're on the right path! Don't hesitate to ask questions - that's how we learn best."
        ]
        
        import random
        return random.choice(encouragements)
    
    async def get_teaching_metrics(self) -> Dict[str, Any]:
        """Get teaching-specific metrics"""
        base_status = await self.get_status()
        
        teaching_metrics = {
            "concepts_taught": list(self.teaching_resources["programming_concepts"].keys()),
            "learning_paths": list(self.teaching_resources["learning_paths"].keys()),
            "teaching_style": "step-by-step, example-rich, encouraging",
            "specializations": [
                "programming_fundamentals",
                "algorithms", 
                "data_structures",
                "best_practices",
                "error_explanation"
            ],
            "safety_features": [
                "content_filtering",
                "educational_focus_only", 
                "no_harmful_guidance",
                "age_appropriate_content"
            ]
        }
        
        base_status.update(teaching_metrics)
        return base_status