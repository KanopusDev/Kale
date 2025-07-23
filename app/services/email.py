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
    """Enterprise-grade email delivery service with comprehensive features"""
    
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
                cursor = conn.cursor()
                
                # Deactivate existing configs for this user
                cursor.execute(
                    "UPDATE smtp_configs SET is_active = ?, updated_at = ? WHERE user_id = ?",
                    (False, datetime.utcnow(), user_id)
                )
                
                # Encrypt password before storing
                encrypted_password = EmailService._encrypt_password(config_data.smtp_password)
                
                # Insert new config
                cursor.execute("""
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
                
                # Fetch created config
                cursor.execute("SELECT * FROM smtp_configs WHERE id = ?", (config_id,))
                config_row = cursor.fetchone()
                
                if config_row:
                    # Decrypt password for return object
                    decrypted_password = EmailService._decrypt_password(config_row[4])
                    
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
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT * FROM smtp_configs WHERE user_id = ? AND is_active = ? ORDER BY created_at DESC LIMIT 1",
                    (user_id, True)
                )
                config_row = cursor.fetchone()
                
                if not config_row:
                    return None
                
                return SMTPConfig(
                    id=config_row['id'],
                    user_id=config_row['user_id'],
                    smtp_host=config_row['smtp_host'],
                    smtp_port=config_row['smtp_port'],
                    smtp_username=config_row['smtp_username'],
                    smtp_password=config_row['smtp_password'],
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
        """Test SMTP connection"""
        try:
            if config.use_tls:
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
            
            server.login(config.smtp_username, config.smtp_password)
            server.quit()
            return True, "SMTP connection successful"
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False, str(e)
    
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
        """Send individual email"""
        try:
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
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            if smtp_config.use_tls:
                await aiosmtplib.send(
                    message,
                    hostname=smtp_config.smtp_host,
                    port=smtp_config.smtp_port,
                    start_tls=True,
                    username=smtp_config.smtp_username,
                    password=smtp_config.smtp_password,
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=smtp_config.smtp_host,
                    port=smtp_config.smtp_port,
                    use_tls=True,
                    username=smtp_config.smtp_username,
                    password=smtp_config.smtp_password,
                )
            
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False, str(e)
    
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
