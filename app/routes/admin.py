"""
Admin Dashboard Routes
Professional admin functionality for monitoring and management
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.schemas import User, AdminStats, EmailLog
from app.services.user import user_service as user
from app.services.email import email
from app.core.database import db_manager
from app.core.security import security
from app.routes.auth import get_current_user
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: User = Depends(require_admin)):
    """Admin dashboard page"""
    return templates.TemplateResponse(
        "admin.html", 
        {"request": request, "user": admin}
    )

@router.get("/stats")
async def get_admin_stats(admin: User = Depends(require_admin)) -> AdminStats:
    """Get comprehensive admin statistics"""
    try:
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
            total_users = cursor.fetchone()['count']
            
            # Verified users
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_verified = 1 AND is_active = 1")
            verified_users = cursor.fetchone()['count']
            
            # Total emails sent
            cursor.execute("SELECT COUNT(*) as count FROM email_logs WHERE status = 'sent'")
            total_emails_sent = cursor.fetchone()['count']
            
            # Emails sent today
            cursor.execute("""
                SELECT COUNT(*) as count FROM email_logs 
                WHERE status = 'sent' AND DATE(sent_at) = DATE('now')
            """)
            emails_sent_today = cursor.fetchone()['count']
            
            # Total templates
            cursor.execute("SELECT COUNT(*) as count FROM email_templates")
            total_templates = cursor.fetchone()['count']
            
            # System templates
            cursor.execute("SELECT COUNT(*) as count FROM email_templates WHERE is_system_template = 1")
            system_templates = cursor.fetchone()['count']
            
            # Active users today
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as count FROM email_logs 
                WHERE DATE(sent_at) = DATE('now')
            """)
            active_users_today = cursor.fetchone()['count']
            
            return AdminStats(
                total_users=total_users,
                verified_users=verified_users,
                total_emails_sent=total_emails_sent,
                emails_sent_today=emails_sent_today,
                total_templates=total_templates,
                system_templates=system_templates,
                active_users_today=active_users_today
            )
            
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@router.get("/users")
async def get_users(
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    verified_only: Optional[bool] = Query(None),
    active_only: bool = Query(True)
) -> Dict[str, Any]:
    """Get paginated list of users with filtering"""
    try:
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query
            where_conditions = ["1=1"]
            params = []
            
            if active_only:
                where_conditions.append("is_active = ?")
                params.append(1)
            
            if verified_only is not None:
                where_conditions.append("is_verified = ?")
                params.append(verified_only)
            
            if search:
                where_conditions.append("(username LIKE ? OR email LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE {where_clause}", params)
            total = cursor.fetchone()['count']
            
            # Get paginated results
            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT id, username, email, is_verified, is_admin, is_active,
                       created_at, last_login, last_activity
                FROM users
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset])
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    "id": row['id'],
                    "username": row['username'],
                    "email": row['email'],
                    "is_verified": bool(row['is_verified']),
                    "is_admin": bool(row['is_admin']),
                    "is_active": bool(row['is_active']),
                    "created_at": row['created_at'],
                    "last_login": row['last_login'],
                    "last_activity": row['last_activity']
                })
            
            return {
                "users": users,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get users")

@router.patch("/users/{user_id}")
async def update_user_admin(
    user_id: int,
    update_data: Dict[str, Any],
    admin: User = Depends(require_admin)
):
    """Update user as admin"""
    try:
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Validate user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="User not found")
            
            # Prepare update fields
            allowed_fields = ['is_verified', 'is_admin', 'is_active']
            update_fields = []
            params = []
            
            for field, value in update_data.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No valid fields to update")
            
            # Update user
            params.append(datetime.utcnow())
            params.append(user_id)
            
            cursor.execute(f"""
                UPDATE users 
                SET {', '.join(update_fields)}, updated_at = ?
                WHERE id = ?
            """, params)
            
            conn.commit()
            
            # Log admin action
            await log_admin_action(admin.id, "update_user", {
                "target_user_id": user_id,
                "changes": update_data
            })
            
            return {"message": "User updated successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.post("/users/{user_id}/verify")
async def verify_user(
    user_id: int,
    admin: User = Depends(require_admin)
):
    """Verify a user account"""
    try:
        logger.info(f"Admin {admin.username} (ID: {admin.id}) attempting to verify user {user_id}")
        
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Validate user exists
            cursor.execute("SELECT id, username, is_verified FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                logger.warning(f"Admin {admin.username} tried to verify non-existent user {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            
            if user_data['is_verified']:
                logger.info(f"User {user_id} ({user_data['username']}) is already verified")
                return {"message": "User is already verified"}
            
            # Verify user
            cursor.execute(
                "UPDATE users SET is_verified = 1, verified_at = ?, updated_at = ? WHERE id = ?", 
                (datetime.utcnow(), datetime.utcnow(), user_id)
            )
            conn.commit()
            
            logger.info(f"User {user_id} ({user_data['username']}) verified successfully by admin {admin.username}")
            
            # Log admin action
            await log_admin_action(admin.id, "user_verify", {
                "target_user_id": user_id,
                "target_username": user_data['username']
            })
            
            return {"message": "User verified successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify user")

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    admin: User = Depends(require_admin)
):
    """Suspend a user account"""
    try:
        logger.info(f"Admin {admin.username} (ID: {admin.id}) attempting to suspend user {user_id}")
        
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Validate user exists and is not admin
            cursor.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                logger.warning(f"Admin {admin.username} tried to suspend non-existent user {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            
            if user_data['is_admin']:
                logger.warning(f"Admin {admin.username} tried to suspend another admin user {user_id} ({user_data['username']})")
                raise HTTPException(status_code=400, detail="Cannot suspend admin users")
            
            # Suspend user
            cursor.execute(
                "UPDATE users SET is_active = 0, suspended_at = ?, updated_at = ? WHERE id = ?", 
                (datetime.utcnow(), datetime.utcnow(), user_id)
            )
            conn.commit()
            
            logger.info(f"User {user_id} ({user_data['username']}) suspended successfully by admin {admin.username}")
            
            # Log admin action
            await log_admin_action(admin.id, "user_suspend", {
                "target_user_id": user_id,
                "target_username": user_data['username']
            })
            
            return {"message": "User suspended successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suspending user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to suspend user")

@router.get("/email-logs")
async def get_email_logs(
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90)
) -> Dict[str, Any]:
    """Get email logs with filtering"""
    try:
        logger.info(f"Admin {admin.username} requesting email logs: page={page}, limit={limit}, user_id={user_id}, status={status}, days={days}")
        
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query
            where_conditions = ["sent_at >= datetime('now', '-' || ? || ' days')"]
            params = [days]
            
            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)
            
            if status:
                where_conditions.append("status = ?")
                params.append(status)
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            cursor.execute(f"SELECT COUNT(*) as count FROM email_logs WHERE {where_clause}", params)
            total = cursor.fetchone()[0]
            
            logger.info(f"Found {total} email logs matching criteria")
            
            # Get paginated results with better error handling
            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT el.id, el.user_id, el.template_id, el.recipient_email, 
                       el.subject, el.status, el.error_message, el.sent_at, 
                       el.message_id, u.username, u.email as user_email
                FROM email_logs el
                JOIN users u ON el.user_id = u.id
                WHERE {where_clause}
                ORDER BY el.sent_at DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset])
            
            logs = []
            for row in cursor.fetchall():
                # Convert SQLite Row to dict safely
                log_entry = {
                    "id": row[0] if len(row) > 0 else None,
                    "user_id": row[1] if len(row) > 1 else None,
                    "template_id": row[2] if len(row) > 2 else None,
                    "recipient_email": row[3] if len(row) > 3 else None,
                    "subject": row[4] if len(row) > 4 else None,
                    "status": row[5] if len(row) > 5 else None,
                    "error_message": row[6] if len(row) > 6 else None,
                    "sent_at": row[7] if len(row) > 7 else None,
                    "message_id": row[8] if len(row) > 8 else None,
                    "username": row[9] if len(row) > 9 else None,
                    "user_email": row[10] if len(row) > 10 else None
                }
                logs.append(log_entry)
            
            logger.info(f"Successfully retrieved {len(logs)} email logs for admin {admin.username}")
            
            return {
                "logs": logs,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting email logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get email logs")

@router.get("/system-health")
async def get_system_health(admin: User = Depends(require_admin)):
    """Get system health metrics"""
    try:
        health_data = {}
        
        # Database health
        try:
            with db_manager.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                health_data["database"] = {
                    "status": "healthy",
                    "connection_pool_size": db_manager.connection_pool.pool_size,
                    "active_connections": db_manager.connection_pool.total_connections
                }
        except Exception as e:
            health_data["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Redis health
        try:
            redis_client = db_manager.redis_pool.get_client()
            redis_client.ping()
            redis_info = redis_client.info()
            health_data["redis"] = {
                "status": "healthy",
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory": redis_info.get("used_memory_human", "unknown"),
                "uptime": redis_info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            health_data["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Email service health
        health_data["email"] = {
            "status": "healthy",
            "note": "Email service operational"
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")

@router.get("/analytics")
async def get_analytics_data(
    admin: User = Depends(require_admin),
    days: int = Query(30, ge=1, le=365)
):
    """Get analytics data for charts and reporting"""
    try:
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Email volume over time
            cursor.execute("""
                SELECT DATE(sent_at) as date, COUNT(*) as count
                FROM email_logs
                WHERE sent_at >= datetime('now', '-' || ? || ' days')
                AND status = 'sent'
                GROUP BY DATE(sent_at)
                ORDER BY date
            """, (days,))
            
            email_volume = [
                {"date": row['date'], "count": row['count']}
                for row in cursor.fetchall()
            ]
            
            # User registration over time
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM users
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            
            user_registrations = [
                {"date": row['date'], "count": row['count']}
                for row in cursor.fetchall()
            ]
            
            # Top templates by usage
            cursor.execute("""
                SELECT template_id, COUNT(*) as usage_count
                FROM email_logs
                WHERE sent_at >= datetime('now', '-' || ? || ' days')
                AND status = 'sent'
                GROUP BY template_id
                ORDER BY usage_count DESC
                LIMIT 10
            """, (days,))
            
            top_templates = [
                {"template_id": row['template_id'], "usage_count": row['usage_count']}
                for row in cursor.fetchall()
            ]
            
            # Email status distribution
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM email_logs
                WHERE sent_at >= datetime('now', '-' || ? || ' days')
                GROUP BY status
            """, (days,))
            
            status_distribution = [
                {"status": row['status'], "count": row['count']}
                for row in cursor.fetchall()
            ]
            
            return {
                "email_volume": email_volume,
                "user_registrations": user_registrations,
                "top_templates": top_templates,
                "status_distribution": status_distribution,
                "period_days": days
            }
            
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics data")

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin)
):
    """Delete user and all associated data (GDPR compliance)"""
    try:
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verify user exists
            cursor.execute("SELECT username, email FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Don't allow deleting admins
            cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
            if cursor.fetchone()['is_admin']:
                raise HTTPException(status_code=400, detail="Cannot delete admin users")
            
            # Delete user data (cascading deletes)
            cursor.execute("DELETE FROM api_usage_logs WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM email_logs WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM smtp_configs WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM email_templates WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            
            # Log admin action
            await log_admin_action(admin.id, "delete_user", {
                "deleted_user_id": user_id,
                "deleted_username": user_data['username'],
                "deleted_email": user_data['email']
            })
            
            return {"message": "User and all associated data deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

async def log_admin_action(admin_id: int, action: str, details: Dict[str, Any]):
    """Log admin actions for audit trail"""
    try:
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_logs
                (user_id, action, resource_type, new_values, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (admin_id, action, "admin_action", json.dumps(details), datetime.utcnow()))
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")

@router.get("/audit-logs")
async def get_audit_logs(
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get admin audit logs"""
    try:
        with db_manager.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM audit_logs WHERE resource_type = 'admin_action'")
            total = cursor.fetchone()['count']
            
            # Get paginated results
            offset = (page - 1) * limit
            cursor.execute("""
                SELECT al.*, u.username as admin_username
                FROM audit_logs al
                JOIN users u ON al.user_id = u.id
                WHERE al.resource_type = 'admin_action'
                ORDER BY al.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    "id": row['id'],
                    "admin_id": row['user_id'],
                    "admin_username": row['username'],
                    "action": row['action'],
                    "details": json.loads(row['new_values']) if row['new_values'] else {},
                    "created_at": row['created_at']
                })
            
            return {
                "logs": logs,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")
