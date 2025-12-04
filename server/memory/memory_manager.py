"""
Memory Manager for ZombieCoder
Handles auto-session memory with short-term and long-term context support
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class MemoryManager:
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.storage_type = config.get('storage', 'sqlite')
        self.db_path = config.get('path', 'data/memory.db')
        self.max_context = config.get('max_context', 5)
        self.language = config.get('language', 'bn')
        self.long_term_notes = config.get('long_term_notes', True)
        
        if self.enabled:
            self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize the storage system"""
        if self.storage_type == 'sqlite':
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables"""
        cursor = self.conn.cursor()
        
        # Session memory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                context TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                context_type TEXT DEFAULT 'short_term'
            )
        ''')
        
        # Long-term notes table
        if self.long_term_notes:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS long_term_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    note_title TEXT NOT NULL,
                    note_content TEXT NOT NULL,
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        self.conn.commit()
    
    async def store_session_context(self, session_id: str, context: Dict) -> bool:
        """Store session context"""
        if not self.enabled:
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO session_memory (session_id, context, context_type)
                VALUES (?, ?, ?)
            ''', (session_id, json.dumps(context), 'short_term'))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing session context: {e}")
            return False
    
    async def get_session_context(self, session_id: str) -> List[Dict]:
        """Retrieve session context"""
        if not self.enabled:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT context, timestamp FROM session_memory 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, self.max_context))
            
            rows = cursor.fetchall()
            contexts = []
            
            for row in rows:
                context = json.loads(row[0])
                context['timestamp'] = row[1]
                contexts.append(context)
            
            return contexts
        except Exception as e:
            print(f"Error retrieving session context: {e}")
            return []
    
    async def store_long_term_note(self, user_id: str, title: str, content: str, tags: List[str] = None) -> bool:
        """Store long-term note (botgachh)"""
        if not self.enabled or not self.long_term_notes:
            return False
            
        try:
            cursor = self.conn.cursor()
            tags_str = ','.join(tags) if tags else None
            
            cursor.execute('''
                INSERT INTO long_term_notes (user_id, note_title, note_content, tags)
                VALUES (?, ?, ?, ?)
            ''', (user_id, title, content, tags_str))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error storing long-term note: {e}")
            return False
    
    async def get_long_term_notes(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve long-term notes"""
        if not self.enabled or not self.long_term_notes:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT note_title, note_content, tags, created_at, updated_at 
                FROM long_term_notes 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            notes = []
            
            for row in rows:
                note = {
                    'title': row[0],
                    'content': row[1],
                    'tags': row[2].split(',') if row[2] else [],
                    'created_at': row[3],
                    'updated_at': row[4]
                }
                notes.append(note)
            
            return notes
        except Exception as e:
            print(f"Error retrieving long-term notes: {e}")
            return []
    
    async def close(self):
        """Close the memory manager"""
        if hasattr(self, 'conn'):
            self.conn.close()

def create_memory_manager(config: Dict) -> MemoryManager:
    """Factory function to create memory manager"""
    return MemoryManager(config)