#!/usr/bin/env python3
"""
Create default admin and demo accounts for Kale Email API Platform
"""
import sqlite3
import bcrypt
import logging
import secrets
import hashlib
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def create_default_accounts():
    """Create default admin and demo accounts"""
    try:
        # Connect to database
        conn = sqlite3.connect('kale.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@example.com",))
        if cursor.fetchone():
            logger.info("Admin user already exists")
        else:
            # Create admin user
            hashed_password = bcrypt.hashpw("Admin@2025".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            api_key = generate_api_key()
            api_key_hash = hash_api_key(api_key)
            
            cursor.execute("""
                INSERT INTO users (username, email, hashed_password, api_key, api_key_hash, is_admin, is_verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "admin",
                "admin@example.com", 
                hashed_password,
                api_key,
                api_key_hash,
                True,
                True,
                datetime.utcnow().isoformat()
            ))
            logger.info("✓ Admin user created (email: admin@example.com, password: Admin@2025)")
            logger.info(f"✓ Admin API key: {api_key}")
        
        # Check if demo user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@example.com",))
        if cursor.fetchone():
            logger.info("Demo user already exists")
        else:
            # Create demo user
            hashed_password = bcrypt.hashpw("Demio@2025".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            api_key = generate_api_key()
            api_key_hash = hash_api_key(api_key)
            
            cursor.execute("""
                INSERT INTO users (username, email, hashed_password, api_key, api_key_hash, is_admin, is_verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "demo",
                "demo@example.com",
                hashed_password,
                api_key,
                api_key_hash,
                False,
                True,
                datetime.utcnow().isoformat()
            ))
            logger.info("✓ Demo user created (email: demo@example.com, password: Demio@2025)")
            logger.info(f"✓ Demo API key: {api_key}")
        
        conn.commit()
        conn.close()
        logger.info("✓ Default accounts creation completed")
        
    except Exception as e:
        logger.error(f"✗ Failed to create default accounts: {e}")
        raise

if __name__ == "__main__":
    create_default_accounts()
