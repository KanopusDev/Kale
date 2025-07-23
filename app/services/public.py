"""
Public API Service
Handles public email API endpoints for /{username}/{template_id}
Enterprise-grade implementation with comprehensive security and monitoring
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import uuid
from contextlib import asynccontextmanager

from app.core.database import db_manager
from app.core.config import settings
from app.models.schemas import EmailSendRequest, EmailLog, User, EmailTemplate, SMTPConfig
from app.services.email import EmailService
from app.services.limitter import RateLimitService
from app.services.user import UserService
from app.services.template import TemplateService

logger = logging.getLogger(__name__)

class PublicAPIService:
    """Enterprise public API service for email sending"""
    
    def __init__(self):
        self.email = EmailService()
        self.rate_limit = RateLimitService()
        self.user = UserService()
        self.template = TemplateService()
        
    async def send_email_via_public_api(
        self,
        username: str,
        template_id: str,
        request_data: Dict[str, Any],
        api_key: str,
        client_ip: str,
        user_agent: str = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Send email via public API endpoint
        Endpoint: /{username}/{template_id}
        """
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Public API request started: {request_id}", extra={
                "request_id": request_id,
                "username": username,
                "template_id": template_id,
                "client_ip": client_ip,
                "user_agent": user_agent
            })
            
            # Step 1: Validate API key and get user
            user = await self._validate_api_key(api_key, username)
            if not user:
                await self._log_api_usage(
                    username, template_id, client_ip, user_agent,
                    request_data, 401, "Invalid API key", request_id
                )
                return False, "Invalid API key", {"request_id": request_id}
            
            # Step 2: Validate user status
            if not user.is_active:
                await self._log_api_usage(
                    username, template_id, client_ip, user_agent,
                    request_data, 403, "Account suspended", request_id
                )
                return False, "Account suspended", {"request_id": request_id}
            
            # Step 3: Check rate limits
            rate_limit_ok, rate_limit_msg = await self._check_rate_limits(user, client_ip)
            if not rate_limit_ok:
                await self._log_api_usage(
                    username, template_id, client_ip, user_agent,
                    request_data, 429, rate_limit_msg, request_id
                )
                return False, rate_limit_msg, {"request_id": request_id}
            
            # Step 4: Validate request data
            valid_request, validation_error = await self._validate_request_data(request_data)
            if not valid_request:
                await self._log_api_usage(
                    username, template_id, client_ip, user_agent,
                    request_data, 400, validation_error, request_id
                )
                return False, validation_error, {"request_id": request_id}
            
            # Step 5: Get and validate template
            template = await self._get_user_template(user.id, template_id)
            if not template:
                await self._log_api_usage(
                    username, template_id, client_ip, user_agent,
                    request_data, 404, "Template not found", request_id
                )
                return False, "Template not found", {"request_id": request_id}
            
            # Step 6: Get user's SMTP configuration
            smtp_config = await self._get_user_smtp_config(user.id)
            if not smtp_config:
                await self._log_api_usage(
                    username, template_id, client_ip, user_agent,
                    request_data, 400, "SMTP not configured", request_id
                )
                return False, "SMTP configuration required", {"request_id": request_id}
            
            # Step 7: Validate recipients
            recipients = request_data.get('recipients', [])
            if isinstance(recipients, str):
                recipients = [recipients]
            
            if not recipients:
                recipients = [request_data.get('to_email', request_data.get('email'))]
            
            if not recipients or not any(recipients):
                await self._log_api_usage(
                    username, template_id, client_ip, user_agent,
                    request_data, 400, "No recipients specified", request_id
                )
                return False, "No recipients specified", {"request_id": request_id}
            
            # Step 8: Process and send emails
            variables = request_data.get('variables', {})
            sent_count = 0
            failed_count = 0
            results = []
            
            for recipient in recipients:
                if not recipient:
                    continue
                    
                try:
                    # Send individual email
                    success, message, message_id = await self.email.send_email_enhanced(
                        user_id=user.id,
                        template_id=template_id,
                        recipient_email=recipient,
                        variables=variables,
                        smtp_config=smtp_config,
                        custom_headers={
                            'X-API-Request-ID': request_id,
                            'X-API-Client-IP': client_ip
                        }
                    )
                    
                    if success:
                        sent_count += 1
                        results.append({
                            "recipient": recipient,
                            "status": "sent",
                            "message_id": message_id
                        })
                    else:
                        failed_count += 1
                        results.append({
                            "recipient": recipient,
                            "status": "failed",
                            "error": message
                        })
                        
                except Exception as e:
                    failed_count += 1
                    results.append({
                        "recipient": recipient,
                        "status": "failed",
                        "error": str(e)
                    })
                    logger.error(f"Email send error for {recipient}: {e}")
            
            # Step 9: Log API usage
            status_code = 200 if sent_count > 0 else 500
            response_message = f"Sent: {sent_count}, Failed: {failed_count}"
            
            await self._log_api_usage(
                username, template_id, client_ip, user_agent,
                request_data, status_code, response_message, request_id
            )
            
            # Step 10: Update user statistics
            await self._update_user_stats(user.id, sent_count, failed_count)
            
            # Step 11: Return results
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            response_data = {
                "request_id": request_id,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_recipients": len(recipients),
                "processing_time_seconds": processing_time,
                "results": results
            }
            
            logger.info(f"Public API request completed: {request_id}", extra={
                "request_id": request_id,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "processing_time": processing_time
            })
            
            return True, response_message, response_data
            
        except Exception as e:
            logger.error(f"Public API error: {e}", extra={
                "request_id": request_id,
                "username": username,
                "template_id": template_id,
                "error": str(e)
            })
            
            await self._log_api_usage(
                username, template_id, client_ip, user_agent,
                request_data, 500, f"Internal server error: {str(e)}", request_id
            )
            
            return False, "Internal server error", {"request_id": request_id}
    
    async def _validate_api_key(self, api_key: str, username: str) -> Optional[User]:
        """Validate API key and return user"""
        try:
            # Hash the API key for secure comparison
            hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
            
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.*, ak.key_hash, ak.is_active as key_active, ak.expires_at
                FROM users u
                JOIN api_keys ak ON u.id = ak.user_id
                WHERE u.username = ? AND ak.key_hash = ? AND ak.is_active = 1
            """, (username, hashed_key))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Check if key is expired
            if row['expires_at'] and datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
                return None
            
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                is_verified=bool(row['is_verified']),
                is_admin=bool(row['is_admin']),
                is_active=bool(row['is_active']),
                api_key=api_key,  # Return the original key
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    async def _check_rate_limits(self, user: User, client_ip: str) -> Tuple[bool, str]:
        """Check various rate limits for the user"""
        try:
            # Get user's daily limit
            daily_limit = -1 if user.is_verified else settings.UNVERIFIED_DAILY_LIMIT
            
            # Check daily email limit
            if daily_limit > 0:
                daily_count = await self._get_daily_email_count(user.id)
                if daily_count >= daily_limit:
                    return False, f"Daily email limit ({daily_limit}) exceeded"
            
            # Check API rate limits
            api_key = f"api_rate:{user.id}"
            if not await self.rate_limit.check_rate_limit(
                api_key, settings.API_RATE_LIMIT_PER_MINUTE, 60
            ):
                return False, "API rate limit exceeded (per minute)"
            
            if not await self.rate_limit.check_rate_limit(
                api_key, settings.API_RATE_LIMIT_PER_HOUR, 3600
            ):
                return False, "API rate limit exceeded (per hour)"
            
            # Check IP-based rate limits
            ip_key = f"ip_rate:{client_ip}"
            if not await self.rate_limit.check_rate_limit(
                ip_key, 100, 60  # 100 requests per minute per IP
            ):
                return False, "IP rate limit exceeded"
            
            # Check burst limits
            burst_key = f"burst:{user.id}"
            if not await self.rate_limit.check_rate_limit(
                burst_key, settings.EMAIL_BURST_LIMIT, 
                settings.EMAIL_BURST_WINDOW_MINUTES * 60
            ):
                return False, "Burst limit exceeded"
            
            return True, "Rate limits OK"
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True, "Rate limit check failed, allowing"
    
    async def _validate_request_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate incoming request data"""
        try:
            # Check required fields
            recipients = data.get('recipients', [])
            if isinstance(recipients, str):
                recipients = [recipients]
            
            # Alternative recipient fields
            if not recipients:
                email_fields = ['to_email', 'email', 'recipient']
                for field in email_fields:
                    if data.get(field):
                        recipients = [data[field]]
                        break
            
            if not recipients or not any(recipients):
                return False, "Recipients required (recipients, to_email, email, or recipient)"
            
            # Validate recipient count
            if len(recipients) > 100:  # Reasonable limit per request
                return False, "Maximum 100 recipients per request"
            
            # Validate email formats
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            for recipient in recipients:
                if not re.match(email_pattern, recipient):
                    return False, f"Invalid email format: {recipient}"
            
            # Validate variables (if provided)
            variables = data.get('variables', {})
            if variables and not isinstance(variables, dict):
                return False, "Variables must be a JSON object"
            
            # Check for prohibited content in variables
            if variables:
                for key, value in variables.items():
                    if isinstance(value, str) and len(value) > 10000:  # 10KB limit per variable
                        return False, f"Variable '{key}' exceeds maximum length"
            
            return True, "Valid request"
            
        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return False, f"Request validation error: {str(e)}"
    
    async def _get_user_template(self, user_id: int, template_id: str) -> Optional[EmailTemplate]:
        """Get user's template or public template"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # First try user's private templates
            cursor.execute("""
                SELECT * FROM email_templates 
                WHERE user_id = ? AND template_id = ? AND is_active = 1
            """, (user_id, template_id))
            
            row = cursor.fetchone()
            
            # If not found, try public/system templates
            if not row:
                cursor.execute("""
                    SELECT * FROM email_templates 
                    WHERE (is_public = 1 OR is_system_template = 1) 
                    AND template_id = ? AND is_active = 1
                """, (template_id,))
                row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return EmailTemplate(
                    id=row['id'],
                    user_id=row['user_id'],
                    template_id=row['template_id'],
                    name=row['name'],
                    subject=row['subject'],
                    html_content=row['html_content'],
                    text_content=row['text_content'],
                    variables=json.loads(row['variables']) if row['variables'] else [],
                    category=row['category'],
                    description=row['description'],
                    is_public=bool(row['is_public']),
                    is_system_template=bool(row['is_system_template']),
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Template retrieval error: {e}")
            return None
    
    async def _get_user_smtp_config(self, user_id: int) -> Optional[SMTPConfig]:
        """Get user's active SMTP configuration"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM smtp_configs 
                WHERE user_id = ? AND is_active = 1 
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return SMTPConfig(
                    id=row['id'],
                    user_id=row['user_id'],
                    smtp_host=row['smtp_host'],
                    smtp_port=row['smtp_port'],
                    smtp_username=row['smtp_username'],
                    smtp_password=row['smtp_password'],  # Will be decrypted by email service
                    use_tls=bool(row['use_tls']),
                    from_email=row['from_email'],
                    from_name=row['from_name'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"SMTP config retrieval error: {e}")
            return None
    
    async def _get_daily_email_count(self, user_id: int) -> int:
        """Get user's email count for today"""
        try:
            today = datetime.utcnow().date()
            
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM email_logs 
                WHERE user_id = ? AND DATE(sent_at) = ? AND status = 'sent'
            """, (user_id, today.isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Daily email count error: {e}")
            return 0
    
    async def _log_api_usage(
        self,
        username: str,
        template_id: str,
        client_ip: str,
        user_agent: str,
        request_data: Dict[str, Any],
        status_code: int,
        response_message: str,
        request_id: str
    ):
        """Log API usage for monitoring and analytics"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            user_id = user_row['id'] if user_row else None
            
            # Log the API call
            cursor.execute("""
                INSERT INTO api_usage_logs 
                (user_id, username, template_id, endpoint, client_ip, user_agent,
                 request_data, status_code, response_message, request_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, username, template_id, f"/{username}/{template_id}",
                client_ip, user_agent, json.dumps(request_data), status_code,
                response_message, request_id, datetime.utcnow()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"API usage logging error: {e}")
    
    async def _update_user_stats(self, user_id: int, sent_count: int, failed_count: int):
        """Update user statistics"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # Update user stats
            cursor.execute("""
                UPDATE users SET 
                    total_emails_sent = total_emails_sent + ?,
                    emails_sent_today = emails_sent_today + ?,
                    last_api_call = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                sent_count, sent_count, datetime.utcnow(), 
                datetime.utcnow(), user_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"User stats update error: {e}")
    
    async def get_api_usage_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get API usage statistics for a user"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # Get detailed stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_calls,
                    COUNT(CASE WHEN status_code = 200 THEN 1 END) as successful_calls,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as failed_calls,
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    AVG(CASE WHEN status_code = 200 THEN 1.0 ELSE 0.0 END) as success_rate
                FROM api_usage_logs 
                WHERE user_id = ? AND created_at >= ?
            """, (user_id, since_date))
            
            stats_row = cursor.fetchone()
            
            # Get usage by day
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as calls,
                    COUNT(CASE WHEN status_code = 200 THEN 1 END) as successful
                FROM api_usage_logs 
                WHERE user_id = ? AND created_at >= ?
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (user_id, since_date))
            
            daily_usage = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_calls": stats_row['total_calls'] or 0,
                "successful_calls": stats_row['successful_calls'] or 0,
                "failed_calls": stats_row['failed_calls'] or 0,
                "active_days": stats_row['active_days'] or 0,
                "success_rate": float(stats_row['success_rate'] or 0),
                "daily_usage": [
                    {
                        "date": row['date'],
                        "calls": row['calls'],
                        "successful": row['successful']
                    }
                    for row in daily_usage
                ]
            }
            
        except Exception as e:
            logger.error(f"API usage stats error: {e}")
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "active_days": 0,
                "success_rate": 0.0,
                "daily_usage": []
            }

# Global service instance
public_api = PublicAPIService()
