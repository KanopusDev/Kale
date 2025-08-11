"""
Enterprise-grade Email Service for Kale Platform
Production-ready SMTP handling with proper SSL/TLS and connection management
"""

import asyncio
import aiosmtplib
import smtplib
import ssl
import socket
import logging
import json
import uuid
import re
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple, Set
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from threading import Lock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid
import certifi

from app.core.database import db_manager
from app.models.schemas import SMTPConfig, SMTPConfigCreate, EmailLog
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolEntry:
    """SMTP connection pool entry with metadata"""
    connection: aiosmtplib.SMTP
    created_at: datetime
    last_used: datetime
    usage_count: int = 0
    is_healthy: bool = True

@dataclass
class SMTPConnectionConfig:
    """Normalized SMTP connection configuration"""
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    use_tls: bool
    use_ssl: bool
    timeout: int = 30
    
    def __post_init__(self):
        """Validate and normalize configuration"""
        # Normalize host
        self.host = str(self.host).strip()
        if not self.host:
            raise ValueError("SMTP host is required")
        
        # Validate port
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid SMTP port: {self.port}")
        
        # Auto-configure SSL/TLS based on port if not explicitly set
        if self.port == 465 and not self.use_ssl and not self.use_tls:
            self.use_ssl = True
            self.use_tls = False
        elif self.port in [587, 25] and not self.use_ssl and not self.use_tls:
            self.use_ssl = False
            self.use_tls = True
    
    @property
    def connection_key(self) -> str:
        """Generate unique connection pool key"""
        auth_hash = ""
        if self.username:
            auth_hash = hashlib.md5(f"{self.username}:{self.password or ''}".encode()).hexdigest()[:8]
        return f"{self.host}:{self.port}:{self.use_ssl}:{self.use_tls}:{auth_hash}"

