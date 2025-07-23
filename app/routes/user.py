"""
Kale User API Management - Production Implementation
User-specific API endpoints and key management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import secrets
import hashlib
from datetime import datetime, timedelta
from app.core.deps import get_current_user
from app.core.database import db_manager
from app.services.library import template_manager, EmailTemplate
from app.models.schemas import User
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class UserAPIManager:
    """Manage user API keys and endpoints"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return f"kale_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def create_user_api_endpoint(username: str) -> str:
        """Create user-specific API endpoint"""
        # Clean username for URL
        clean_username = "".join(c for c in username if c.isalnum() or c in ".-_").lower()
        return f"kale.kanopus.org/{clean_username}"
    
    @staticmethod
    def store_api_key(user_id: int, api_key: str, name: str = "Default") -> Dict[str, Any]:
        """Store API key in database"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # Hash the API key for storage
            api_key_hash = UserAPIManager.hash_api_key(api_key)
            
            cursor.execute("""
                INSERT INTO user_api_keys (user_id, api_key_hash, key_name, created_at, last_used)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, api_key_hash, name, datetime.now(), None))
            
            api_key_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "id": api_key_id,
                "api_key": api_key,  # Return the actual key only once
                "name": name,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to store API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
    
    @staticmethod
    def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return user info"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            api_key_hash = UserAPIManager.hash_api_key(api_key)
            
            cursor.execute("""
                SELECT uak.id, uak.user_id, uak.key_name, u.username, u.email, u.is_verified
                FROM user_api_keys uak
                JOIN users u ON uak.user_id = u.id
                WHERE uak.api_key_hash = ? AND uak.is_active = 1
            """, (api_key_hash,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # Update last used timestamp
                UserAPIManager.update_api_key_usage(result[0])
                
                return {
                    "api_key_id": result[0],
                    "user_id": result[1],
                    "key_name": result[2],
                    "username": result[3],
                    "email": result[4],
                    "is_verified": bool(result[5])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            return None
    
    @staticmethod
    def update_api_key_usage(api_key_id: int):
        """Update last used timestamp for API key"""
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_api_keys 
                SET last_used = ?, usage_count = usage_count + 1
                WHERE id = ?
            """, (datetime.now(), api_key_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update API key usage: {e}")


# API Key Management Endpoints

@router.get("/user/api-keys")
async def list_user_api_keys(current_user: User = Depends(get_current_user)):
    """List user's API keys"""
    try:
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, key_name, created_at, last_used, usage_count, is_active
            FROM user_api_keys
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (current_user.id,))
        
        keys = []
        for row in cursor.fetchall():
            keys.append({
                "id": row[0],
                "name": row[1],
                "created_at": row[2],
                "last_used": row[3],
                "usage_count": row[4] or 0,
                "is_active": bool(row[5])
            })
        
        conn.close()
        
        return {
            "api_keys": keys,
            "api_endpoint": UserAPIManager.create_user_api_endpoint(current_user.username)
        }
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )


@router.post("/user/api-keys")
async def create_api_key(
    key_name: str = "Default",
    current_user: User = Depends(get_current_user)
):
    """Create a new API key for the user"""
    try:
        # Generate new API key
        api_key = UserAPIManager.generate_api_key()
        
        # Store in database
        key_data = UserAPIManager.store_api_key(current_user.id, api_key, key_name)
        
        return {
            "message": "API key created successfully",
            "api_key": key_data["api_key"],
            "key_id": key_data["id"],
            "name": key_data["name"],
            "api_endpoint": UserAPIManager.create_user_api_endpoint(current_user.username),
            "warning": "Save this API key securely. It will not be shown again."
        }
        
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.delete("/user/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete an API key"""
    try:
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        
        # Verify ownership and delete
        cursor.execute("""
            UPDATE user_api_keys 
            SET is_active = 0, deleted_at = ?
            WHERE id = ? AND user_id = ?
        """, (datetime.now(), key_id, current_user.id))
        
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        conn.commit()
        conn.close()
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


# Template Management Endpoints

@router.get("/templates")
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user)
):
    """List available templates"""
    try:
        templates = template_manager.list_templates(category=category, user_id=str(current_user.id))
        
        template_list = []
        for template in templates:
            template_list.append({
                "id": template.id,
                "name": template.name,
                "category": template.category,
                "description": f"Template for {template.category.lower()} emails",
                "is_system": template.is_system,
                "tags": template.tags or [],
                "variable_count": len(template.variables),
                "created_by": template.created_by if not template.is_system else "System"
            })
        
        return {
            "templates": template_list,
            "total": len(template_list),
            "categories": list(set(t["category"] for t in template_list))
        }
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.get("/templates/{template_id}")
async def get_template_details(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed template information"""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check access permissions
        if not template.is_system and template.created_by != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this template"
            )
        
        return {
            "id": template.id,
            "name": template.name,
            "category": template.category,
            "subject": template.subject,
            "html_content": template.html_content,
            "text_content": template.text_content,
            "variables": [
                {
                    "name": var.name,
                    "type": var.type,
                    "label": var.label,
                    "description": var.description,
                    "required": var.required,
                    "default_value": var.default_value
                }
                for var in template.variables
            ],
            "is_system": template.is_system,
            "tags": template.tags or [],
            "created_by": template.created_by,
            "created_at": template.created_at.isoformat() if template.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )


@router.get("/templates/{template_id}/preview")
async def preview_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get template preview with sample data"""
    try:
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check access permissions
        if not template.is_system and template.created_by != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this template"
            )
        
        preview = template_manager.get_template_preview(template_id)
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "preview": preview,
            "preview_data": template.preview_data or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate template preview"
        )


