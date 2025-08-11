import sqlite3
import redis
from typing import Optional, Dict, Any, List
from app.core.config import settings
import logging
import threading
import time
import json
from contextlib import contextmanager
from datetime import datetime, timedelta
import hashlib
import queue
import asyncio

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    """Professional SQLite connection pool with thread safety"""
    
    def __init__(self, database_path: str, pool_size: int = 20):
        self.database_path = database_path
        self.pool_size = pool_size
        self.pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.total_connections = 0
        
        # Initialize the pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            if conn:
                self.pool.put(conn)
                self.total_connections += 1
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create a new database connection with optimized settings"""
        try:
            conn = sqlite3.connect(
                self.database_path,
                timeout=settings.DATABASE_TIMEOUT,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            conn.row_factory = sqlite3.Row
            
            # SQLite optimizations for enterprise usage
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=memory")
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB
            conn.execute("PRAGMA foreign_keys=ON")
            
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            # Try to get connection from pool
            try:
                conn = self.pool.get_nowait()
            except queue.Empty:
                # Pool exhausted, create new connection
                conn = self._create_connection()
                if not conn:
                    raise Exception("Unable to create database connection")
            
            # Test connection
            conn.execute("SELECT 1")
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                try:
                    conn.close()
                except:
                    pass
                conn = None
            raise
        finally:
            # Return connection to pool
            if conn:
                try:
                    # Reset connection state
                    conn.rollback()
                    
                    # Return to pool if pool not full
                    try:
                        self.pool.put_nowait(conn)
                    except queue.Full:
                        conn.close()
                except:
                    try:
                        conn.close()
                    except:
                        pass

class RedisConnectionPool:
    """Professional Redis connection pool"""
    
    def __init__(self):
        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            retry_on_timeout=True,
            health_check_interval=30,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
    
    def get_client(self) -> redis.Redis:
        """Get Redis client"""
        return self.client
    
    def health_check(self) -> bool:
        """Check Redis health"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

