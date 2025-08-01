import bcrypt
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
from loguru import logger

class AuthManager:
    """Simple authentication manager for the application"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._init_auth_tables()
    
    def _init_auth_tables(self):
        """Initialize authentication tables"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'viewer',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    last_login TEXT,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    expires_at TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Create default admin user if none exists
            cursor.execute('SELECT COUNT(*) FROM users')
            if cursor.fetchone()[0] == 0:
                self.create_user('admin', 'admin123', 'admin')
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, password: str, role: str = 'viewer') -> bool:
        """Create new user"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    username,
                    self.hash_password(password),
                    role,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"User created: {username} with role {role}")
                return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user info"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password_hash, role, is_active
                FROM users
                WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if user and user['is_active'] and self.verify_password(password, user['password_hash']):
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = ? WHERE id = ?
                ''', (datetime.now().isoformat(), user['id']))
                
                # Log authentication
                self.db_manager.log_action('user_login', {
                    'user_id': user['id'],
                    'username': user['username']
                }, user['username'])
                
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                }
            
            return None
    
    def check_permission(self, user_role: str, required_role: str) -> bool:
        """Check if user has required permission"""
        role_hierarchy = {
            'viewer': 0,
            'editor': 1,
            'manager': 2,
            'admin': 3
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def login_page(self):
        """Display login page"""
        st.title("🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary")
            
            if submitted:
                user = self.authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    def logout(self):
        """Logout user"""
        if 'user' in st.session_state:
            self.db_manager.log_action('user_logout', {
                'user_id': st.session_state.user['id'],
                'username': st.session_state.user['username']
            }, st.session_state.user['username'])
            
            del st.session_state.user
            st.rerun()
    
    def require_auth(self, required_role: str = 'viewer'):
        """Decorator to require authentication"""
        if 'user' not in st.session_state:
            self.login_page()
            st.stop()
        
        if not self.check_permission(st.session_state.user['role'], required_role):
            st.error(f"Permission denied. {required_role} role required.")
            st.stop()
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current logged in user"""
        return st.session_state.get('user')