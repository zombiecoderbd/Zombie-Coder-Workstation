"""
ChromaDB Manager - ZombieCoder Local AI
Vector Database for RAG and Knowledge Management
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False
import uuid

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Vector document structure"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    collection: str = "default"


class ChromaManager:
    """ChromaDB manager for vector storage and retrieval"""
    
    def __init__(self, persist_directory: str = "./data/chroma", collection_name: str = "zombiecoder_knowledge"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize ChromaDB client and collection"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, skipping initialization")
            return False
            
        try:
            # Create persist directory
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "ZombieCoder knowledge base",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            self.initialized = True
            logger.info(f"📚 ChromaDB initialized with collection {self.collection_name} at {self.persist_directory}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            return False
    
    async def close(self):
        """Close ChromaDB connection"""
        if not CHROMADB_AVAILABLE:
            return
        # ChromaDB handles persistence automatically
        self.initialized = False
        logger.info("📚 ChromaDB connection closed")
    
    async def add_document(self, content: str, metadata: Dict[str, Any] = None, doc_id: str = None) -> str:
        """Add document to collection"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, skipping document addition")
            return ""
        if not self.initialized:
            raise RuntimeError("ChromaDB not initialized")
        
        if not doc_id:
            doc_id = str(uuid.uuid4())
        
        try:
            # Add to collection
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata or {}]
            )
            
            logger.info(f"📚 Added document {doc_id} to collection {self.collection_name}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """Add multiple documents to collection"""
        if not self.initialized:
            raise RuntimeError("ChromaDB not initialized")
        
        try:
            ids = [doc.id for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"📚 Added {len(documents)} documents to collection {self.collection_name}")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    async def search(self, query: str, n_results: int = 5, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.initialized:
            return []
        
        try:
            # Perform similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                    'distance': results['distances'][0][i] if results.get('distances') else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from collection"""
        if not self.initialized:
            return False
        
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"🗑️ Deleted document {doc_id} from collection {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def update_document(self, doc_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Update document in collection"""
        if not self.initialized:
            return False
        
        try:
            # Get existing document
            existing = self.collection.get(ids=[doc_id])
            if not existing['ids']:
                logger.warning(f"Document {doc_id} not found for update")
                return False
            
            # Update content or metadata
            update_content = content or existing['documents'][0]
            update_metadata = metadata or existing['metadatas'][0]
            
            # Delete and re-add (ChromaDB update pattern)
            self.collection.delete(ids=[doc_id])
            self.collection.add(
                ids=[doc_id],
                documents=[update_content],
                metadatas=[update_metadata]
            )
            
            logger.info(f"🔄 Updated document {doc_id} in collection {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        if not self.initialized:
            return None
        
        try:
            result = self.collection.get(ids=[doc_id])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0] if result['metadatas'][0] else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        if not self.initialized:
            return {}
        
        try:
            count = self.collection.count()
            return {
                'name': self.collection_name,
                'count': count,
                'metadata': self.collection.metadata if hasattr(self.collection, 'metadata') else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    async def create_collection(self, name: str, metadata: Dict[str, Any] = None) -> bool:
        """Create a new collection"""
        if not self.client:
            return False
        
        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata or {}
            )
            
            logger.info(f"📚 Created/get collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            return False
    
    async def list_collections(self) -> List[str]:
        """List all collections"""
        if not self.client:
            return []
        
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []


async def create_chroma_manager(persist_directory: str = "./data/chroma", collection_name: str = "zombiecoder_knowledge") -> ChromaManager:
    """Factory function to create ChromaDB manager"""
    if not CHROMADB_AVAILABLE:
        logger.warning("ChromaDB not available, returning uninitialized manager")
        return ChromaManager(persist_directory, collection_name)
    chroma_manager = ChromaManager(persist_directory, collection_name)
    await chroma_manager.initialize()
    return chroma_manager