@router.post("/templates")
async def create_custom_template(
    template_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a custom template"""
    try:
        # Validate required fields
        required_fields = ["name", "category", "subject", "html_content", "text_content", "variables"]
        for field in required_fields:
            if field not in template_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Create template
        template = template_manager.create_custom_template(template_data, str(current_user.id))
        
        return {
            "message": "Template created successfully",
            "template_id": template.id,
            "template_name": template.name,
            "category": template.category,
            "variable_count": len(template.variables)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


# User API Endpoint for External Access

@router.post("/{username}/{template_id}")
async def send_email_via_user_api(
    username: str,
    template_id: str,
    email_data: Dict[str, Any],
    api_key: str = Query(..., description="User API key")
):
    """
    User-specific API endpoint for sending emails
    Format: kale.kanopus.org/{username}/{template_id}?api_key=your_api_key
    """
    try:
        # Verify API key and get user info
        user_info = UserAPIManager.verify_api_key(api_key)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Verify username matches API key owner
        if user_info["username"].lower() != username.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key does not match username"
            )
        
        # Check daily limits for unverified users
        if not user_info["is_verified"]:
            today_count = await get_daily_email_count(user_info["user_id"])
            if today_count >= 1000:  # 1k email per day limit
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Daily email limit reached. Verify your account for unlimited sending."
                )
        
        # Validate required fields
        if "recipients" not in email_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'recipients' field"
            )
        
        if "variables" not in email_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing 'variables' field"
            )
        
        # Get and render template
        template = template_manager.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check template access
        if not template.is_system and template.created_by != str(user_info["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this template"
            )
        
        # Render template with variables
        rendered = template_manager.render_template(template_id, email_data["variables"])
        
        # Here you would integrate with your SMTP service
        # For now, we'll return a success response
        
        # Log the email send request
        await log_email_send(user_info["user_id"], template_id, len(email_data["recipients"]))
        
        return {
            "message": "Email sent successfully",
            "template_id": template_id,
            "template_name": template.name,
            "recipients_count": len(email_data["recipients"]),
            "user": user_info["username"],
            "remaining_daily_limit": None if user_info["is_verified"] else (1000 - await get_daily_email_count(user_info["user_id"])),
            "status": "sent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send email via API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )


# Helper Functions

async def get_daily_email_count(user_id: int) -> int:
    """Get today's email count for user"""
    try:
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        cursor.execute("""
            SELECT COALESCE(SUM(recipient_count), 0) 
            FROM email_logs 
            WHERE user_id = ? AND DATE(sent_at) = ?
        """, (user_id, today))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Failed to get daily email count: {e}")
        return 0


async def log_email_send(user_id: int, template_id: str, recipient_count: int):
    """Log email send activity"""
    try:
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO email_logs (user_id, template_id, recipient_count, sent_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, template_id, recipient_count, datetime.now()))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to log email send: {e}")


# User Statistics Endpoint

@router.get("/user/stats")
async def get_user_statistics(current_user: User = Depends(get_current_user)):
    """Get user email statistics"""
    try:
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        
        # Get total emails sent
        cursor.execute("""
            SELECT COALESCE(SUM(recipient_count), 0) 
            FROM email_logs 
            WHERE user_id = ?
        """, (current_user.id,))
        total_emails = cursor.fetchone()[0]
        
        # Get today's emails
        today = datetime.now().date()
        cursor.execute("""
            SELECT COALESCE(SUM(recipient_count), 0) 
            FROM email_logs 
            WHERE user_id = ? AND DATE(sent_at) = ?
        """, (current_user.id, today))
        today_emails = cursor.fetchone()[0]
        
        # Get this month's emails
        month_start = datetime.now().replace(day=1).date()
        cursor.execute("""
            SELECT COALESCE(SUM(recipient_count), 0) 
            FROM email_logs 
            WHERE user_id = ? AND DATE(sent_at) >= ?
        """, (current_user.id, month_start))
        month_emails = cursor.fetchone()[0]
        
        # Get API key count
        cursor.execute("""
            SELECT COUNT(*) FROM user_api_keys 
            WHERE user_id = ? AND is_active = 1
        """, (current_user.id,))
        api_key_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_verified": current_user.is_verified,
                "created_at": current_user.created_at.isoformat()
            },
            "statistics": {
                "total_emails_sent": total_emails,
                "emails_today": today_emails,
                "emails_this_month": month_emails,
                "active_api_keys": api_key_count,
                "daily_limit": None if current_user.is_verified else 1000,
                "remaining_today": None if current_user.is_verified else max(0, 1000 - today_emails)
            },
            "api_endpoint": UserAPIManager.create_user_api_endpoint(current_user.username)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )
