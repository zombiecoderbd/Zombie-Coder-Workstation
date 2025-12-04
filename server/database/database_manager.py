"""
SQLite Database Manager - ZombieCoder Local AI
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import asyncio
import sqlite3
import json
import logging
import aiosqlite
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class SessionRecord:
    """Session record"""
    session_id: str
    created_at: datetime
    last_active: datetime
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ConversationRecord:
    """Conversation record"""
    conversation_id: str
    session_id: str
    timestamp: datetime
    user_input: str
    agent_response: str
    agent_id: str
    metadata: Dict[str, Any] = None


@dataclass
class AgentMetricsRecord:
    """Agent metrics record"""
    metric_id: str
    agent_id: str
    timestamp: datetime
    response_time: float
    tokens_used: int
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class DatabaseManager:
    """SQLite database manager for ZombieCoder"""
    
    def __init__(self, db_path: str = "./data/zombiecoder.db"):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize database connection and tables"""
        try:
            # Create data directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to database
            self.db = await aiosqlite.connect(self.db_path)
            
            # Enable foreign keys
            await self.db.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            await self._create_tables()
            
            # Commit changes
            await self.db.commit()
            
            self.initialized = True
            logger.info(f"🗄️ SQLite database initialized at {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            return False
    
    async def _create_tables(self):
        """Create database tables"""
        # Sessions table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                metadata TEXT
            )
        """)
        
        # Conversations table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        # Agent metrics table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                metric_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time REAL NOT NULL,
                tokens_used INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                metadata TEXT
            )
        """)
        
        # Create indexes
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_last_active 
            ON sessions (last_active)
        """)
        
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_session 
            ON conversations (session_id, timestamp)
        """)
        
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_agent 
            ON conversations (agent_id, timestamp)
        """)
        
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_agent 
            ON agent_metrics (agent_id, timestamp)
        """)
        
        logger.info("🗄️ Database tables created")
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
            self.initialized = False
            logger.info("🔌 Database connection closed")
    
    # --- Session Management ---
    
    async def create_session(self, session_id: str = None, user_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """Create a new session"""
        if not self.initialized:
            raise RuntimeError("Database not initialized")
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            await self.db.execute(
                """
                INSERT INTO sessions (session_id, user_id, metadata, created_at, last_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (session_id, user_id, json.dumps(metadata) if metadata else None)
            )
            await self.db.commit()
            logger.info(f"➕ Created session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def update_session_activity(self, session_id: str):
        """Update session last active timestamp"""
        if not self.initialized:
            return
        
        try:
            await self.db.execute(
                "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE session_id = ?",
                (session_id,)
            )
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    async def get_session(self, session_id: str) -> Optional[SessionRecord]:
        """Get session by ID"""
        if not self.initialized:
            return None
        
        try:
            cursor = await self.db.execute(
                "SELECT session_id, created_at, last_active, user_id, metadata FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                return SessionRecord(
                    session_id=row[0],
                    created_at=datetime.fromisoformat(row[1]) if isinstance(row[1], str) else row[1],
                    last_active=datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2],
                    user_id=row[3],
                    metadata=json.loads(row[4]) if row[4] else None
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session and related data"""
        if not self.initialized:
            return False
        
        try:
            # Delete conversations first (foreign key constraint)
            await self.db.execute(
                "DELETE FROM conversations WHERE session_id = ?",
                (session_id,)
            )
            
            # Delete session
            await self.db.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            
            await self.db.commit()
            logger.info(f"🗑️ Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    # --- Conversation Management ---
    
    async def add_conversation(self, session_id: str, user_input: str, agent_response: str, agent_id: str, metadata: Dict[str, Any] = None) -> str:
        """Add conversation record"""
        if not self.initialized:
            raise RuntimeError("Database not initialized")
        
        conversation_id = str(uuid.uuid4())
        
        try:
            await self.db.execute(
                """
                INSERT INTO conversations 
                (conversation_id, session_id, user_input, agent_response, agent_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (conversation_id, session_id, user_input, agent_response, agent_id, json.dumps(metadata) if metadata else None)
            )
            await self.db.commit()
            logger.info(f"💬 Added conversation for session: {session_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error adding conversation: {e}")
            raise
    
    async def get_conversations(self, session_id: str, limit: int = 50) -> List[ConversationRecord]:
        """Get conversations for session"""
        if not self.initialized:
            return []
        
        try:
            cursor = await self.db.execute(
                """
                SELECT conversation_id, session_id, timestamp, user_input, agent_response, agent_id, metadata
                FROM conversations 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (session_id, limit)
            )
            
            rows = await cursor.fetchall()
            conversations = []
            
            for row in rows:
                conversations.append(ConversationRecord(
                    conversation_id=row[0],
                    session_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2],
                    user_input=row[3],
                    agent_response=row[4],
                    agent_id=row[5],
                    metadata=json.loads(row[6]) if row[6] else None
                ))
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    # --- Metrics Management ---
    
    async def add_agent_metric(self, agent_id: str, response_time: float, tokens_used: int, success: bool, error_message: str = None, metadata: Dict[str, Any] = None) -> str:
        """Add agent metrics record"""
        if not self.initialized:
            raise RuntimeError("Database not initialized")
        
        metric_id = str(uuid.uuid4())
        
        try:
            await self.db.execute(
                """
                INSERT INTO agent_metrics 
                (metric_id, agent_id, response_time, tokens_used, success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (metric_id, agent_id, response_time, tokens_used, success, error_message, json.dumps(metadata) if metadata else None)
            )
            await self.db.commit()
            logger.info(f"📊 Added metrics for agent: {agent_id}")
            return metric_id
            
        except Exception as e:
            logger.error(f"Error adding agent metrics: {e}")
            raise
    
    async def get_agent_metrics(self, agent_id: str, hours: int = 24) -> List[AgentMetricsRecord]:
        """Get agent metrics for recent period"""
        if not self.initialized:
            return []
        
        try:
            cursor = await self.db.execute(
                """
                SELECT metric_id, agent_id, timestamp, response_time, tokens_used, success, error_message, metadata
                FROM agent_metrics 
                WHERE agent_id = ? AND timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
                """.format(hours),
                (agent_id,)
            )
            
            rows = await cursor.fetchall()
            metrics = []
            
            for row in rows:
                metrics.append(AgentMetricsRecord(
                    metric_id=row[0],
                    agent_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2],
                    response_time=row[3],
                    tokens_used=row[4],
                    success=bool(row[5]),
                    error_message=row[6],
                    metadata=json.loads(row[7]) if row[7] else None
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting agent metrics: {e}")
            return []
    
    # --- Analytics ---
    
    async def get_session_count(self) -> int:
        """Get total session count"""
        if not self.initialized:
            return 0
        
        try:
            cursor = await self.db.execute("SELECT COUNT(*) FROM sessions")
            row = await cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0
    
    async def get_conversation_count(self) -> int:
        """Get total conversation count"""
        if not self.initialized:
            return 0
        
        try:
            cursor = await self.db.execute("SELECT COUNT(*) FROM conversations")
            row = await cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            logger.error(f"Error getting conversation count: {e}")
            return 0
    
    async def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get agent performance statistics"""
        if not self.initialized:
            return {}
        
        try:
            cursor = await self.db.execute(
                """
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(response_time) as avg_response_time,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
                    AVG(tokens_used) as avg_tokens
                FROM agent_metrics 
                WHERE agent_id = ?
                """,
                (agent_id,)
            )
            
            row = await cursor.fetchone()
            if row:
                total_requests = row[0] or 0
                successful_requests = row[2] or 0
                success_rate = (successful_requests / max(total_requests, 1)) * 100
                
                return {
                    'total_requests': total_requests,
                    'avg_response_time': row[1] or 0,
                    'success_rate': success_rate,
                    'avg_tokens': row[3] or 0,
                    'successful_requests': successful_requests
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting agent performance: {e}")
            return {}


async def create_database_manager(db_path: str = "./data/zombiecoder.db") -> DatabaseManager:
    """Factory function to create database manager"""
    db_manager = DatabaseManager(db_path)
    await db_manager.initialize()
    return db_manager