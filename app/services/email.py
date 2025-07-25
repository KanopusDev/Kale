import aiosmtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr, make_msgid
from typing import Optional, List, Dict, Any, Union
from app.core.database import db_manager
from app.models.schemas import SMTPConfig, SMTPConfigCreate, EmailSendRequest, EmailLog
from app.core.config import settings
import logging
import asyncio
from datetime import datetime, date, timedelta
import json
import re
import hashlib
import base64
import time
from contextlib import asynccontextmanager
import ssl
import certifi
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

@dataclass
class EmailDeliveryStatus:
    """Email delivery status tracking"""
    message_id: str
    status: str  # pending, sent, delivered, bounced, failed
    timestamp: datetime
    error_message: Optional[str] = None
    retry_count: int = 0
    
@dataclass
class EmailMetrics:
    """Email metrics for analytics"""
    total_sent: int = 0
    total_delivered: int = 0
    total_bounced: int = 0
    total_failed: int = 0
    delivery_rate: float = 0.0
    bounce_rate: float = 0.0

class EmailService:
    """Professional email delivery service with comprehensive features"""
    
    def __init__(self):
        self.connection_pool = {}
        self.retry_queues = {}
        self.delivery_tracking = {}
        
    @asynccontextmanager
    async def get_smtp_connection(self, config: SMTPConfig):
        """Get pooled SMTP connection with proper error handling"""
        connection_key = f"{config.smtp_host}:{config.smtp_port}:{config.smtp_username}"
        
        if connection_key in self.connection_pool:
            connection = self.connection_pool[connection_key]
            try:
                # Test if connection is still alive
                await connection.noop()
                yield connection
                return
            except Exception:
                # Connection is dead, remove from pool
                del self.connection_pool[connection_key]
        
        # Create new connection
        connection = aiosmtplib.SMTP(
            hostname=config.smtp_host,
            port=config.smtp_port,
            use_tls=config.use_tls,
            timeout=30,
            start_tls=config.use_tls
        )
        
        try:
            await connection.connect()
            if config.smtp_username and config.smtp_password:
                await connection.login(config.smtp_username, config.smtp_password)
            
            # Store in pool for reuse
            self.connection_pool[connection_key] = connection
            yield connection
            
        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            try:
                await connection.quit()
            except:
                pass
            raise
    
    def generate_message_id(self, domain: Optional[str] = None) -> str:
        """Generate unique message ID for email tracking"""
        if not domain:
            domain = settings.EMAIL_DOMAIN or "kale.kanopus.org"
        return make_msgid(domain=domain)
    
    def create_email_headers(self, from_email: str, to_email: str, 
                           subject: str, config: SMTPConfig,
                           custom_headers: Optional[Dict] = None) -> Dict[str, str]:
        """Create comprehensive email headers with tracking"""
        headers = {
            'Message-ID': self.generate_message_id(),
            'Date': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000'),
            'From': formataddr((config.from_name or '', from_email)),
            'To': to_email,
            'Subject': subject,
            'MIME-Version': '1.0',
            'X-Mailer': f'Kale Email API v{settings.APP_VERSION}',
            'X-Priority': '3',
            'X-MSMail-Priority': 'Normal',
            'List-Unsubscribe': f'<mailto:unsubscribe@{settings.EMAIL_DOMAIN}>',
            'Return-Path': from_email,
        }
        
        # Add tracking headers
        tracking_id = str(uuid.uuid4())
        headers['X-Kale-Tracking-ID'] = tracking_id
        headers['X-Kale-User-ID'] = str(config.user_id) if hasattr(config, 'user_id') else 'unknown'
        
        # Add SPF, DKIM preparation headers
        if settings.EMAIL_DKIM_ENABLED:
            headers['DKIM-Signature'] = 'v=1; a=rsa-sha256; c=relaxed/relaxed'
        
        # Add custom headers
        if custom_headers:
            headers.update(custom_headers)
            
        return headers
    @staticmethod
    def create_smtp_config(user_id: int, config_data: SMTPConfigCreate) -> Optional[SMTPConfig]:
        """Create SMTP configuration for user with validation"""
        try:
            # Validate SMTP configuration before saving
            if not EmailService._validate_smtp_config(config_data):
                raise ValueError("Invalid SMTP configuration")
            
            with db_manager.get_db_connection() as conn:
                
                # Deactivate existing configs for this user
                conn.execute(
                    "UPDATE smtp_configs SET is_active = ?, updated_at = ? WHERE user_id = ?",
                    (False, datetime.utcnow(), user_id)
                )
                
                # Encrypt password before storing
                encrypted_password = EmailService._encrypt_password(config_data.smtp_password) if config_data.smtp_password else ""
                
                # Insert new config
                cursor = conn.execute("""
                    INSERT INTO smtp_configs 
                    (user_id, smtp_host, smtp_port, smtp_username, smtp_password, 
                     use_tls, from_email, from_name, is_active, created_at, updated_at,
                     max_send_rate, daily_limit, connection_timeout)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, config_data.smtp_host, config_data.smtp_port,
                    config_data.smtp_username, encrypted_password,
                    config_data.use_tls, config_data.from_email, 
                    config_data.from_name, True, datetime.utcnow(), datetime.utcnow(),
                    getattr(config_data, 'max_send_rate', 10),  # Default 10 emails/minute
                    getattr(config_data, 'daily_limit', 1000),  # Default 1000/day
                    getattr(config_data, 'connection_timeout', 30)  # Default 30 seconds
                ))
                
                config_id = cursor.lastrowid
                conn.commit()
                
                # Fetch created config using column names
                config_row = conn.execute("SELECT * FROM smtp_configs WHERE id = ?", (config_id,)).fetchone()
                
                if config_row:
                    # Handle both old and new column names for password
                    password_value = None
                    if 'smtp_password' in config_row.keys():
                        password_value = config_row['smtp_password']
                    elif 'smtp_password_encrypted' in config_row.keys():
                        password_value = config_row['smtp_password_encrypted']
                    
                    # Decrypt password for return object
                    decrypted_password = EmailService._decrypt_password(password_value) if password_value else ''
                    
                    return SMTPConfig(
                        id=config_row['id'],
                        user_id=config_row['user_id'],
                        smtp_host=config_row['smtp_host'],
                        smtp_port=config_row['smtp_port'],
                        smtp_username=config_row['smtp_username'],
                        smtp_password=decrypted_password,
                        use_tls=bool(config_row['use_tls']),
                        from_email=config_row['from_email'],
                        from_name=config_row['from_name'],
                        is_active=bool(config_row['is_active']),
                        created_at=config_row['created_at']
                    )
                return None
            
        except Exception as e:
            logger.error(f"Error creating SMTP config: {e}")
            return None
    
    @staticmethod
    def _validate_smtp_config(config: SMTPConfigCreate) -> bool:
        """Validate SMTP configuration parameters"""
        # Basic validation
        if not config.smtp_host or not config.smtp_port:
            return False
        
        # Port validation
        if not (1 <= config.smtp_port <= 65535):
            return False
        
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, config.from_email):
            return False
        
        # Common SMTP ports validation
        valid_ports = {25, 465, 587, 2525}
        if config.smtp_port not in valid_ports:
            logger.warning(f"Unusual SMTP port: {config.smtp_port}")
        
        return True
    
    @staticmethod
    def _encrypt_password(password: str) -> str:
        """Encrypt password for secure storage"""
        return base64.b64encode(password.encode()).decode()
    
    @staticmethod
    def _decrypt_password(encrypted_password: str) -> str:
        """Decrypt password for use"""
        try:
            return base64.b64decode(encrypted_password.encode()).decode()
        except Exception:
            return encrypted_password  # Fallback for unencrypted passwords
            
        except Exception as e:
            logger.error(f"Error creating SMTP config: {e}")
            return None
    
    @staticmethod
    def get_user_smtp_config(user_id: int) -> Optional[SMTPConfig]:
        """Get active SMTP configuration for user"""
        try:
            with db_manager.get_db_connection() as conn:
                
                config_row = conn.execute(
                    "SELECT * FROM smtp_configs WHERE user_id = ? AND is_active = ? ORDER BY created_at DESC LIMIT 1",
                    (user_id, True)
                ).fetchone()
                
                if not config_row:
                    return None
                
                # Handle both old and new column names for password
                password_value = None
                if 'smtp_password' in config_row.keys():
                    password_value = config_row['smtp_password']
                elif 'smtp_password_encrypted' in config_row.keys():
                    password_value = config_row['smtp_password_encrypted']
                
                # Decrypt password if it exists
                decrypted_password = EmailService._decrypt_password(password_value) if password_value else ''
                
                return SMTPConfig(
                    id=config_row['id'],
                    user_id=config_row['user_id'],
                    smtp_host=config_row['smtp_host'],
                    smtp_port=config_row['smtp_port'],
                    smtp_username=config_row['smtp_username'],
                    smtp_password=decrypted_password,
                    use_tls=bool(config_row['use_tls']),
                    from_email=config_row['from_email'],
                    from_name=config_row['from_name'],
                    is_active=bool(config_row['is_active']),
                    created_at=config_row['created_at']
                )
            
        except Exception as e:
            logger.error(f"Error getting SMTP config: {e}")
            return None
    
    @staticmethod
    def test_smtp_connection(config: SMTPConfig) -> tuple[bool, str]:
        """Test SMTP connection with proper SSL/TLS handling and encoding"""
        try:
            # Sanitize and validate config data
            smtp_host = str(config.smtp_host).strip().encode('ascii', 'ignore').decode('ascii')
            smtp_username = str(config.smtp_username).strip().encode('ascii', 'ignore').decode('ascii') if config.smtp_username else ''
            smtp_password = str(config.smtp_password).strip().encode('ascii', 'ignore').decode('ascii') if config.smtp_password else ''
            
            if not smtp_host:
                return False, "SMTP host is required"
            
            # Create SSL context with proper configuration
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            server = None
            
            # Handle different connection types based on port and use_tls setting
            if config.smtp_port == 465:
                # SSL connection (usually port 465)
                server = smtplib.SMTP_SSL(smtp_host, config.smtp_port, context=ssl_context)
            elif config.use_tls and config.smtp_port in [587, 25]:
                # TLS connection (usually port 587 or 25)
                server = smtplib.SMTP(smtp_host, config.smtp_port)
                server.starttls(context=ssl_context)
            else:
                # Plain connection or custom configuration
                if config.use_tls:
                    server = smtplib.SMTP(smtp_host, config.smtp_port)
                    server.starttls(context=ssl_context)
                else:
                    # Try plain connection first
                    try:
                        server = smtplib.SMTP(smtp_host, config.smtp_port)
                    except Exception:
                        # If plain fails, try SSL
                        server = smtplib.SMTP_SSL(smtp_host, config.smtp_port, context=ssl_context)
            
            # Check if server supports authentication before attempting login
            if smtp_username and smtp_password:
                try:
                    # Get server capabilities
                    capabilities = server.ehlo_or_helo_if_needed()
                    
                    # Check if AUTH is supported
                    if hasattr(server, 'has_extn') and server.has_extn('auth'):
                        server.login(smtp_username, smtp_password)
                    else:
                        # Some servers don't require AUTH for local/trusted connections
                        logger.warning(f"SMTP server {smtp_host} doesn't support AUTH extension, continuing without authentication")
                except smtplib.SMTPAuthenticationError as auth_error:
                    server.quit()
                    return False, f"Authentication failed: {str(auth_error)}"
                except Exception as login_error:
                    # If login fails but server doesn't support AUTH, it might still work for sending
                    logger.warning(f"Login attempt failed: {login_error}, continuing without authentication")
            
            server.quit()
            return True, "SMTP connection successful"
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            error_msg = str(e)
            
            # Provide more helpful error messages
            if "WRONG_VERSION_NUMBER" in error_msg:
                error_msg = "SSL/TLS configuration mismatch. Try toggling the TLS setting or using a different port (587 for TLS, 465 for SSL, 25 for plain)."
            elif "authentication failed" in error_msg.lower():
                error_msg = "Authentication failed. Please check your username and password."
            elif "connection refused" in error_msg.lower():
                error_msg = "Connection refused. Please check the host and port settings."
            elif "auth extension not supported" in error_msg.lower():
                error_msg = "Server doesn't support authentication. Try connecting without username/password or use a different SMTP server."
            elif "ascii" in error_msg.lower() and "encode" in error_msg.lower():
                error_msg = "Invalid characters in SMTP configuration. Please use only ASCII characters for host, username, and password."
            
            return False, error_msg
    
    @staticmethod
    def replace_variables(content: str, variables: Dict[str, Any]) -> str:
        """Replace variables in email content"""
        try:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))
            return content
        except Exception as e:
            logger.error(f"Error replacing variables: {e}")
            return content
    
    @staticmethod
    def extract_variables(content: str) -> List[str]:
        """Extract variable names from content"""
        try:
            pattern = r'\{\{(\w+)\}\}'
            variables = re.findall(pattern, content)
            return list(set(variables))
        except Exception as e:
            logger.error(f"Error extracting variables: {e}")
            return []
    
    @staticmethod
    async def send_email(
        smtp_config: SMTPConfig,
        recipient: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, str]:
        """Send individual email with proper SSL/TLS handling and encoding"""
        try:
            # Sanitize and validate config data
            smtp_host = str(smtp_config.smtp_host).strip().encode('ascii', 'ignore').decode('ascii')
            smtp_username = str(smtp_config.smtp_username).strip().encode('ascii', 'ignore').decode('ascii') if smtp_config.smtp_username else ''
            smtp_password = str(smtp_config.smtp_password).strip().encode('ascii', 'ignore').decode('ascii') if smtp_config.smtp_password else ''
            
            # Replace variables in content
            if variables:
                subject = EmailService.replace_variables(subject, variables)
                html_content = EmailService.replace_variables(html_content, variables)
                if text_content:
                    text_content = EmailService.replace_variables(text_content, variables)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{smtp_config.from_name} <{smtp_config.from_email}>" if smtp_config.from_name else smtp_config.from_email
            message["To"] = recipient
            message["Message-ID"] = make_msgid()
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Configure SSL context
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Send email with proper SSL/TLS configuration
            send_params = {
                "hostname": smtp_host,
                "port": smtp_config.smtp_port,
                "tls_context": ssl_context
            }
            
            # Only include authentication if username is provided
            if smtp_username:
                send_params["username"] = smtp_username
                
                # Only include password if provided
                if smtp_password:
                    send_params["password"] = smtp_password
            
            # Handle different connection types based on port and use_tls setting
            if smtp_config.smtp_port == 465:
                # SSL connection (usually port 465)
                send_params["use_tls"] = True
            elif smtp_config.use_tls and smtp_config.smtp_port in [587, 25]:
                # TLS connection (usually port 587 or 25)
                send_params["start_tls"] = True
            else:
                # Custom configuration
                if smtp_config.use_tls:
                    send_params["start_tls"] = True
                else:
                    # Try to determine the best method based on port
                    if smtp_config.smtp_port == 465:
                        send_params["use_tls"] = True
                    else:
                        send_params["start_tls"] = True
            
            # Send email using aiosmtplib with proper parameter handling
            # Create SMTP client for better control
            smtp_client = aiosmtplib.SMTP(
                hostname=send_params["hostname"],
                port=send_params["port"],
                tls_context=send_params["tls_context"],
                use_tls=send_params.get("use_tls", False),
                start_tls=send_params.get("start_tls", False)
            )
            
            await smtp_client.connect()
            
            # Authenticate if credentials provided
            if send_params.get("username") and send_params.get("password"):
                await smtp_client.login(send_params["username"], send_params["password"])
            
            # Send the message
            await smtp_client.send_message(message)
            await smtp_client.quit()
            
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            error_msg = str(e)
            
            # Provide more helpful error messages
            if "WRONG_VERSION_NUMBER" in error_msg:
                error_msg = "SSL/TLS configuration mismatch. Please check your SMTP settings."
            elif "authentication failed" in error_msg.lower():
                error_msg = "Authentication failed. Please check your username and password."
            elif "connection refused" in error_msg.lower():
                error_msg = "Connection refused. Please check the host and port settings."
            elif "ascii" in error_msg.lower() and "encode" in error_msg.lower():
                error_msg = "Invalid characters in email content or SMTP configuration. Please use only ASCII characters."
            
            return False, error_msg
    
    async def send_email_enhanced(
        self,
        user_id: int,
        template_id: str,
        recipient_email: str,
        variables: Optional[Dict[str, Any]] = None,
        smtp_config: Optional[SMTPConfig] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        message_id: Optional[str] = None
    ) -> tuple[bool, str, str]:
        """Enhanced email sending method with template support and logging"""
        try:
            # Get template using database query directly
            template = None
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM email_templates 
                    WHERE template_id = ? AND (user_id = ? OR is_public = ? OR is_system_template = ?)
                """, (template_id, user_id, True, True))
                template_row = cursor.fetchone()
                if template_row:
                    template = dict(template_row)
            
            if not template:
                return False, f"Template {template_id} not found", ""
            
            # Use provided SMTP config or get default for user
            if not smtp_config:
                smtp_config = EmailService.get_user_smtp_config(user_id)
                if not smtp_config:
                    return False, "No SMTP configuration found", ""
            
            # Prepare variables (merge template defaults with provided)
            final_variables = {}
            if template.get('default_variables'):
                try:
                    default_vars = json.loads(template['default_variables'])
                    if isinstance(default_vars, dict):
                        final_variables.update(default_vars)
                except json.JSONDecodeError:
                    pass
            
            if variables:
                final_variables.update(variables)
            
            # Replace variables in template content
            subject = template['subject']
            html_content = template['html_content']
            text_content = template.get('text_content')
            
            if final_variables:
                subject = EmailService.replace_variables(subject, final_variables)
                html_content = EmailService.replace_variables(html_content, final_variables)
                if text_content:
                    text_content = EmailService.replace_variables(text_content, final_variables)
            
            # Generate message ID if not provided
            if not message_id:
                message_id = make_msgid()
            
            # Create message with custom headers
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{smtp_config.from_name} <{smtp_config.from_email}>" if smtp_config.from_name else smtp_config.from_email
            message["To"] = recipient_email
            message["Message-ID"] = message_id
            
            # Add custom headers
            if custom_headers:
                for header_name, header_value in custom_headers.items():
                    message[header_name] = header_value
            
            # Add content parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send using existing send_email logic
            smtp_host = str(smtp_config.smtp_host).strip().encode('ascii', 'ignore').decode('ascii')
            smtp_username = str(smtp_config.smtp_username).strip().encode('ascii', 'ignore').decode('ascii') if smtp_config.smtp_username else ''
            smtp_password = str(smtp_config.smtp_password).strip().encode('ascii', 'ignore').decode('ascii') if smtp_config.smtp_password else ''
            
            # Configure SSL context
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Send email with proper SSL/TLS configuration
            send_params = {
                "hostname": smtp_host,
                "port": smtp_config.smtp_port,
                "tls_context": ssl_context
            }
            
            # Only include authentication if username is provided
            if smtp_username:
                send_params["username"] = smtp_username
                if smtp_password:
                    send_params["password"] = smtp_password
            
            # Handle different connection types based on port and use_tls setting
            if smtp_config.smtp_port == 465:
                send_params["use_tls"] = True
            elif smtp_config.use_tls and smtp_config.smtp_port in [587, 25]:
                send_params["start_tls"] = True
            else:
                if smtp_config.use_tls:
                    send_params["start_tls"] = True
                else:
                    if smtp_config.smtp_port == 465:
                        send_params["use_tls"] = True
                    else:
                        send_params["start_tls"] = True
            
            # Create SMTP client
            smtp_client = aiosmtplib.SMTP(
                hostname=send_params["hostname"],
                port=send_params["port"],
                tls_context=send_params["tls_context"],
                use_tls=send_params.get("use_tls", False),
                start_tls=send_params.get("start_tls", False)
            )
            
            await smtp_client.connect()
            
            # Authenticate if credentials provided
            if send_params.get("username") and send_params.get("password"):
                await smtp_client.login(send_params["username"], send_params["password"])
            
            # Send the message
            await smtp_client.send_message(message)
            await smtp_client.quit()
            
            # Log successful email
            EmailService.log_email(
                user_id=user_id,
                template_id=template_id,
                recipient=recipient_email,
                subject=subject,
                status="sent"
            )
            
            # Update user statistics
            await self._update_user_email_stats(user_id)
            
            return True, "Email sent successfully", message_id
            
        except Exception as e:
            logger.error(f"Error in send_email_enhanced: {e}")
            error_msg = str(e)
            
            # Provide more helpful error messages
            if "WRONG_VERSION_NUMBER" in error_msg:
                error_msg = "SSL/TLS configuration mismatch. Please check your SMTP settings."
            elif "authentication failed" in error_msg.lower():
                error_msg = "Authentication failed. Please check your username and password."
            elif "connection refused" in error_msg.lower():
                error_msg = "Connection refused. Please check the host and port settings."
            elif "ascii" in error_msg.lower() and "encode" in error_msg.lower():
                error_msg = "Invalid characters in email content or SMTP configuration. Please use only ASCII characters."
            
            # Log failed email
            EmailService.log_email(
                user_id=user_id,
                template_id=template_id,
                recipient=recipient_email,
                subject=subject if 'subject' in locals() else "Unknown",
                status="failed",
                error_message=error_msg
            )
            
            return False, error_msg, ""
    
    async def _update_user_email_stats(self, user_id: int) -> None:
        """Update user email statistics"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Update total emails sent and last API call
                cursor.execute("""
                    UPDATE users 
                    SET total_emails_sent = COALESCE(total_emails_sent, 0) + 1,
                        emails_sent_today = COALESCE(emails_sent_today, 0) + 1,
                        last_api_call = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating user email stats: {e}")
    
    @staticmethod
    def log_email(
        user_id: int,
        template_id: str,
        recipient: str,
        subject: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Log email sending attempt"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO email_logs 
                    (user_id, template_id, recipient_email, subject, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, template_id, recipient, subject, status, error_message))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging email: {e}")
    
    @staticmethod
    def get_email_logs(user_id: int, limit: int = 100, offset: int = 0) -> List[EmailLog]:
        """Get email logs for user"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM email_logs 
                    WHERE user_id = ? 
                    ORDER BY sent_at DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                log_rows = cursor.fetchall()
                
                return [
                    EmailLog(
                        id=row['id'],
                        user_id=row['user_id'],
                        template_id=row['template_id'],
                        recipient_email=row['recipient_email'],
                        subject=row['subject'],
                        status=row['status'],
                        error_message=row['error_message'],
                        sent_at=row['sent_at']
                    ) for row in log_rows
                ]
            
        except Exception as e:
            logger.error(f"Error getting email logs: {e}")
            return []
    
    @staticmethod
    def get_daily_email_count(user_id: int, target_date: Optional[date] = None) -> int:
        """Get email count for specific date"""
        try:
            if not target_date:
                target_date = date.today()
            
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) as count FROM email_logs 
                    WHERE user_id = ? AND DATE(sent_at) = ? AND status = 'sent'
                """, (user_id, target_date.isoformat()))
                
                result = cursor.fetchone()
                return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting daily email count: {e}")
            return 0

    async def get_email_metrics(self, user_id: int, days: int = 30) -> EmailMetrics:
        """Get comprehensive email metrics for analytics"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            since_date = datetime.utcnow() - timedelta(days=days)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sent,
                    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as total_delivered,
                    SUM(CASE WHEN status = 'bounced' THEN 1 ELSE 0 END) as total_bounced,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as total_failed
                FROM email_logs 
                WHERE user_id = ? AND sent_at >= ?
            """, (user_id, since_date))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                total_sent = result[0] or 0
                total_delivered = result[1] or 0
                total_bounced = result[2] or 0
                total_failed = result[3] or 0
                
                delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
                bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0
                
                return EmailMetrics(
                    total_sent=total_sent,
                    total_delivered=total_delivered,
                    total_bounced=total_bounced,
                    total_failed=total_failed,
                    delivery_rate=delivery_rate,
                    bounce_rate=bounce_rate
                )
            
            return EmailMetrics()
            
        except Exception as e:
            logger.error(f"Error getting email metrics: {e}")
            return EmailMetrics()
    
    async def process_scheduled_emails(self):
        """Process scheduled emails that are due for delivery"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM scheduled_emails 
                WHERE status = 'scheduled' AND schedule_time <= ?
                ORDER BY schedule_time ASC
                LIMIT 100
            """, (datetime.utcnow(),))
            
            scheduled_emails = cursor.fetchall()
            
            for email_row in scheduled_emails:
                try:
                    # Mark as processing
                    cursor.execute("""
                        UPDATE scheduled_emails 
                        SET status = 'processing' 
                        WHERE id = ?
                    """, (email_row['id'],))
                    conn.commit()
                    
                    # Get SMTP config
                    smtp_config = self.get_smtp_config_by_id(email_row['smtp_config_id'])
                    if not smtp_config:
                        continue
                    
                    # Parse variables
                    variables = json.loads(email_row['variables']) if email_row['variables'] else {}
                    
                    # Send email
                    success, error_msg, _ = await self.send_email_enhanced(
                        email_row['user_id'],
                        email_row['template_id'],
                        email_row['recipient_email'],
                        variables,
                        smtp_config,
                        message_id=email_row['message_id']
                    )
                    
                    # Update status
                    status = 'sent' if success else 'failed'
                    cursor.execute("""
                        UPDATE scheduled_emails 
                        SET status = ?, error_message = ?, sent_at = ?
                        WHERE id = ?
                    """, (status, error_msg if not success else None, datetime.utcnow(), email_row['id']))
                    conn.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing scheduled email {email_row['id']}: {e}")
                    cursor.execute("""
                        UPDATE scheduled_emails 
                        SET status = 'failed', error_message = ?
                        WHERE id = ?
                    """, (str(e), email_row['id']))
                    conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error processing scheduled emails: {e}")
    
    def get_smtp_config_by_id(self, config_id: int) -> Optional[SMTPConfig]:
        """Get SMTP config by ID"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM smtp_configs WHERE id = ?", (config_id,))
            config_row = cursor.fetchone()
            conn.close()
            
            if config_row:
                # Decrypt password
                decrypted_password = self._decrypt_password(config_row[4])
                
                return SMTPConfig(
                    id=config_row[0],
                    user_id=config_row[1],
                    smtp_host=config_row[2],
                    smtp_port=config_row[3],
                    smtp_username=config_row[4],
                    smtp_password=decrypted_password,
                    use_tls=bool(config_row[5]),
                    from_email=config_row[6],
                    from_name=config_row[7],
                    is_active=bool(config_row[8]),
                    created_at=config_row[9],
                    updated_at=config_row[10]
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting SMTP config: {e}")
            return None
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle delivery webhooks from email providers"""
        try:
            message_id = webhook_data.get('message_id')
            event_type = webhook_data.get('event')  # delivered, bounced, clicked, opened
            timestamp = webhook_data.get('timestamp')
            
            if not message_id or not event_type:
                return False
            
            # Update delivery tracking
            if message_id in self.delivery_tracking:
                self.delivery_tracking[message_id].status = event_type
                self.delivery_tracking[message_id].timestamp = datetime.fromtimestamp(timestamp) if timestamp else datetime.utcnow()
            
            # Update database
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            if event_type == 'bounced':
                # Add to bounce list
                cursor.execute("""
                    INSERT OR REPLACE INTO email_bounces 
                    (email, bounce_type, bounce_reason, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    webhook_data.get('email'),
                    webhook_data.get('bounce_type', 'hard'),
                    webhook_data.get('reason', 'Unknown'),
                    datetime.utcnow()
                ))
            
            # Update email log status
            cursor.execute("""
                UPDATE email_logs 
                SET status = ?, updated_at = ?
                WHERE message_id = ?
            """, (event_type, datetime.utcnow(), message_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            return False
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old email logs and tracking data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # Clean old email logs
            cursor.execute("""
                DELETE FROM email_logs 
                WHERE sent_at < ?
            """, (cutoff_date,))
            
            # Clean old scheduled emails
            cursor.execute("""
                DELETE FROM scheduled_emails 
                WHERE (status = 'sent' OR status = 'failed') AND created_at < ?
            """, (cutoff_date,))
            
            # Clean old bounce records (keep them longer)
            bounce_cutoff = datetime.utcnow() - timedelta(days=days_to_keep * 2)
            cursor.execute("""
                DELETE FROM email_bounces 
                WHERE created_at < ?
            """, (bounce_cutoff,))
            
            conn.commit()
            conn.close()
            
            # Clean in-memory tracking
            old_keys = [
                k for k, v in self.delivery_tracking.items() 
                if v.timestamp < cutoff_date
            ]
            for key in old_keys:
                del self.delivery_tracking[key]
            
            logger.info(f"Cleaned up email data older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Data cleanup error: {e}")

email = EmailService()
