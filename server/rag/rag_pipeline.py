"""
RAG Pipeline - Retrieval-Augmented Generation with Validation
Handles document retrieval, context building, and hallucination prevention
"""

import asyncio
import logging
import json
import re
import hashlib
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import time
from pathlib import Path
import sqlite3
import aiohttp
from abc import ABC, abstractmethod


@dataclass
class DocumentChunk:
    """Represents a chunk of document"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    similarity_score: float = 0.0


@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__ + ".OpenAIEmbedding")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "input": text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data["data"][0]["embedding"]
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI embedding error: {error_text}")
                        return []
        
        except Exception as e:
            self.logger.error(f"Error getting OpenAI embedding: {e}")
            return []


class SimpleEmbeddingProvider(EmbeddingProvider):
    """Simple hash-based embedding for demo purposes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".SimpleEmbedding")
        self.embedding_size = 384
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate simple embedding based on text hash"""
        try:
            # Create a simple hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_hex = hash_obj.hexdigest()
            
            # Convert hash to float values
            embedding = []
            for i in range(0, len(hash_hex), 2):
                hex_pair = hash_hex[i:i+2]
                float_val = int(hex_pair, 16) / 255.0
                embedding.append(float_val)
            
            # Pad or truncate to desired size
            while len(embedding) < self.embedding_size:
                embedding.append(0.0)
            
            return embedding[:self.embedding_size]
        
        except Exception as e:
            self.logger.error(f"Error generating simple embedding: {e}")
            return [0.0] * self.embedding_size


class VectorStore:
    """Simple in-memory vector store for demo purposes"""
    
    def __init__(self):
        self.documents: List[DocumentChunk] = []
        self.logger = logging.getLogger(__name__ + ".VectorStore")
    
    async def add_document(self, chunk: DocumentChunk):
        """Add document to store"""
        self.documents.append(chunk)
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[DocumentChunk]:
        """Search for similar documents"""
        if not query_embedding:
            return []
        
        # Calculate similarity scores
        scored_docs = []
        for doc in self.documents:
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                doc.similarity_score = similarity
                scored_docs.append(doc)
        
        # Sort by similarity and return top_k
        scored_docs.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_docs[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)


class ContentValidator:
    """Validates content for safety and accuracy"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__ + ".ContentValidator")
        
        # Validation rules
        self.blocked_patterns = config.get('blocked_patterns', [])
        self.max_length = config.get('max_length', 5000)
        self.similarity_threshold = config.get('similarity_threshold', 0.8)
        
    async def validate_input(self, content: str) -> ValidationResult:
        """Validate input content"""
        issues = []
        suggestions = []
        
        # Length check
        if len(content) > self.max_length:
            issues.append(f"Content too long (max {self.max_length} characters)")
            suggestions.append("Consider breaking down into smaller parts")
        
        # Blocked patterns check
        for pattern in self.blocked_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Content contains blocked pattern: {pattern}")
                suggestions.append("Remove sensitive information")
        
        # Basic safety checks
        if any(word in content.lower() for word in ['password', 'secret', 'token', 'key']):
            issues.append("Content may contain sensitive information")
            suggestions.append("Remove or redact sensitive information")
        
        is_valid = len(issues) == 0
        confidence = 1.0 - (len(issues) * 0.2)  # Simple confidence calculation
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=max(0.0, confidence),
            issues=issues,
            suggestions=suggestions
        )
    
    async def validate_output(self, 
                             output: str, 
                             context: List[DocumentChunk]) -> ValidationResult:
        """Validate output content against context"""
        issues = []
        suggestions = []
        
        # Length check
        if len(output) > self.max_length:
            issues.append(f"Output too long (max {self.max_length} characters)")
        
        # Fact-check against context (simplified)
        if context:
            context_text = " ".join([doc.content for doc in context])
            similarity = self._text_similarity(output, context_text)
            
            if similarity < self.similarity_threshold:
                issues.append("Output may not be well-supported by context")
                suggestions.append("Ensure response is based on provided context")
        
        # Hallucination checks
        hallucination_indicators = [
            "I believe", "I think", "probably", "might be", "could be"
        ]
        
        for indicator in hallucination_indicators:
            if indicator.lower() in output.lower():
                issues.append(f"Potential hallucination indicator: '{indicator}'")
                suggestions.append("Use more definitive language based on context")
        
        is_valid = len(issues) == 0
        confidence = 1.0 - (len(issues) * 0.15)
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=max(0.0, confidence),
            issues=issues,
            suggestions=suggestions
        )
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)


