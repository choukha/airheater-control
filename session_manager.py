from typing import Optional, Dict, Any
import time
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 hour
        
    def create_session(self, username: str, role: str) -> str:
        """Create new session for user"""
        session_id = f"{username}_{int(time.time())}"
        self.sessions[session_id] = {
            "username": username,
            "role": role,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        return session_id
        
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if valid"""
        if session_id not in self.sessions:
            return None
            
        session = self.sessions[session_id]
        if self._is_session_expired(session):
            del self.sessions[session_id]
            return None
            
        # Update last activity
        session["last_activity"] = datetime.now()
        return session
        
    def end_session(self, session_id: str):
        """End user session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if self._is_session_expired(session)
        ]
        for sid in expired:
            del self.sessions[sid]
            
    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """Check if session has expired"""
        current_time = datetime.now()
        last_activity = session["last_activity"]
        return (current_time - last_activity).total_seconds() > self.session_timeout
        
    def has_permission(self, session_id: str, required_role: str) -> bool:
        """Check if session has required role"""
        session = self.get_session(session_id)
        if not session:
            return False
            
        if required_role == "guest":
            return True
        elif required_role == "operator":
            return session["role"] == "operator"
            
        return False