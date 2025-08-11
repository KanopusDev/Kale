from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from datetime import datetime
from app.models.schemas import (
    SMTPConfig, SMTPConfigCreate, User, EmailSendRequest, EmailLog
)
from app.services.email import email
from app.services.template import template
from app.services.limitter import rate_limit
from app.core.deps import get_current_user, verify_api_access
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])

@router.post("/smtp", response_model=SMTPConfig, status_code=status.HTTP_201_CREATED)
async def create_smtp_config(
    config_data: SMTPConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """Create SMTP configuration"""
    try:
        # Test SMTP connection first (only if password is provided)
        if config_data.smtp_password:
            test_config = SMTPConfig(
                id=0,
                user_id=current_user.id,
                **config_data.dict(),
                is_active=True,
                created_at=datetime.now()
            )
            
            is_valid, error_message = email.test_smtp_connection(test_config)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SMTP connection failed: {error_message}"
                )
        
        # Create SMTP config
        smtp_config = email.create_smtp_config(current_user.id, config_data)
        if not smtp_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create SMTP configuration"
            )
        
        logger.info(f"SMTP config created for user {current_user.username}")
        return smtp_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMTP config creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP configuration failed"
        )

@router.get("/smtp")
async def get_smtp_config(current_user: User = Depends(get_current_user)):
    """Get user's SMTP configuration"""
    try:
        smtp_config = email.get_user_smtp_config(current_user.id)
        if not smtp_config:
            # Return empty configuration instead of 404
            return {
                "id": None,
                "user_id": current_user.id,
                "name": "Default",
                "smtp_host": "",
                "smtp_port": 587,
                "smtp_username": "",
                "smtp_password": "",
                "use_tls": True,
                "use_ssl": False,
                "from_email": "",
                "from_name": "",
                "is_active": False,
                "is_verified": False,
                "last_used": None,
                "created_at": None,
                "updated_at": None,
                "configured": False
            }
        
        # Hide sensitive data
        smtp_config_dict = {
            "id": smtp_config.id if hasattr(smtp_config, 'id') else None,
            "user_id": current_user.id,
            "name": smtp_config.name if hasattr(smtp_config, 'name') else "Default",
            "smtp_host": smtp_config.smtp_host if hasattr(smtp_config, 'smtp_host') else "",
            "smtp_port": smtp_config.smtp_port if hasattr(smtp_config, 'smtp_port') else 587,
            "smtp_username": smtp_config.smtp_username if hasattr(smtp_config, 'smtp_username') else "",
            "smtp_password": "***" if hasattr(smtp_config, 'smtp_password') and smtp_config.smtp_password else "",
            "use_tls": smtp_config.use_tls if hasattr(smtp_config, 'use_tls') else True,
            "use_ssl": smtp_config.use_ssl if hasattr(smtp_config, 'use_ssl') else False,
            "from_email": smtp_config.from_email if hasattr(smtp_config, 'from_email') else "",
            "from_name": smtp_config.from_name if hasattr(smtp_config, 'from_name') else "",
            "is_active": smtp_config.is_active if hasattr(smtp_config, 'is_active') else False,
            "is_verified": smtp_config.is_verified if hasattr(smtp_config, 'is_verified') else False,
            "last_used": smtp_config.last_used if hasattr(smtp_config, 'last_used') else None,
            "created_at": smtp_config.created_at if hasattr(smtp_config, 'created_at') else None,
            "updated_at": smtp_config.updated_at if hasattr(smtp_config, 'updated_at') else None,
            "configured": True
        }
        
        return smtp_config_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SMTP config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get SMTP configuration"
        )

@router.post("/smtp/test")
async def test_smtp_config(current_user: User = Depends(get_current_user)):
    """Test SMTP configuration"""
    try:
        smtp_config = email.get_user_smtp_config(current_user.id)
        if not smtp_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SMTP configuration not found"
            )
        
        is_valid, message = email.test_smtp_connection(smtp_config)
        return {"success": is_valid, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMTP test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP test failed"
        )

