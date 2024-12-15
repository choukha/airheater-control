import sqlite3
import hashlib
import logging
from typing import Optional
import streamlit as st

class UserAuth:
    def __init__(self, db_path: Optional[str] = None):
        """Initialize user authentication system"""
        self.db_path = db_path or st.secrets["db_path"]
        self.setup_users_table()
        
    def setup_users_table(self):
        """Create users table and initialize default users from secrets"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create users table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'guest',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_login DATETIME,
                        failed_attempts INTEGER DEFAULT 0
                    )
                ''')
                
                # Add users from secrets if they don't exist
                cursor = conn.cursor()
                for user_type, user_info in st.secrets.get("users", {}).items():
                    username = user_info["username"]
                    password = user_info["password"]
                    role = user_info["role"]
                    
                    # Check if user exists
                    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
                    if cursor.fetchone()[0] == 0:
                        # Add user with hashed password
                        self.add_user(username, password, role)
                        logging.info(f"Added default user: {username} with role: {role}")
                
        except sqlite3.Error as e:
            logging.error(f"Error setting up users table: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Create SHA-256 hash of password"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def add_user(self, username: str, password: str, role: str = 'guest') -> bool:
        """Add new user with hashed password"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                password_hash = self.hash_password(password)
                conn.execute(
                    """INSERT INTO users 
                        (username, password_hash, role, failed_attempts) 
                       VALUES (?, ?, ?, 0)""",
                    (username, password_hash, role)
                )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verify_user(self, username: str, password: str) -> Optional[str]:
        """Verify username and password, return role if successful"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get user info
                cursor.execute(
                    """SELECT password_hash, role, failed_attempts 
                       FROM users WHERE username = ?""",
                    (username,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                stored_hash, role, failed_attempts = result
                
                # Check if account is locked
                max_attempts = st.secrets.get("max_failed_attempts", 3)
                if failed_attempts >= max_attempts:
                    logging.warning(f"Account locked for user: {username}")
                    return None
                
                # Verify password
                if stored_hash == self.hash_password(password):
                    # Reset failed attempts and update last login
                    conn.execute(
                        """UPDATE users 
                           SET failed_attempts = 0, 
                               last_login = CURRENT_TIMESTAMP 
                           WHERE username = ?""",
                        (username,)
                    )
                    return role
                else:
                    # Increment failed attempts
                    conn.execute(
                        "UPDATE users SET failed_attempts = failed_attempts + 1 WHERE username = ?",
                        (username,)
                    )
                    return None
                
        except sqlite3.Error as e:
            logging.error(f"Error verifying user: {e}")
            return None
    
    def reset_failed_attempts(self, username: str) -> bool:
        """Reset failed login attempts for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE users SET failed_attempts = 0 WHERE username = ?",
                    (username,)
                )
            return True
        except sqlite3.Error:
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user's password"""
        if not self.verify_user(username, old_password):
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                new_hash = self.hash_password(new_password)
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (new_hash, username)
                )
                return True
        except sqlite3.Error:
            return False
    
    def get_user_info(self, username: str) -> Optional[dict]:
        """Get user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT role, created_at, last_login, failed_attempts 
                       FROM users WHERE username = ?""",
                    (username,)
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        "role": result[0],
                        "created_at": result[1],
                        "last_login": result[2],
                        "failed_attempts": result[3]
                    }
                return None
                
        except sqlite3.Error:
            return None

def test_auth():
    """Test authentication functionality"""
    auth = UserAuth()
    
    # Test with correct credentials
    role = auth.verify_user(
        st.secrets["users"]["operator"]["username"],
        st.secrets["users"]["operator"]["password"]
    )
    print(f"Operator login test: {'Success' if role == 'operator' else 'Failed'}")
    
    # Test with incorrect password
    role = auth.verify_user(
        st.secrets["users"]["operator"]["username"],
        "wrong_password"
    )
    print(f"Wrong password test: {'Success' if role is None else 'Failed'}")

if __name__ == "__main__":
    test_auth()