from typing import Optional, List, Dict, Any
from app.core.database import db_manager
from app.core.security import security
from app.models.schemas import UserCreate, User, UserLogin, UserUpdate
from app.core.config import settings
import sqlite3
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def create_user(user_data: UserCreate) -> Optional[User]:
        """Create a new user"""
        try:
            with db_manager.get_db_connection() as conn:
                # Check if username or email already exists
                result = conn.execute(
                    "SELECT id FROM users WHERE username = ? OR email = ?", 
                    (user_data.username, user_data.email)
                ).fetchone()
                if result:
                    return None
                
                # Hash password and generate API key
                hashed_password = security.get_password_hash(user_data.password)
                api_key = security.generate_api_key()
                api_key_hash = security.get_password_hash(api_key)
                
                # Check if user should be admin
                is_admin = user_data.email in settings.admin_emails_list
                
                # Insert user
                cursor = conn.execute("""
                    INSERT INTO users (username, email, hashed_password, is_admin, api_key, api_key_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_data.username, user_data.email, hashed_password, is_admin, api_key, api_key_hash))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                # Fetch created user
                user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
                
                return User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    is_verified=bool(user_row['is_verified']),
                    is_admin=bool(user_row['is_admin']),
                    api_key=user_row['api_key'],
                    created_at=user_row['created_at'],
                    updated_at=user_row['updated_at']
                )
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def authenticate_user(user_data: UserLogin) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            with db_manager.get_db_connection() as conn:
                user_row = conn.execute("SELECT * FROM users WHERE email = ?", (user_data.email,)).fetchone()
                
                if not user_row:
                    return None
                
                if not security.verify_password(user_data.password, user_row['hashed_password']):
                    return None
                
                return User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    is_verified=bool(user_row['is_verified']),
                    is_admin=bool(user_row['is_admin']),
                    api_key=user_row['api_key'],
                    created_at=user_row['created_at'],
                    updated_at=user_row['updated_at']
                )
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                user_row = cursor.fetchone()
                
                if not user_row:
                    return None
                
                return User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    is_verified=bool(user_row['is_verified']),
                    is_admin=bool(user_row['is_admin']),
                    api_key=user_row['api_key'],
                    created_at=user_row['created_at'],
                    updated_at=user_row['updated_at']
                )
                
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user_row = cursor.fetchone()
                
                if not user_row:
                    return None
                
                return User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    is_verified=bool(user_row['is_verified']),
                    is_admin=bool(user_row['is_admin']),
                    api_key=user_row['api_key'],
                    created_at=user_row['created_at'],
                    updated_at=user_row['updated_at']
                )
                
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    @staticmethod
    def get_user_by_api_key(api_key: str) -> Optional[User]:
        """Get user by API key"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM users WHERE api_key = ?", (api_key,))
                user_row = cursor.fetchone()
                
                if not user_row:
                    return None
                
                return User(
                    id=user_row['id'],
                    username=user_row['username'],
                    email=user_row['email'],
                    is_verified=bool(user_row['is_verified']),
                    is_admin=bool(user_row['is_admin']),
                    api_key=user_row['api_key'],
                    created_at=user_row['created_at'],
                    updated_at=user_row['updated_at']
                )
                
        except Exception as e:
            logger.error(f"Error getting user by API key: {e}")
            return None
    
    @staticmethod
    def update_user(user_id: int, user_data: UserUpdate, current_user: User) -> bool:
        """Update user information"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get current user data for password verification
                cursor.execute("SELECT hashed_password FROM users WHERE id = ?", (user_id,))
                user_row = cursor.fetchone()
                if not user_row:
                    return False
                
                updates = []
                params = []
                
                if user_data.email:
                    # Check if email is already taken by another user
                    cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (user_data.email, user_id))
                    if cursor.fetchone():
                        return False
                    updates.append("email = ?")
                    params.append(user_data.email)
                
                if user_data.new_password:
                    if not user_data.current_password:
                        return False
                    
                    # Verify current password
                    if not security.verify_password(user_data.current_password, user_row['hashed_password']):
                        return False
                    
                    updates.append("hashed_password = ?")
                    params.append(security.get_password_hash(user_data.new_password))
                
                if updates:
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(user_id)
                    
                    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    @staticmethod
    def verify_user(user_id: int) -> bool:
        """Mark user as verified"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE users SET is_verified = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (True, user_id)
                )
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return False
    
    @staticmethod
    def get_all_users(limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users (admin only)"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
                user_rows = cursor.fetchall()
                
                return [
                    User(
                        id=row['id'],
                        username=row['username'],
                        email=row['email'],
                        is_verified=bool(row['is_verified']),
                        is_admin=bool(row['is_admin']),
                        api_key=row['api_key'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in user_rows
                ]
                
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

user_service = UserService()