@router.post("/send-test")
async def send_test_email(
    test_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Send a test email using the user's SMTP configuration"""
    try:
        # Get user's SMTP config
        smtp_config = email.get_user_smtp_config(current_user.id)
        if not smtp_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SMTP configuration not found. Please configure SMTP settings first."
            )
        
        # Extract test email data
        recipient_email = test_data.get('to_email') or test_data.get('recipient_email')
        template_id = test_data.get('template_id')
        subject = test_data.get('subject', 'Test Email from Kale')
        message = test_data.get('message', 'This is a test email sent from Kale Email API Platform.')
        
        if not recipient_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipient email is required"
            )
        
        # If template_id is provided, use template
        html_content = None
        text_content = None
        variables = test_data.get('variables', {})
        
        if template_id:
            # Get template
            template_obj = template.get_template_by_id(current_user.id, template_id)
            if template_obj:
                subject = template_obj.subject
                html_content = template_obj.html_content
                text_content = template_obj.text_content
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found"
                )
        else:
            # Use provided message as HTML content
            html_content = f"<html><body><p>{message}</p></body></html>"
            text_content = message
        
        # Send test email
        success, error_message = await email.send_email(
            smtp_config=smtp_config,
            recipient=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            variables=variables
        )
        
        if success:
            # Log the test email
            email.log_email(
                user_id=current_user.id,
                template_id=template_id or 'test-email',
                recipient=recipient_email,
                subject=subject,
                status='sent'
            )
            
            return {"success": True, "message": "Test email sent successfully"}
        else:
            return {"success": False, "message": f"Failed to send test email: {error_message}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send test email error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )

@router.get("/logs", response_model=List[EmailLog])
async def get_email_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get user's email logs"""
    try:
        logs = email.get_email_logs(current_user.id, limit, offset)
        return logs
        
    except Exception as e:
        logger.error(f"Error getting email logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get email logs"
        )

# API endpoint for sending emails
@router.post("/{username}/{template_id}")
async def send_emails_api(
    username: str,
    template_id: str,
    request: Request,
    email_data: EmailSendRequest,
    api_key: str = None
):
    """Public API endpoint for sending emails"""
    try:
        # Get API key from header if not provided as parameter
        if not api_key:
            api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
        
        # Verify API access
        user = await verify_api_access(api_key, username)
        
        # Check API rate limit
        if not rate_limit.check_api_rate_limit(api_key, f"/{username}/{template_id}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API rate limit exceeded. Max 60 requests per minute."
            )
        
        # Check email rate limit
        can_send, daily_limit, remaining = rate_limit.check_rate_limit(
            user.id, user.is_verified
        )
        
        if not can_send:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily email limit exceeded. Limit: {daily_limit}, Remaining: {remaining}"
            )
        
        # Get template - using the template service
        template_obj = template.get_template_by_id(user.id, template_id)
        if not template_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Get SMTP config
        smtp_config = email.get_user_smtp_config(user.id)
        if not smtp_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMTP configuration not found. Please configure SMTP settings first."
            )
        
        # Send emails
        results = []
        successful_sends = 0
        
        for recipient in email_data.recipients:
            # Check if we've hit the limit
            if successful_sends >= remaining and remaining != -1:
                break
            
            try:
                # Use the enhanced email sending method
                success, error_message, message_id = await email.send_email_enhanced(
                    user_id=user.id,
                    template_id=template_id,
                    recipient_email=recipient,
                    variables=email_data.variables,
                    smtp_config=smtp_config
                )
                
                if success:
                    successful_sends += 1
                    rate_limit.increment_email_count(user.id)
                    status_msg = "sent"
                else:
                    status_msg = "failed"
                
                results.append({
                    "recipient": recipient,
                    "status": status_msg,
                    "message_id": message_id if success else None,
                    "error": error_message if not success else None
                })
                
            except Exception as e:
                logger.error(f"Error sending email to {recipient}: {e}")
                
                results.append({
                    "recipient": recipient,
                    "status": "failed",
                    "message_id": None,
                    "error": str(e)
                })
        
        # Log API usage
        rate_limit.log_api_usage(
            user_id=user.id,
            endpoint=f"/{username}/{template_id}",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            request_data=f"Recipients: {len(email_data.recipients)}",
            response_status=200
        )
        
        logger.info(f"Emails sent via API: {successful_sends}/{len(email_data.recipients)} for user {username}")
        
        return {
            "message": f"Processed {len(results)} emails",
            "successful": successful_sends,
            "failed": len(results) - successful_sends,
            "results": results,
            "remaining_daily_limit": remaining - successful_sends if remaining != -1 else -1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API email sending error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email sending failed"
        )