class SMTPConnectionManager:
    """Thread-safe SMTP connection pool manager"""
    
    def __init__(self, max_pool_size: int = 20, connection_timeout: int = 30, pool_cleanup_interval: int = 300):
        self._pool: Dict[str, ConnectionPoolEntry] = {}
        self._pool_lock = Lock()
        self._max_pool_size = max_pool_size
        self._connection_timeout = connection_timeout
        self._pool_cleanup_interval = pool_cleanup_interval
        self._last_cleanup = time.time()
    
    def _cleanup_stale_connections(self) -> None:
        """Remove stale and unhealthy connections from pool"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._pool_cleanup_interval:
            return
        
        with self._pool_lock:
            stale_keys = []
            for key, entry in self._pool.items():
                # Remove connections that haven't been used in 10 minutes or are unhealthy
                if (current_time - entry.last_used.timestamp() > 600 or 
                    not entry.is_healthy or
                    entry.usage_count > 1000):  # Prevent connection reuse issues
                    stale_keys.append(key)
            
            for key in stale_keys:
                entry = self._pool.pop(key, None)
                if entry and entry.connection:
                    try:
                        asyncio.create_task(entry.connection.quit())
                    except Exception as e:
                        logger.debug(f"Error closing stale connection: {e}")
            
            self._last_cleanup = current_time
            if stale_keys:
                logger.info(f"Cleaned up {len(stale_keys)} stale SMTP connections")
    
    async def _create_connection(self, config: SMTPConnectionConfig) -> aiosmtplib.SMTP:
        """Create a new SMTP connection with proper SSL/TLS configuration and enhanced authentication"""
        # Create SSL context with secure defaults
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.set_ciphers('DEFAULT:!aNULL:!eNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK')
        
        # Use same environment check as sync test
        if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == "development":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        logger.info(f"Creating async SMTP connection to {config.host}:{config.port}")
        
        smtp = None
        
        try:
            if config.use_ssl:
                # Direct SSL connection (port 465)
                logger.info("Using SSL connection for async SMTP")
                smtp = aiosmtplib.SMTP(
                    hostname=config.host.strip(),
                    port=config.port,
                    timeout=config.timeout,
                    use_tls=True,
                    tls_context=ssl_context
                )
            elif config.use_tls:
                # STARTTLS connection (port 587/25) - aiosmtplib handles this differently
                logger.info("Using STARTTLS connection for async SMTP")
                smtp = aiosmtplib.SMTP(
                    hostname=config.host.strip(),
                    port=config.port,
                    timeout=config.timeout,
                    start_tls=True,  # This tells aiosmtplib to use STARTTLS automatically
                    tls_context=ssl_context
                )
            else:
                # Plain connection
                logger.info("Using plain connection for async SMTP")
                smtp = aiosmtplib.SMTP(
                    hostname=config.host.strip(),
                    port=config.port,
                    timeout=config.timeout,
                    use_tls=False,
                    tls_context=ssl_context
                )
            
            # Connect to server - aiosmtplib will handle STARTTLS automatically if start_tls=True
            logger.info("Connecting to SMTP server...")
            await smtp.connect()
            
            # Send EHLO command
            logger.info("Sending EHLO command...")
            await smtp.ehlo()
            
            # No need to call starttls manually - aiosmtplib handles it automatically
            
            # Authenticate if credentials provided - use same method as sync test
            if config.username and config.password:
                logger.info(f"Authenticating async SMTP with username: {config.username}")
                
                # Clean up credentials the same way as in test
                username = config.username.strip()
                password = config.password.strip()
                
                try:
                    # Use the same authentication approach as the sync test
                    await smtp.login(username, password)
                    logger.info("Async SMTP authentication successful")
                except Exception as auth_error:
                    logger.error(f"Async SMTP authentication failed: {auth_error}")
                    # Provide the same detailed error handling as sync test
                    error_msg = str(auth_error)
                    if "535" in error_msg:
                        if "gmail" in config.host.lower():
                            raise ConnectionError("Authentication failed. For Gmail, ensure you're using an App Password, not your regular password.")
                        elif "outlook" in config.host.lower() or "hotmail" in config.host.lower():
                            raise ConnectionError("Authentication failed. For Outlook/Hotmail, ensure proper authentication settings.")
                        else:
                            raise ConnectionError(f"Authentication failed: Invalid username or password. Error: {error_msg}")
                    else:
                        raise ConnectionError(f"Authentication failed: {error_msg}")
            
            # Test connection with NOOP
            logger.info("Testing async SMTP connection with NOOP...")
            await smtp.noop()
            logger.info("Async SMTP connection established successfully")
            
            return smtp
            
        except Exception as e:
            logger.error(f"Failed to create async SMTP connection: {e}")
            if smtp:
                try:
                    await smtp.quit()
                except:
                    pass
            raise ConnectionError(f"Failed to establish SMTP connection: {e}")
    
    @asynccontextmanager
    async def get_connection(self, config: SMTPConnectionConfig):
        """Get a pooled SMTP connection with automatic cleanup"""
        self._cleanup_stale_connections()
        
        connection_key = config.connection_key
        connection = None
        pool_entry = None
        
        # Try to get existing connection from pool
        with self._pool_lock:
            if connection_key in self._pool:
                pool_entry = self._pool[connection_key]
                connection = pool_entry.connection
        
        # Test existing connection
        if connection and pool_entry:
            try:
                await connection.noop()
                pool_entry.last_used = datetime.utcnow()
                pool_entry.usage_count += 1
                pool_entry.is_healthy = True
                
                yield connection
                return
                
            except Exception as e:
                logger.debug(f"Existing SMTP connection failed health check: {e}")
                pool_entry.is_healthy = False
                
                # Remove unhealthy connection from pool
                with self._pool_lock:
                    self._pool.pop(connection_key, None)
                
                try:
                    await connection.quit()
                except:
                    pass
                
                connection = None
        
        # Create new connection
        try:
            connection = await self._create_connection(config)
            
            # Add to pool if there's space
            with self._pool_lock:
                if len(self._pool) < self._max_pool_size:
                    self._pool[connection_key] = ConnectionPoolEntry(
                        connection=connection,
                        created_at=datetime.utcnow(),
                        last_used=datetime.utcnow(),
                        usage_count=1,
                        is_healthy=True
                    )
            
            yield connection
            
        except Exception as e:
            if connection:
                try:
                    await connection.quit()
                except:
                    pass
            raise
        
        finally:
            # Update pool entry if connection is still in pool
            with self._pool_lock:
                if connection_key in self._pool:
                    self._pool[connection_key].last_used = datetime.utcnow()

class EmailService:
    """Enterprise-grade email service with robust SMTP handling"""
    
    def __init__(self):
        self.connection_manager = SMTPConnectionManager()
        self._delivery_tracking: Dict[str, Dict] = {}
        self._bounce_tracking: Set[str] = set()
        
        # Load bounce list from database
        self._load_bounce_list()
    
    def _load_bounce_list(self) -> None:
        """Load email bounce list from database"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT email FROM email_bounces 
                    WHERE bounce_type = 'hard' AND created_at > ?
                """, (datetime.utcnow() - timedelta(days=30),))
                
                for row in cursor.fetchall():
                    self._bounce_tracking.add(row[0].lower())
                    
        except Exception as e:
            logger.warning(f"Failed to load bounce list: {e}")
    
    @staticmethod
    def _encrypt_password(password: str) -> str:
        """Encrypt password for database storage"""
        if not password:
            return ""
        
        # Use a simple encoding for now - in production, use proper encryption
        import base64
        return base64.b64encode(password.encode('utf-8')).decode('ascii')
    
    @staticmethod
    def _decrypt_password(encrypted_password: str) -> str:
        """Decrypt password from database"""
        if not encrypted_password:
            return ""
        
        try:
            import base64
            return base64.b64decode(encrypted_password.encode('ascii')).decode('utf-8')
        except Exception:
            # Fallback for unencrypted passwords
            return encrypted_password
    
    def _validate_email_address(self, email: str) -> bool:
        """Validate email address format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
    def _validate_smtp_config(self, config: SMTPConfigCreate) -> Tuple[bool, str]:
        """Validate SMTP configuration"""
        if not config.smtp_host or not config.smtp_host.strip():
            return False, "SMTP host is required"
        
        if not isinstance(config.smtp_port, int) or not (1 <= config.smtp_port <= 65535):
            return False, f"Invalid SMTP port: {config.smtp_port}"
        
        if not self._validate_email_address(config.from_email):
            return False, "Invalid from email address"
        
        # Validate common SMTP configurations
        if config.smtp_port == 465 and not config.use_tls:
            logger.warning("Port 465 typically requires SSL/TLS")
        elif config.smtp_port in [587, 25] and config.use_tls is False:
            logger.warning("Ports 587/25 typically use STARTTLS")
        
        return True, "Configuration valid"
    
    def create_smtp_config(self, user_id: int, config_data: SMTPConfigCreate) -> Optional[SMTPConfig]:
        """Create and store SMTP configuration"""
        try:
            # Validate configuration
            is_valid, error_msg = self._validate_smtp_config(config_data)
            if not is_valid:
                logger.error(f"Invalid SMTP config: {error_msg}")
                return None
            
            with db_manager.get_db_connection() as conn:
                # Deactivate existing configs
                conn.execute(
                    "UPDATE smtp_configs SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,)
                )
                
                # Encrypt password
                encrypted_password = self._encrypt_password(config_data.smtp_password)
                
                # Insert new configuration
                cursor = conn.execute("""
                    INSERT INTO smtp_configs 
                    (user_id, smtp_host, smtp_port, smtp_username, smtp_password, 
                     use_tls, from_email, from_name, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    user_id,
                    config_data.smtp_host.strip(),
                    config_data.smtp_port,
                    config_data.smtp_username.strip() if config_data.smtp_username else None,
                    encrypted_password,
                    1 if config_data.use_tls else 0,
                    config_data.from_email.strip(),
                    config_data.from_name.strip() if config_data.from_name else None
                ))
                
                config_id = cursor.lastrowid
                conn.commit()
                
                # Return created configuration
                return SMTPConfig(
                    id=config_id,
                    user_id=user_id,
                    smtp_host=config_data.smtp_host.strip(),
                    smtp_port=config_data.smtp_port,
                    smtp_username=config_data.smtp_username.strip() if config_data.smtp_username else "",
                    smtp_password=config_data.smtp_password,  # Return unencrypted for immediate use
                    use_tls=config_data.use_tls,
                    from_email=config_data.from_email.strip(),
                    from_name=config_data.from_name.strip() if config_data.from_name else "",
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to create SMTP config: {e}")
            return None
    
    def get_user_smtp_config(self, user_id: int) -> Optional[SMTPConfig]:
        """Retrieve user's active SMTP configuration"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, user_id, smtp_host, smtp_port, smtp_username, smtp_password,
                           use_tls, from_email, from_name, is_active, created_at, updated_at
                    FROM smtp_configs 
                    WHERE user_id = ? AND is_active = 1 
                    ORDER BY created_at DESC LIMIT 1
                """, (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Decrypt password
                decrypted_password = self._decrypt_password(row[5])
                
                return SMTPConfig(
                    id=row[0],
                    user_id=row[1],
                    smtp_host=row[2],
                    smtp_port=row[3],
                    smtp_username=row[4] or "",
                    smtp_password=decrypted_password,
                    use_tls=bool(row[6]),
                    from_email=row[7],
                    from_name=row[8] or "",
                    is_active=bool(row[9]),
                    created_at=row[10]
                )
                
        except Exception as e:
            logger.error(f"Failed to get SMTP config: {e}")
            return None
    
    def test_smtp_connection(self, config: SMTPConfig) -> Tuple[bool, str]:
        """Test SMTP connection with enhanced error handling"""
        try:
            # Create connection configuration
            smtp_config = SMTPConnectionConfig(
                host=config.smtp_host.strip(),
                port=config.smtp_port,
                username=config.smtp_username.strip() if config.smtp_username else "",
                password=config.smtp_password,
                use_tls=config.use_tls,
                use_ssl=config.smtp_port == 465,
                timeout=30
            )
            
            # Test synchronous connection with enhanced SSL handling
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.set_ciphers('DEFAULT:!aNULL:!eNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK')
            
            if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == "development":
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            server = None
            
            try:
                logger.info(f"Testing SMTP connection to {smtp_config.host}:{smtp_config.port}")
                
                if smtp_config.use_ssl:
                    # SSL connection (port 465)
                    logger.info("Using SSL connection")
                    server = smtplib.SMTP_SSL(
                        smtp_config.host, 
                        smtp_config.port, 
                        context=ssl_context,
                        timeout=smtp_config.timeout
                    )
                else:
                    # Plain or STARTTLS connection
                    logger.info("Using plain/STARTTLS connection")
                    server = smtplib.SMTP(
                        smtp_config.host, 
                        smtp_config.port,
                        timeout=smtp_config.timeout
                    )
                    
                    if smtp_config.use_tls:
                        logger.info("Starting TLS encryption")
                        server.starttls(context=ssl_context)
                
                # Test EHLO/HELO
                server.ehlo()
                
                # Authenticate if credentials provided
                if smtp_config.username and smtp_config.password:
                    logger.info(f"Authenticating with username: {smtp_config.username}")
                    
                    # Clean up credentials
                    username = smtp_config.username.strip()
                    password = smtp_config.password.strip()
                    
                    # Handle special authentication cases
                    try:
                        server.login(username, password)
                        logger.info("SMTP authentication successful")
                    except smtplib.SMTPAuthenticationError as auth_error:
                        error_msg = str(auth_error)
                        logger.error(f"SMTP authentication failed: {error_msg}")
                        
                        # Provide helpful error messages
                        if "535" in error_msg:
                            if "gmail" in smtp_config.host.lower():
                                return False, "Authentication failed. For Gmail, ensure you're using an App Password, not your regular password. Enable 2FA and generate an App Password in your Google Account settings."
                            elif "outlook" in smtp_config.host.lower() or "hotmail" in smtp_config.host.lower():
                                return False, "Authentication failed. For Outlook/Hotmail, ensure 'Less secure app access' is enabled or use OAuth2. Check your account security settings."
                            else:
                                return False, f"Authentication failed: Invalid username or password. Please verify your credentials. Error: {error_msg}"
                        else:
                            return False, f"Authentication failed: {error_msg}"
                else:
                    logger.info("No authentication credentials provided")
                
                # Test with NOOP
                server.noop()
                server.quit()
                
                logger.info("SMTP connection test successful")
                return True, "SMTP connection and authentication successful"
                
            except smtplib.SMTPAuthenticationError as e:
                error_msg = str(e)
                logger.error(f"SMTP authentication error: {error_msg}")
                
                # Provide specific guidance based on the error
                if "535" in error_msg:
                    return False, f"Authentication failed: Invalid credentials. Please check your username and password. For Gmail, use App Passwords. Error: {error_msg}"
                elif "534" in error_msg:
                    return False, f"Authentication mechanism not supported. Try enabling 'Less secure app access' or use App Passwords. Error: {error_msg}"
                else:
                    return False, f"Authentication failed: {error_msg}"
                    
            except smtplib.SMTPConnectError as e:
                logger.error(f"SMTP connection error: {e}")
                return False, f"Connection failed: Unable to connect to {smtp_config.host}:{smtp_config.port}. Check host and port settings. Error: {str(e)}"
                
            except smtplib.SMTPServerDisconnected as e:
                logger.error(f"SMTP server disconnected: {e}")
                return False, f"Server disconnected unexpectedly. This may be due to firewall or network issues. Error: {str(e)}"
                
            except ssl.SSLError as e:
                logger.error(f"SSL error: {e}")
                ssl_error = str(e)
                if "certificate verify failed" in ssl_error.lower():
                    return False, f"SSL certificate verification failed. This may be due to self-signed certificates or outdated certificates. Error: {ssl_error}"
                else:
                    return False, f"SSL/TLS error: {ssl_error}. Try toggling SSL/TLS settings or check if the server supports the chosen encryption method."
                    
            except socket.timeout:
                logger.error("SMTP connection timeout")
                return False, f"Connection timeout after {smtp_config.timeout} seconds. Check your network connection and firewall settings."
                
            except socket.gaierror as e:
                logger.error(f"DNS resolution error: {e}")
                return False, f"Cannot resolve hostname '{smtp_config.host}'. Please check the SMTP host address."
                
            except ConnectionRefusedError:
                logger.error("Connection refused")
                return False, f"Connection refused by {smtp_config.host}:{smtp_config.port}. Check if the port is correct and not blocked by firewall."
                
            except Exception as e:
                logger.error(f"Unexpected SMTP error: {e}")
                return False, f"Unexpected error during connection test: {str(e)}"
            
            finally:
                if server:
                    try:
                        server.quit()
                    except Exception:
                        pass
            
        except Exception as e:
            logger.error(f"SMTP connection test error: {e}")
            return False, f"Connection test failed: {str(e)}"
    
    def _replace_variables(self, content: str, variables: Optional[Dict[str, Any]]) -> str:
        """Replace template variables in content"""
        if not variables:
            return content
        
        try:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))
            return content
        except Exception as e:
            logger.warning(f"Variable replacement error: {e}")
            return content
    
    def _create_email_message(
        self, 
        smtp_config: SMTPConfig,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> MIMEMultipart:
        """Create email message with proper headers"""
        
        # Create multipart message
        message = MIMEMultipart("alternative")
        
        # Set basic headers
        message["Subject"] = subject
        message["From"] = formataddr((smtp_config.from_name or "", smtp_config.from_email))
        message["To"] = recipient
        message["Message-ID"] = make_msgid()
        message["Date"] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Add tracking headers
        message["X-Kale-Version"] = getattr(settings, 'APP_VERSION', '1.0.0')
        message["X-Mailer"] = f"Kale Email API v{getattr(settings, 'APP_VERSION', '1.0.0')}"
        
        # Add custom headers
        if custom_headers:
            for header_name, header_value in custom_headers.items():
                message[header_name] = header_value
        
        # Add text content if provided
        if text_content:
            text_part = MIMEText(text_content, "plain", "utf-8")
            message.attach(text_part)
        
        # Add HTML content
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(html_part)
        
        return message
    
    async def send_email(
        self,
        smtp_config: SMTPConfig,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str]:
        """Send email with robust error handling and connection management"""
        
        # Validate recipient
        if not self._validate_email_address(recipient):
            return False, "Invalid recipient email address"
        
        # Check bounce list
        if recipient.lower() in self._bounce_tracking:
            return False, "Recipient is on bounce list"
        
        try:
            # Replace variables in content
            processed_subject = self._replace_variables(subject, variables)
            processed_html = self._replace_variables(html_content, variables)
            processed_text = self._replace_variables(text_content, variables) if text_content else None
            
            # Create connection configuration
            connection_config = SMTPConnectionConfig(
                host=smtp_config.smtp_host,
                port=smtp_config.smtp_port,
                username=smtp_config.smtp_username,
                password=smtp_config.smtp_password,
                use_tls=smtp_config.use_tls,
                use_ssl=smtp_config.smtp_port == 465,
                timeout=30
            )
            
            # Create email message
            message = self._create_email_message(
                smtp_config=smtp_config,
                recipient=recipient,
                subject=processed_subject,
                html_content=processed_html,
                text_content=processed_text,
                custom_headers=custom_headers
            )
            
            # Send email using connection pool
            async with self.connection_manager.get_connection(connection_config) as smtp:
                await smtp.send_message(message)
            
            logger.info(f"Email sent successfully to {recipient}")
            return True, "Email sent successfully"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {recipient}: {error_msg}")
            
            # Categorize errors for better user experience
            if "authentication" in error_msg.lower():
                return False, "SMTP authentication failed. Please check your credentials."
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                return False, "Connection to SMTP server failed. Please check your settings."
            elif "ssl" in error_msg.lower() or "tls" in error_msg.lower():
                return False, "SSL/TLS error. Please verify your security settings."
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                return False, "SMTP server quota exceeded. Please try again later."
            else:
                return False, f"Email delivery failed: {error_msg}"
    
    async def send_email_enhanced(
        self,
        user_id: int,
        template_id: str,
        recipient_email: str,
        variables: Optional[Dict[str, Any]] = None,
        smtp_config: Optional[SMTPConfig] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        message_id: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """Enhanced email sending with template support and comprehensive logging"""
        
        try:
            # Get template from database
            template = None
            with db_manager.get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT template_id, subject, html_content, text_content, default_variables
                    FROM email_templates 
                    WHERE template_id = ? AND (user_id = ? OR is_public = 1 OR is_system_template = 1)
                """, (template_id, user_id))
                
                row = cursor.fetchone()
                if row:
                    template = {
                        'template_id': row[0],
                        'subject': row[1],
                        'html_content': row[2],
                        'text_content': row[3],
                        'default_variables': row[4]
                    }
            
            if not template:
                return False, f"Template '{template_id}' not found", ""
            
            # Get SMTP configuration
            if not smtp_config:
                smtp_config = self.get_user_smtp_config(user_id)
                if not smtp_config:
                    return False, "No SMTP configuration found", ""
            
            # Merge variables
            final_variables = {}
            if template.get('default_variables'):
                try:
                    default_vars = json.loads(template['default_variables'])
                    if isinstance(default_vars, dict):
                        final_variables.update(default_vars)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            if variables:
                final_variables.update(variables)
            
            # Generate message ID
            if not message_id:
                message_id = make_msgid()
            
            # Add message ID to custom headers
            if not custom_headers:
                custom_headers = {}
            custom_headers["Message-ID"] = message_id
            
            # Send email
            success, error_msg = await self.send_email(
                smtp_config=smtp_config,
                recipient=recipient_email,
                subject=template['subject'],
                html_content=template['html_content'],
                text_content=template['text_content'],
                variables=final_variables,
                custom_headers=custom_headers
            )
            
            # Log email attempt
            self.log_email(
                user_id=user_id,
                template_id=template_id,
                recipient=recipient_email,
                subject=template['subject'],
                status="sent" if success else "failed",
                error_message=None if success else error_msg
            )
            
            # Update user statistics
            if success:
                await self._update_user_stats(user_id)
            
            return success, error_msg, message_id
            
        except Exception as e:
            error_msg = f"Enhanced email sending failed: {str(e)}"
            logger.error(error_msg)
            
            # Log failed attempt
            self.log_email(
                user_id=user_id,
                template_id=template_id,
                recipient=recipient_email,
                subject="Unknown",
                status="failed",
                error_message=error_msg
            )
            
            return False, error_msg, ""
    
    async def _update_user_stats(self, user_id: int) -> None:
        """Update user email statistics"""
        try:
            with db_manager.get_db_connection() as conn:
                conn.execute("""
                    UPDATE users 
                    SET 
                        total_emails_sent = COALESCE(total_emails_sent, 0) + 1,
                        emails_sent_today = COALESCE(emails_sent_today, 0) + 1,
                        last_api_call = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update user stats: {e}")
    
    def log_email(
        self,
        user_id: int,
        template_id: str,
        recipient: str,
        subject: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Log email sending attempt with comprehensive details"""
        try:
            with db_manager.get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO email_logs 
                    (user_id, template_id, recipient_email, subject, status, error_message, sent_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, template_id, recipient, subject, status, error_message))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log email: {e}")
    
    def get_email_logs(self, user_id: int, limit: int = 100, offset: int = 0) -> List[EmailLog]:
        """Retrieve email logs for user"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, user_id, template_id, recipient_email, subject, 
                           status, error_message, sent_at
                    FROM email_logs 
                    WHERE user_id = ? 
                    ORDER BY sent_at DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                logs = []
                for row in cursor.fetchall():
                    logs.append(EmailLog(
                        id=row[0],
                        user_id=row[1],
                        template_id=row[2],
                        recipient_email=row[3],
                        subject=row[4],
                        status=row[5],
                        error_message=row[6],
                        sent_at=row[7]
                    ))
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to get email logs: {e}")
            return []
    
    def get_daily_email_count(self, user_id: int, target_date: Optional[str] = None) -> int:
        """Get daily email count for user"""
        try:
            if not target_date:
                target_date = datetime.utcnow().strftime('%Y-%m-%d')
            
            with db_manager.get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM email_logs 
                    WHERE user_id = ? AND DATE(sent_at) = ? AND status = 'sent'
                """, (user_id, target_date))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Failed to get daily email count: {e}")
            return 0
    
    def add_to_bounce_list(self, email: str, bounce_type: str = "hard", reason: str = "Unknown") -> None:
        """Add email to bounce list"""
        try:
            email = email.lower().strip()
            self._bounce_tracking.add(email)
            
            with db_manager.get_db_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO email_bounces 
                    (email, bounce_type, bounce_reason, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (email, bounce_type, reason))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to add email to bounce list: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old email logs and connection pool"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with db_manager.get_db_connection() as conn:
                # Clean old email logs
                cursor = conn.execute("""
                    DELETE FROM email_logs 
                    WHERE sent_at < ?
                """, (cutoff_date,))
                deleted_logs = cursor.rowcount
                
                # Clean old bounce records (keep them longer)
                bounce_cutoff = datetime.utcnow() - timedelta(days=days_to_keep * 2)
                cursor = conn.execute("""
                    DELETE FROM email_bounces 
                    WHERE created_at < ? AND bounce_type != 'hard'
                """, (bounce_cutoff,))
                deleted_bounces = cursor.rowcount
                
                conn.commit()
            
            # Reload bounce list
            self._load_bounce_list()
            
            # Clean connection pool
            self.connection_manager._cleanup_stale_connections()
            
            logger.info(f"Cleaned up {deleted_logs} email logs and {deleted_bounces} bounce records")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

# Global email service instance
email = EmailService()
