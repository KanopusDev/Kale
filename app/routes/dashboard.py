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

@router.get("/admin/stats", response_model=AdminStats)
async def get_admin_dashboard_stats(admin_user: User = Depends(get_current_admin_user)):
    """Get admin dashboard statistics"""
    try:
        # Get all users
        all_users = user.get_all_users(limit=10000)
        total_users = len(all_users)
        verified_users = len([u for u in all_users if u.is_verified])
        
        # Get template statistics
        all_templates = template.get_public_templates(limit=10000)
        total_templates = len(all_templates)
        system_templates = len([t for t in all_templates if t.is_system_template])
        
        # Calculate total emails sent (this is a simplified calculation)
        total_emails = 0
        emails_today = 0
        active_users_today = 0
        
        for user in all_users:
            user_emails = email.get_email_logs(user.id, limit=10000)
            total_emails += len(user_emails)
            
            user_emails_today = email.get_daily_email_count(user.id)
            emails_today += user_emails_today
            
            if user_emails_today > 0:
                active_users_today += 1
        
        return AdminStats(
            total_users=total_users,
            verified_users=verified_users,
            total_emails_sent=total_emails,
            emails_sent_today=emails_today,
            total_templates=total_templates,
            system_templates=system_templates,
            active_users_today=active_users_today
        )
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get admin dashboard statistics"
        )

@router.get("/admin/users", response_model=List[User])
async def get_all_users_admin(
    limit: int = 100,
    offset: int = 0,
    admin_user: User = Depends(get_current_admin_user)
):
    """Get all users (admin only)"""
    try:
        users = user.get_all_users(limit, offset)
        return users
        
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )

@router.get("/admin/emails", response_model=List[EmailLog])
async def get_all_email_logs_admin(
    limit: int = 100,
    offset: int = 0,
    admin_user: User = Depends(get_current_admin_user)
):
    """Get all email logs (admin only)"""
    try:
        # Get all users first
        all_users = user.get_all_users(limit=10000)
        
        # Get email logs for all users (simplified approach)
        all_logs = []
        for user in all_users:
            user_logs = email.get_email_logs(user.id, limit=limit//len(all_users) if all_users else limit)
            all_logs.extend(user_logs)
        
        # Sort by sent_at and apply pagination
        all_logs.sort(key=lambda x: x.sent_at, reverse=True)
        return all_logs[offset:offset+limit]
        
    except Exception as e:
        logger.error(f"Error getting all email logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get email logs"
        )

@router.post("/admin/verify-user/{user_id}")
async def verify_user_admin(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user)
):
    """Verify a user (admin only)"""
    try:
        success = user.verify_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User {user_id} verified by admin {admin_user.username}")
        return {"message": "User verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin user verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User verification failed"
        )

@router.get("/admin/user/{user_id}/api-usage")
async def get_user_api_usage_admin(
    user_id: int,
    limit: int = 100,
    offset: int = 0,
    admin_user: User = Depends(get_current_admin_user)
):
    """Get API usage for specific user (admin only)"""
    try:
        usage_logs = rate_limit.get_user_api_usage(user_id, limit, offset)
        return usage_logs
        
    except Exception as e:
        logger.error(f"Error getting user API usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API usage"
        )
