from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models.schemas import (
    User, DashboardStats, AdminStats, EmailLog
)
from app.services.user import user_service as user
from app.services.email import email
from app.services.template import template
from app.services.limitter import rate_limit
from app.core.deps import get_current_user, get_current_admin_user
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_user_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get user dashboard statistics"""
    try:
        # Get email statistics
        total_emails = len(email.get_email_logs(current_user.id, limit=10000))
        emails_today = email.get_daily_email_count(current_user.id)
        
        # Get template count
        templates = template.get_user_templates(current_user.id, limit=10000)
        total_templates = len(templates)
        
        # Get SMTP config status
        smtp_config = email.get_user_smtp_config(current_user.id)
        active_smtp_configs = 1 if smtp_config else 0
        
        # Get rate limit info
        daily_limit = settings.VERIFIED_DAILY_LIMIT if current_user.is_verified else settings.UNVERIFIED_DAILY_LIMIT
        remaining_today = daily_limit - emails_today if daily_limit != -1 else -1
        
        return DashboardStats(
            total_emails_sent=total_emails,
            emails_sent_today=emails_today,
            total_templates=total_templates,
            active_smtp_configs=active_smtp_configs,
            daily_limit=daily_limit,
            remaining_today=remaining_today
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics"
        )