class RAGPipeline:
    """
    Main RAG Pipeline that orchestrates retrieval and generation
    """
    
    def __init__(self, config: Dict[str, Any], db_config: Dict[str, Any]):
        self.config = config
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.embedding_provider: Optional[EmbeddingProvider] = None
        self.vector_store: Optional[VectorStore] = None
        self.validator: Optional[ContentValidator] = None
        
        # Configuration
        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.max_context_length = config.get('max_context_length', 4000)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.max_retrieved_docs = config.get('max_retrieved_docs', 5)
        
        # Cache
        self.cache: Dict[str, Any] = {}
        
    async def initialize(self) -> bool:
        """Initialize the RAG pipeline"""
        try:
            self.logger.info("Initializing RAG Pipeline...")
            
            # Initialize embedding provider
            await self._initialize_embedding_provider()
            
            # Initialize vector store
            self.vector_store = VectorStore()
            
            # Initialize validator
            validation_config = self.config.get('validation', {})
            self.validator = ContentValidator(validation_config)
            
            # Load initial documents
            await self._load_sample_documents()
            
            self.logger.info("RAG Pipeline initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Pipeline: {e}")
            return False
    
    async def _initialize_embedding_provider(self):
        """Initialize embedding provider"""
        embedding_model = self.config.get('embedding_model', 'simple')
        
        if embedding_model == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.embedding_provider = OpenAIEmbeddingProvider(api_key)
            else:
                self.logger.warning("OpenAI API key not found, using simple embeddings")
                self.embedding_provider = SimpleEmbeddingProvider()
        else:
            self.embedding_provider = SimpleEmbeddingProvider()
        
        self.logger.info(f"Using embedding provider: {type(self.embedding_provider).__name__}")
    
    async def _load_sample_documents(self):
        """Load sample documents for demonstration"""
        sample_docs = [
            {
                "content": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
                "metadata": {"source": "python_basics", "category": "programming"}
            },
            {
                "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. Common algorithms include neural networks, decision trees, and support vector machines.",
                "metadata": {"source": "ml_intro", "category": "ai"}
            },
            {
                "content": "Web development involves creating websites and web applications. It typically includes frontend development (HTML, CSS, JavaScript) and backend development (server-side programming, databases).",
                "metadata": {"source": "web_dev", "category": "web"}
            },
            {
                "content": "Data structures are ways of organizing and storing data efficiently. Common data structures include arrays, linked lists, stacks, queues, trees, and graphs. Each has specific use cases and performance characteristics.",
                "metadata": {"source": "data_structures", "category": "computer_science"}
            },
            {
                "content": "Version control systems like Git help developers track changes in code over time. Git allows multiple developers to work on the same project simultaneously and merge their changes efficiently.",
                "metadata": {"source": "git_basics", "category": "tools"}
            }
        ]
        
        for doc in sample_docs:
            await self._add_document(doc['content'], doc['metadata'])
        
        self.logger.info(f"Loaded {len(sample_docs)} sample documents")
    
    async def _add_document(self, content: str, metadata: Dict[str, Any]):
        """Add document to vector store"""
        # Split into chunks
        chunks = self._split_text(content)
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await self.embedding_provider.get_embedding(chunk)
            
            # Create document chunk
            doc_chunk = DocumentChunk(
                id=f"{metadata.get('source', 'unknown')}_{i}",
                content=chunk,
                metadata={**metadata, "chunk_index": i},
                embedding=embedding
            )
            
            # Add to vector store
            await self.vector_store.add_document(doc_chunk)
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to split at word boundary
            while end > start and text[end] not in '.!?\\n ':
                end -= 1
            
            if end == start:
                end = start + self.chunk_size
            
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if end > self.chunk_overlap else end
        
        return chunks
    
    async def retrieve_context(self, 
                             query: str, 
                             agent_id: str, 
                             session_context: Dict[str, Any]) -> str:
        """
        Retrieve relevant context for a query
        """
        try:
            # Validate input
            if self.validator:
                validation_result = await self.validator.validate_input(query)
                if not validation_result.is_valid:
                    self.logger.warning(f"Input validation failed: {validation_result.issues}")
            
            # Check cache first
            cache_key = f"{hashlib.md5(query.encode()).hexdigest()}_{agent_id}"
            if cache_key in self.cache:
                self.logger.debug("Using cached context")
                return self.cache[cache_key]
            
            # Generate query embedding
            query_embedding = await self.embedding_provider.get_embedding(query)
            
            if not query_embedding:
                self.logger.warning("Failed to generate query embedding")
                return ""
            
            # Search for similar documents
            similar_docs = await self.vector_store.search(
                query_embedding, 
                top_k=self.max_retrieved_docs
            )
            
            # Filter by similarity threshold
            relevant_docs = [
                doc for doc in similar_docs 
                if doc.similarity_score >= self.similarity_threshold
            ]
            
            if not relevant_docs:
                self.logger.debug("No relevant documents found")
                return ""
            
            # Build context string
            context_parts = []
            context_length = 0
            
            for doc in relevant_docs:
                if context_length + len(doc.content) > self.max_context_length:
                    break
                
                context_parts.append(f"[{doc.metadata.get('source', 'unknown')}]\\n{doc.content}")
                context_length += len(doc.content)
            
            context = "\\n\\n".join(context_parts)
            
            # Cache the result
            self.cache[cache_key] = context
            
            self.logger.info(f"Retrieved {len(relevant_docs)} documents for context")
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            return ""
    
    async def validate_response(self, 
                               response: str, 
                               context: List[DocumentChunk]) -> ValidationResult:
        """Validate model response"""
        if not self.validator:
            return ValidationResult(True, 1.0, [], [])
        
        return await self.validator.validate_output(response, context)
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add new document to the knowledge base"""
        try:
            await self._add_document(content, metadata)
            
            # Clear cache since documents changed
            self.cache.clear()
            
            self.logger.info(f"Added document with metadata: {metadata}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding document: {e}")
            return False
    
    async def search_documents(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search documents and return results"""
        try:
            query_embedding = await self.embedding_provider.get_embedding(query)
            
            if not query_embedding:
                return []
            
            similar_docs = await self.vector_store.search(query_embedding, top_k)
            
            results = []
            for doc in similar_docs:
                results.append({
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "similarity_score": doc.similarity_score
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get RAG pipeline status"""
        doc_count = len(self.vector_store.documents) if self.vector_store else 0
        
        return {
            "initialized": self.vector_store is not None,
            "embedding_provider": type(self.embedding_provider).__name__ if self.embedding_provider else None,
            "document_count": doc_count,
            "cache_size": len(self.cache),
            "config": {
                "chunk_size": self.chunk_size,
                "similarity_threshold": self.similarity_threshold,
                "max_retrieved_docs": self.max_retrieved_docs
            }
        }
    
    async def shutdown(self):
        """Shutdown the RAG pipeline"""
        self.logger.info("Shutting down RAG Pipeline...")
        self.cache.clear()
        self.logger.info("RAG Pipeline shutdown complete")