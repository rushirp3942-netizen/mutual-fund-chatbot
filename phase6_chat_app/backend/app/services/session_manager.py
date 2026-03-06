"""
Session Manager for chat conversations.

Manages conversation history and context across sessions.
"""

import uuid
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Session:
    """Chat session"""
    session_id: str
    created_at: float
    last_activity: float
    messages: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class SessionManager:
    """
    Manages chat sessions with in-memory storage.
    
    For production, this should use Redis or a database.
    """
    
    def __init__(self, session_timeout: int = 3600):
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout  # seconds
    
    def create_session(self) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        now = time.time()
        
        self.sessions[session_id] = Session(
            session_id=session_id,
            created_at=now,
            last_activity=now,
            messages=[],
            metadata={}
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session expired
            if time.time() - session.last_activity > self.session_timeout:
                self.delete_session(session_id)
                return None
            
            # Update last activity
            session.last_activity = time.time()
        
        return session
    
    def add_message(self, session_id: str, role: str, content: str, **metadata):
        """Add message to session"""
        session = self.get_session(session_id)
        
        if not session:
            return False
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            **metadata
        }
        
        session.messages.append(message)
        session.last_activity = time.time()
        
        # Keep only last 20 messages to prevent memory issues
        if len(session.messages) > 20:
            session.messages = session.messages[-20:]
        
        return True
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        session = self.get_session(session_id)
        
        if not session:
            return []
        
        return session.messages[-limit:]
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def cleanup_expired(self):
        """Remove expired sessions"""
        now = time.time()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_activity > self.session_timeout
        ]
        
        for sid in expired:
            self.delete_session(sid)
        
        return len(expired)
    
    def get_stats(self) -> Dict:
        """Get session statistics"""
        return {
            'active_sessions': len(self.sessions),
            'total_messages': sum(len(s.messages) for s in self.sessions.values())
        }


# Global session manager instance
session_manager = SessionManager()
