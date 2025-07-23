from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
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
        # Test SMTP connection first
        test_config = SMTPConfig(
            id=0,
            user_id=current_user.id,
            **config_data.dict(),
            is_active=True,
            created_at=""
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

@router.get("/smtp", response_model=SMTPConfig)
async def get_smtp_config(current_user: User = Depends(get_current_user)):
    """Get user's SMTP configuration"""
    try:
        smtp_config = email.get_user_smtp_config(current_user.id)
        if not smtp_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SMTP configuration not found"
            )
        
        return smtp_config
        
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
        
        # Get template
        template = template.get_template_by_id(user.id, template_id)
        if not template:
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
                success, error_message = await email.send_email(
                    smtp_config=smtp_config,
                    recipient=recipient,
                    subject=template.subject,
                    html_content=template.html_content,
                    text_content=template.text_content,
                    variables=email_data.variables
                )
                
                if success:
                    successful_sends += 1
                    rate_limit.increment_email_count(user.id)
                    status_msg = "sent"
                else:
                    status_msg = "failed"
                
                # Log email attempt
                email.log_email(
                    user_id=user.id,
                    template_id=template_id,
                    recipient=recipient,
                    subject=template.subject,
                    status=status_msg,
                    error_message=error_message if not success else None
                )
                
                results.append({
                    "recipient": recipient,
                    "status": status_msg,
                    "error": error_message if not success else None
                })
                
            except Exception as e:
                logger.error(f"Error sending email to {recipient}: {e}")
                email.log_email(
                    user_id=user.id,
                    template_id=template_id,
                    recipient=recipient,
                    subject=template.subject,
                    status="failed",
                    error_message=str(e)
                )
                
                results.append({
                    "recipient": recipient,
                    "status": "failed",
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