class DatabaseManager:
    """Professional database manager"""
    
    def __init__(self):
        self.db_path = settings.database_url_formatted.replace("sqlite:///", "")
        self.connection_pool = DatabaseConnectionPool(self.db_path, settings.DATABASE_POOL_SIZE)
        self.redis_pool = RedisConnectionPool()
        
        # Initialize database schema
        self.init_database()
        
        # Start health monitoring
        self._start_health_monitoring()
        
        logger.info("Database manager initialized successfully")
    
    def init_database(self):
        """Initialize SQLite database with Professional schema"""
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys=ON")
                
                # Users table with enhanced security
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        is_verified BOOLEAN DEFAULT FALSE,
                        is_admin BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        api_key TEXT UNIQUE NOT NULL,
                        api_key_hash TEXT UNIQUE NOT NULL,
                        failed_login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP NULL,
                        last_login TIMESTAMP NULL,
                        last_activity TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_ip VARCHAR(45),
                        email_verification_token TEXT,
                        email_verification_expires TIMESTAMP,
                        password_reset_token TEXT,
                        password_reset_expires TIMESTAMP
                    )
                """)
                
                # SMTP configurations table with encryption
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS smtp_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(255) DEFAULT 'Default',
                        smtp_host VARCHAR(255) NOT NULL,
                        smtp_port INTEGER NOT NULL,
                        smtp_username VARCHAR(255) NOT NULL,
                        smtp_password TEXT NOT NULL,
                        use_tls BOOLEAN DEFAULT TRUE,
                        use_ssl BOOLEAN DEFAULT FALSE,
                        from_email VARCHAR(255) NOT NULL,
                        from_name VARCHAR(255),
                        is_active BOOLEAN DEFAULT TRUE,
                        is_verified BOOLEAN DEFAULT FALSE,
                        last_used TIMESTAMP NULL,
                        max_send_rate INTEGER DEFAULT 10,
                        daily_limit INTEGER DEFAULT 1000,
                        connection_timeout INTEGER DEFAULT 30,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Email templates table with versioning
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        template_id VARCHAR(100) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        subject TEXT NOT NULL,
                        html_content TEXT NOT NULL,
                        text_content TEXT,
                        variables JSON,
                        default_variables JSON,
                        is_public BOOLEAN DEFAULT FALSE,
                        is_system_template BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        category VARCHAR(100),
                        description TEXT,
                        version INTEGER DEFAULT 1,
                        parent_template_id INTEGER NULL,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (parent_template_id) REFERENCES email_templates (id),
                        UNIQUE(user_id, template_id, version)
                    )
                """)
                
                # Email logs table with detailed tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        template_id VARCHAR(100) NOT NULL,
                        smtp_config_id INTEGER,
                        recipient_email VARCHAR(255) NOT NULL,
                        recipient_name VARCHAR(255),
                        subject TEXT NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        error_message TEXT,
                        error_code VARCHAR(10),
                        message_id VARCHAR(255),
                        delivery_status VARCHAR(50),
                        opened_at TIMESTAMP NULL,
                        clicked_at TIMESTAMP NULL,
                        variables_used JSON,
                        processing_time_ms INTEGER,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        delivered_at TIMESTAMP NULL,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (smtp_config_id) REFERENCES smtp_configs (id)
                    )
                """)
                
                # API usage logs table with detailed metrics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_usage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        api_key_used VARCHAR(100),
                        endpoint VARCHAR(255) NOT NULL,
                        method VARCHAR(10) NOT NULL,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        request_data TEXT,
                        response_status INTEGER,
                        response_time_ms INTEGER,
                        bytes_sent INTEGER,
                        bytes_received INTEGER,
                        error_message TEXT,
                        rate_limited BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                    )
                """)
                
                # User sessions table for session management
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Email bounces table for tracking bounced emails
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_bounces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email VARCHAR(255) NOT NULL,
                        bounce_type VARCHAR(50) NOT NULL,
                        bounce_reason TEXT,
                        bounce_code VARCHAR(10),
                        smtp_response TEXT,
                        user_id INTEGER,
                        template_id VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
                        UNIQUE(email, bounce_type)
                    )
                """)
                
                # Email delivery tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_delivery_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id INTEGER NOT NULL,
                        recipient_email VARCHAR(255) NOT NULL,
                        template_id VARCHAR(100),
                        status VARCHAR(50) DEFAULT 'pending',
                        delivery_attempts INTEGER DEFAULT 0,
                        last_attempt_at TIMESTAMP,
                        delivered_at TIMESTAMP,
                        opened_at TIMESTAMP,
                        clicked_at TIMESTAMP,
                        bounced_at TIMESTAMP,
                        bounce_reason TEXT,
                        tracking_data JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Rate limiting tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rate_limit_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        resource_type VARCHAR(50) NOT NULL,
                        resource_key VARCHAR(255) NOT NULL,
                        current_count INTEGER DEFAULT 0,
                        limit_value INTEGER NOT NULL,
                        window_start TIMESTAMP NOT NULL,
                        window_end TIMESTAMP NOT NULL,
                        reset_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        UNIQUE(user_id, resource_type, resource_key, window_start)
                    )
                """)
                
                # System audit logs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        action VARCHAR(100) NOT NULL,
                        resource_type VARCHAR(50),
                        resource_id VARCHAR(100),
                        old_values JSON,
                        new_values JSON,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # User API keys table for additional API key management
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_api_keys (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        api_key VARCHAR(255) NOT NULL,
                        api_key_hash VARCHAR(255) UNIQUE NOT NULL,
                        key_name VARCHAR(255) NOT NULL,
                        description TEXT,
                        permissions JSON,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_used TIMESTAMP NULL,
                        usage_count INTEGER DEFAULT 0,
                        rate_limit INTEGER DEFAULT 1000,
                        expires_at TIMESTAMP NULL,
                        deleted_at TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Ensure deleted_at column exists for existing tables
                try:
                    cursor.execute("SELECT deleted_at FROM user_api_keys LIMIT 1")
                except Exception:
                    # Column doesn't exist, add it
                    cursor.execute("ALTER TABLE user_api_keys ADD COLUMN deleted_at TIMESTAMP NULL")
                    logger.info("Added missing deleted_at column to user_api_keys table")
                
                # System settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT,
                        description TEXT,
                        is_public BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create comprehensive indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                    "CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key)",
                    "CREATE INDEX IF NOT EXISTS idx_users_api_key_hash ON users(api_key_hash)",
                    "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_id ON user_api_keys(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_user_api_keys_api_key_hash ON user_api_keys(api_key_hash)",
                    "CREATE INDEX IF NOT EXISTS idx_user_api_keys_active ON user_api_keys(is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_user_api_keys_expires ON user_api_keys(expires_at)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_smtp_user_id ON smtp_configs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_smtp_active ON smtp_configs(is_active)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_templates_user_id ON email_templates(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_templates_template_id ON email_templates(template_id)",
                    "CREATE INDEX IF NOT EXISTS idx_templates_public ON email_templates(is_public)",
                    "CREATE INDEX IF NOT EXISTS idx_templates_system ON email_templates(is_system_template)",
                    "CREATE INDEX IF NOT EXISTS idx_templates_category ON email_templates(category)",
                    "CREATE INDEX IF NOT EXISTS idx_templates_active ON email_templates(is_active)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_email_logs_user_id ON email_logs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at)",
                    "CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status)",
                    "CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email)",
                    "CREATE INDEX IF NOT EXISTS idx_email_logs_template ON email_logs(template_id)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage_logs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage_logs(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage_logs(endpoint)",
                    "CREATE INDEX IF NOT EXISTS idx_api_usage_ip ON api_usage_logs(ip_address)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)",
                    "CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)",
                    "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)",
                    
                    "CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key)",
                    
                    # Indexes for email_bounces table
                    "CREATE INDEX IF NOT EXISTS idx_email_bounces_email ON email_bounces(email)",
                    "CREATE INDEX IF NOT EXISTS idx_email_bounces_type ON email_bounces(bounce_type)",
                    "CREATE INDEX IF NOT EXISTS idx_email_bounces_created_at ON email_bounces(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_email_bounces_user_id ON email_bounces(user_id)",
                    
                    # Indexes for email_delivery_tracking table
                    "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_message_id ON email_delivery_tracking(message_id)",
                    "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_user_id ON email_delivery_tracking(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_recipient ON email_delivery_tracking(recipient_email)",
                    "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_status ON email_delivery_tracking(status)",
                    "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_created_at ON email_delivery_tracking(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_template_id ON email_delivery_tracking(template_id)",
                    
                    # Indexes for rate_limit_tracking table
                    "CREATE INDEX IF NOT EXISTS idx_rate_limit_user_id ON rate_limit_tracking(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_rate_limit_resource ON rate_limit_tracking(resource_type, resource_key)",
                    "CREATE INDEX IF NOT EXISTS idx_rate_limit_window ON rate_limit_tracking(window_start, window_end)",
                    "CREATE INDEX IF NOT EXISTS idx_rate_limit_reset_at ON rate_limit_tracking(reset_at)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                # Run database migrations for existing installations
                self._run_migrations(conn)
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _run_migrations(self, conn):
        """Run database migrations for existing installations"""
        try:
            cursor = conn.cursor()
            
            # Check users table and add missing columns
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns to users table
            missing_user_columns = [
                ("verified_at", "TIMESTAMP NULL"),
                ("suspended_at", "TIMESTAMP NULL"),
                ("suspension_reason", "TEXT NULL"),
                ("total_emails_sent", "INTEGER DEFAULT 0"),
                ("emails_sent_today", "INTEGER DEFAULT 0"),
                ("last_api_call", "TIMESTAMP NULL")
            ]
            
            for column_name, column_def in missing_user_columns:
                if column_name not in user_columns:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                    logger.info(f"Added missing column {column_name} to users table")
            
            # Check if smtp_configs table exists and add missing columns
            cursor.execute("PRAGMA table_info(smtp_configs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns if they don't exist
            missing_columns = [
                ("max_send_rate", "INTEGER DEFAULT 10"),
                ("daily_limit", "INTEGER DEFAULT 1000"),
                ("connection_timeout", "INTEGER DEFAULT 30")
            ]
            
            for column_name, column_def in missing_columns:
                if column_name not in columns:
                    cursor.execute(f"ALTER TABLE smtp_configs ADD COLUMN {column_name} {column_def}")
                    logger.info(f"Added missing column {column_name} to smtp_configs table")
            
            # Fix smtp_password column name if needed (from smtp_password_encrypted to smtp_password)
            if "smtp_password_encrypted" in columns and "smtp_password" not in columns:
                # Create new table with correct column name
                cursor.execute("""
                    CREATE TABLE smtp_configs_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(255) DEFAULT 'Default',
                        smtp_host VARCHAR(255) NOT NULL,
                        smtp_port INTEGER NOT NULL,
                        smtp_username VARCHAR(255) NOT NULL,
                        smtp_password TEXT NOT NULL,
                        use_tls BOOLEAN DEFAULT TRUE,
                        use_ssl BOOLEAN DEFAULT FALSE,
                        from_email VARCHAR(255) NOT NULL,
                        from_name VARCHAR(255),
                        is_active BOOLEAN DEFAULT TRUE,
                        is_verified BOOLEAN DEFAULT FALSE,
                        last_used TIMESTAMP NULL,
                        max_send_rate INTEGER DEFAULT 10,
                        daily_limit INTEGER DEFAULT 1000,
                        connection_timeout INTEGER DEFAULT 30,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                
                # Copy data from old table
                cursor.execute("""
                    INSERT INTO smtp_configs_new 
                    (id, user_id, name, smtp_host, smtp_port, smtp_username, smtp_password, 
                     use_tls, use_ssl, from_email, from_name, is_active, is_verified, 
                     last_used, created_at, updated_at)
                    SELECT id, user_id, name, smtp_host, smtp_port, smtp_username, smtp_password_encrypted,
                           use_tls, use_ssl, from_email, from_name, is_active, is_verified,
                           last_used, created_at, updated_at
                    FROM smtp_configs
                """)
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE smtp_configs")
                cursor.execute("ALTER TABLE smtp_configs_new RENAME TO smtp_configs")
                
                logger.info("Migrated smtp_configs table to fix column names")
            
            # Check email_templates table and add missing columns
            cursor.execute("PRAGMA table_info(email_templates)")
            template_columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns to email_templates table
            missing_template_columns = [
                ("default_variables", "JSON")
            ]
            
            for column_name, column_def in missing_template_columns:
                if column_name not in template_columns:
                    cursor.execute(f"ALTER TABLE email_templates ADD COLUMN {column_name} {column_def}")
                    logger.info(f"Added missing column {column_name} to email_templates table")
            
            # Check api_usage_logs table and add missing columns
            cursor.execute("PRAGMA table_info(api_usage_logs)")
            api_log_columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns to api_usage_logs table
            missing_api_log_columns = [
                ("username", "VARCHAR(255)"),
                ("template_id", "VARCHAR(255)"),
                ("request_id", "VARCHAR(255)"),
                ("client_ip", "VARCHAR(45)"),
                ("status_code", "INTEGER"),
                ("response_message", "TEXT")
            ]
            
            for column_name, column_def in missing_api_log_columns:
                if column_name not in api_log_columns:
                    cursor.execute(f"ALTER TABLE api_usage_logs ADD COLUMN {column_name} {column_def}")
                    logger.info(f"Added missing column {column_name} to api_usage_logs table")
            
            # Make user_id nullable if it's currently NOT NULL
            if api_log_columns:
                cursor.execute("PRAGMA table_info(api_usage_logs)")
                for column_info in cursor.fetchall():
                    if column_info[1] == 'user_id' and column_info[3] == 1:  # NOT NULL constraint
                        # Need to recreate table to remove NOT NULL constraint
                        cursor.execute("""
                            CREATE TABLE api_usage_logs_new (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER,
                                username VARCHAR(255),
                                template_id VARCHAR(255),
                                api_key_used VARCHAR(100),
                                endpoint VARCHAR(255) NOT NULL,
                                method VARCHAR(10) NOT NULL,
                                client_ip VARCHAR(45),
                                ip_address VARCHAR(45),
                                user_agent TEXT,
                                request_data TEXT,
                                response_status INTEGER,
                                status_code INTEGER,
                                response_time_ms INTEGER,
                                bytes_sent INTEGER,
                                bytes_received INTEGER,
                                error_message TEXT,
                                response_message TEXT,
                                rate_limited BOOLEAN DEFAULT FALSE,
                                request_id VARCHAR(255),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                            )
                        """)
                        
                        # Copy existing data
                        cursor.execute("""
                            INSERT INTO api_usage_logs_new 
                            (id, user_id, api_key_used, endpoint, method, ip_address, user_agent,
                             request_data, response_status, response_time_ms, bytes_sent, bytes_received,
                             error_message, rate_limited, created_at)
                            SELECT id, user_id, api_key_used, endpoint, method, ip_address, user_agent,
                                   request_data, response_status, response_time_ms, bytes_sent, bytes_received,
                                   error_message, rate_limited, created_at
                            FROM api_usage_logs
                        """)
                        
                        # Drop old table and rename
                        cursor.execute("DROP TABLE api_usage_logs")
                        cursor.execute("ALTER TABLE api_usage_logs_new RENAME TO api_usage_logs")
                        
                        logger.info("Migrated api_usage_logs table to allow NULL user_id")
                        break
            
            # Create new tables if they don't exist (for existing installations)
            new_tables = [
                ("email_bounces", """
                    CREATE TABLE IF NOT EXISTS email_bounces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email VARCHAR(255) NOT NULL,
                        bounce_type VARCHAR(50) NOT NULL,
                        bounce_reason TEXT,
                        bounce_code VARCHAR(10),
                        smtp_response TEXT,
                        user_id INTEGER,
                        template_id VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
                        UNIQUE(email, bounce_type)
                    )
                """),
                ("email_delivery_tracking", """
                    CREATE TABLE IF NOT EXISTS email_delivery_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id INTEGER NOT NULL,
                        recipient_email VARCHAR(255) NOT NULL,
                        template_id VARCHAR(100),
                        status VARCHAR(50) DEFAULT 'pending',
                        delivery_attempts INTEGER DEFAULT 0,
                        last_attempt_at TIMESTAMP,
                        delivered_at TIMESTAMP,
                        opened_at TIMESTAMP,
                        clicked_at TIMESTAMP,
                        bounced_at TIMESTAMP,
                        bounce_reason TEXT,
                        tracking_data JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """),
                ("rate_limit_tracking", """
                    CREATE TABLE IF NOT EXISTS rate_limit_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        resource_type VARCHAR(50) NOT NULL,
                        resource_key VARCHAR(255) NOT NULL,
                        current_count INTEGER DEFAULT 0,
                        limit_value INTEGER NOT NULL,
                        window_start TIMESTAMP NOT NULL,
                        window_end TIMESTAMP NOT NULL,
                        reset_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        UNIQUE(user_id, resource_type, resource_key, window_start)
                    )
                """)
            ]
            
            for table_name, create_sql in new_tables:
                try:
                    # Check if table exists
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    if not cursor.fetchone():
                        cursor.execute(create_sql)
                        logger.info(f"Created missing table: {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to create table {table_name}: {e}")
            
            # Create missing indexes for new tables
            new_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_email_bounces_email ON email_bounces(email)",
                "CREATE INDEX IF NOT EXISTS idx_email_bounces_type ON email_bounces(bounce_type)",
                "CREATE INDEX IF NOT EXISTS idx_email_bounces_created_at ON email_bounces(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_email_bounces_user_id ON email_bounces(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_message_id ON email_delivery_tracking(message_id)",
                "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_user_id ON email_delivery_tracking(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_recipient ON email_delivery_tracking(recipient_email)",
                "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_status ON email_delivery_tracking(status)",
                "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_created_at ON email_delivery_tracking(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_delivery_tracking_template_id ON email_delivery_tracking(template_id)",
                "CREATE INDEX IF NOT EXISTS idx_rate_limit_user_id ON rate_limit_tracking(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_rate_limit_resource ON rate_limit_tracking(resource_type, resource_key)",
                "CREATE INDEX IF NOT EXISTS idx_rate_limit_window ON rate_limit_tracking(window_start, window_end)",
                "CREATE INDEX IF NOT EXISTS idx_rate_limit_reset_at ON rate_limit_tracking(reset_at)"
            ]
            
            for index_sql in new_indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            # Don't raise exception to prevent startup failure
            pass
    
    def _start_health_monitoring(self):
        """Start background health monitoring"""
        def health_monitor():
            while True:
                try:
                    # Check Redis health
                    if not self.redis_pool.health_check():
                        logger.warning("Redis health check failed")
                    
                    # Check database connectivity
                    with self.connection_pool.get_connection() as conn:
                        conn.execute("SELECT 1")
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start health monitoring in background thread
        health_thread = threading.Thread(target=health_monitor, daemon=True)
        health_thread.start()
    
    def get_db_connection(self):
        """Get database connection from pool"""
        return self.connection_pool.get_connection()
    
    def get_redis_client(self) -> redis.Redis:
        """Get Redis client"""
        return self.redis_pool.get_client()
    
    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        """Execute database query with proper error handling"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.lastrowid
                    
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
    def insert_audit_log(self, user_id: Optional[int], action: str, resource_type: str = None, 
                        resource_id: str = None, old_values: Dict = None, new_values: Dict = None,
                        ip_address: str = None, user_agent: str = None):
        """Insert audit log entry"""
        try:
            self.execute_query("""
                INSERT INTO audit_logs 
                (user_id, action, resource_type, resource_id, old_values, new_values, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, action, resource_type, resource_id,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                ip_address, user_agent
            ))
        except Exception as e:
            logger.error(f"Failed to insert audit log: {e}")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            self.execute_query("""
                DELETE FROM user_sessions 
                WHERE expires_at < CURRENT_TIMESTAMP OR is_active = FALSE
            """)
            logger.info("Expired sessions cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            stats = {}
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # User statistics
                cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE is_active = 1")
                stats['total_users'] = cursor.fetchone()['total_users']
                
                cursor.execute("SELECT COUNT(*) as verified_users FROM users WHERE is_verified = 1 AND is_active = 1")
                stats['verified_users'] = cursor.fetchone()['verified_users']
                
                # Email statistics
                cursor.execute("SELECT COUNT(*) as total_emails FROM email_logs")
                stats['total_emails'] = cursor.fetchone()['total_emails']
                
                cursor.execute("""
                    SELECT COUNT(*) as emails_today 
                    FROM email_logs 
                    WHERE DATE(sent_at) = DATE('now')
                """)
                stats['emails_today'] = cursor.fetchone()['emails_today']
                
                # Template statistics
                cursor.execute("SELECT COUNT(*) as total_templates FROM email_templates WHERE is_active = 1")
                stats['total_templates'] = cursor.fetchone()['total_templates']
                
                cursor.execute("SELECT COUNT(*) as system_templates FROM email_templates WHERE is_system_template = 1 AND is_active = 1")
                stats['system_templates'] = cursor.fetchone()['system_templates']
                
                # API usage statistics
                cursor.execute("""
                    SELECT COUNT(*) as api_calls_today 
                    FROM api_usage_logs 
                    WHERE DATE(created_at) = DATE('now')
                """)
                stats['api_calls_today'] = cursor.fetchone()['api_calls_today']
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def optimize_database(self):
        """Optimize database performance"""
        try:
            with self.get_db_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            logger.info("Database optimized")
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")

# Global database manager instance
db_manager = DatabaseManager()
