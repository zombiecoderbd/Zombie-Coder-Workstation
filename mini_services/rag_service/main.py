"""
RAG Service - ZombieCoder Local AI
Document Retrieval and Vector Search
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False
import uuid
import os

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document data structure"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class ChromaManager:
    """Manage ChromaDB operations"""
    
    def __init__(self, persist_directory: str = "./data/chroma"):
        self.persist_directory = persist_directory
        self.client = None
        self.collections = {}
        
    async def initialize(self) -> bool:
        """Initialize ChromaDB client"""
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
            
            logger.info(f"📚 ChromaDB initialized with persistence at {self.persist_directory}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            return False
    
    async def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new collection"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, skipping collection creation")
            return False
        try:
            if not self.client:
                return False
            
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata or {}
            )
            
            self.collections[name] = collection
            logger.info(f"📚 Created/get collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            return False
    
    async def add_documents(self, collection_name: str, documents: List[Document]) -> bool:
        """Add documents to collection"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, skipping document addition")
            return False
        try:
            if collection_name not in self.collections:
                await self.create_collection(collection_name)
            
            collection = self.collections[collection_name]
            
            # Prepare data for insertion
            ids = [doc.id for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Add to collection
            collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"📚 Added {len(documents)} documents to collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {e}")
            return False
    
    async def search_similar(self, collection_name: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, returning empty results")
            return []
        try:
            if collection_name not in self.collections:
                logger.warning(f"Collection {collection_name} not found")
                return []
            
            collection = self.collections[collection_name]
            
            # Perform similarity search
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching in {collection_name}: {e}")
            return []
    
    async def delete_documents(self, collection_name: str, ids: List[str]) -> bool:
        """Delete documents from collection"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, skipping document deletion")
            return False
        try:
            if collection_name not in self.collections:
                return False
            
            collection = self.collections[collection_name]
            collection.delete(ids=ids)
            
            logger.info(f"🗑️ Deleted {len(ids)} documents from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents from {collection_name}: {e}")
            return False
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, returning empty info")
            return {}
        try:
            if collection_name not in self.collections:
                await self.create_collection(collection_name)
            
            collection = self.collections[collection_name]
            count = collection.count()
            
            return {
                'name': collection_name,
                'count': count,
                'metadata': collection.metadata if hasattr(collection, 'metadata') else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return {}


class RAGService:
    """RAG service for document retrieval and vector search"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 3001):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="ZombieCoder RAG Service",
            description="Document Retrieval and Vector Search"
        )
        self.chroma_manager = ChromaManager()
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
        
        @self.app.on_event("startup")
        async def startup_event():
            await self._initialize()
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self._cleanup()
        
        @self.app.get("/")
        async def root():
            return {
                "message": "📚 ZombieCoder RAG Service",
                "status": "running",
                "port": self.port
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            if not CHROMADB_AVAILABLE:
                return {
                    "status": "degraded",
                    "warning": "ChromaDB not available, RAG functionality limited",
                    "timestamp": datetime.now().isoformat()
                }
            try:
                # Test ChromaDB connection
                collections = await self._get_collections_list()
                return {
                    "status": "healthy",
                    "collections": len(collections),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        @self.app.post("/collections/{collection_name}")
        async def create_collection(collection_name: str, metadata: Optional[Dict[str, Any]] = None):
            """Create a new collection"""
            success = await self.chroma_manager.create_collection(collection_name, metadata)
            if success:
                return {"message": f"Collection {collection_name} created successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to create collection")
        
        @self.app.post("/collections/{collection_name}/documents")
        async def add_documents(collection_name: str, documents: List[Dict[str, Any]]):
            """Add documents to collection"""
            docs = []
            for doc_data in documents:
                doc = Document(
                    id=doc_data.get('id', str(uuid.uuid4())),
                    content=doc_data.get('content', ''),
                    metadata=doc_data.get('metadata', {})
                )
                docs.append(doc)
            
            success = await self.chroma_manager.add_documents(collection_name, docs)
            if success:
                return {"message": f"Added {len(docs)} documents to {collection_name}"}
            else:
                raise HTTPException(status_code=500, detail="Failed to add documents")
        
        @self.app.post("/collections/{collection_name}/search")
        async def search_documents(collection_name: str, query: Dict[str, Any]):
            """Search for similar documents"""
            search_query = query.get('query', '')
            n_results = query.get('n_results', 5)
            
            if not search_query:
                raise HTTPException(status_code=400, detail="Query is required")
            
            results = await self.chroma_manager.search_similar(collection_name, search_query, n_results)
            return {"results": results}
        
        @self.app.delete("/collections/{collection_name}/documents/{document_id}")
        async def delete_document(collection_name: str, document_id: str):
            """Delete a document from collection"""
            success = await self.chroma_manager.delete_documents(collection_name, [document_id])
            if success:
                return {"message": f"Document {document_id} deleted from {collection_name}"}
            else:
                raise HTTPException(status_code=500, detail="Failed to delete document")
        
        @self.app.get("/collections/{collection_name}/info")
        async def get_collection_info(collection_name: str):
            """Get collection information"""
            info = await self.chroma_manager.get_collection_info(collection_name)
            return info
        
        @self.app.get("/collections")
        async def list_collections():
            """List all collections"""
            collections = await self._get_collections_list()
            return {"collections": collections}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time RAG operations"""
            await websocket.accept()
            connection_id = str(id(websocket))
            self.websocket_connections[connection_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_json()
                    response = await self._handle_websocket_message(data)
                    await websocket.send_json(response)
                    
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if connection_id in self.websocket_connections:
                    del self.websocket_connections[connection_id]
                await websocket.close()
    
    async def _initialize(self):
        """Initialize RAG service"""
        success = await self.chroma_manager.initialize()
        if success:
            # Create default collections
            await self.chroma_manager.create_collection("knowledge_base")
            await self.chroma_manager.create_collection("code_snippets")
            await self.chroma_manager.create_collection("documentation")
        elif not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, RAG service running in degraded mode")
            
        self.running = True
        logger.info(f"📚 RAG service initialized on {self.host}:{self.port}")
    
    async def _cleanup(self):
        """Cleanup resources"""
        self.running = False
        logger.info("🧹 RAG service cleanup completed")
    
    async def _get_collections_list(self) -> List[str]:
        """Get list of collections"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available, returning empty collection list")
            return []
        try:
            if self.chroma_manager.client:
                collections = self.chroma_manager.client.list_collections()
                return [c.name for c in collections]
            return []
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    async def _handle_websocket_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebSocket messages"""
        try:
            action = data.get('action')
            
            if action == 'search':
                collection = data.get('collection', 'knowledge_base')
                query = data.get('query', '')
                n_results = data.get('n_results', 5)
                
                results = await self.chroma_manager.search_similar(collection, query, n_results)
                return {
                    'action': 'search_results',
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif action == 'add_document':
                collection = data.get('collection', 'knowledge_base')
                doc_data = data.get('document', {})
                
                doc = Document(
                    id=doc_data.get('id', str(uuid.uuid4())),
                    content=doc_data.get('content', ''),
                    metadata=doc_data.get('metadata', {})
                )
                
                success = await self.chroma_manager.add_documents(collection, [doc])
                return {
                    'action': 'document_added',
                    'success': success,
                    'document_id': doc.id,
                    'timestamp': datetime.now().isoformat()
                }
            
            elif action == 'get_info':
                collection = data.get('collection', 'knowledge_base')
                info = await self.chroma_manager.get_collection_info(collection)
                return {
                    'action': 'collection_info',
                    'info': info,
                    'timestamp': datetime.now().isoformat()
                }
            
            else:
                return {
                    'action': 'error',
                    'error': f'Unknown action: {action}',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            return {
                'action': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def start(self):
        """Start the RAG service"""
        if self.running:
            logger.warning("RAG service is already running")
            return
        
        try:
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            self.server = uvicorn.Server(config)
            
            logger.info(f"📚 Starting RAG service on {self.host}:{self.port}")
            await self.server.serve()
            
        except Exception as e:
            logger.error(f"❌ Failed to start RAG service: {e}")
            raise
    
    async def stop(self):
        """Stop the RAG service"""
        if not self.running:
            logger.warning("RAG service is not running")
            return
        
        logger.info("🛑 Stopping RAG service...")
        self.running = False
        
        if hasattr(self, 'server'):
            await self.server.shutdown()


async def create_rag_service(host: str = "0.0.0.0", port: int = 3001) -> RAGService:
    """Factory function to create RAG service"""
    return RAGService(host, port)


if __name__ == "__main__":
    # Run RAG service
    async def main():
        service = RAGService()
        await service.start()
    
    asyncio.run(main())