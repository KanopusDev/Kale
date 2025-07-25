"""
Public API Routes
Handles the main public email API endpoints: /{username}/{template_id}
Professional implementation with comprehensive security and monitoring
"""

from fastapi import APIRouter, Request, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime

from app.services.public import public_api
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    return request.client.host if request.client else "unknown"

def get_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Extract API key from Authorization header or query parameter"""
    # Try Authorization header first (Bearer token)
    if credentials:
        return credentials.credentials
    
    # Try query parameter
    api_key = request.query_params.get("api_key")
    if api_key:
        return api_key
    
    # Try custom header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key required. Use Authorization header, X-API-Key header, or api_key query parameter."
    )

@router.post("/{username}/{template_id}")
async def send_email_public_api(
    username: str,
    template_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """
    Public Email API Endpoint
    POST /{username}/{template_id}
    
    Send emails using user's template via public API
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    try:
        # Parse request body
        try:
            request_data = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in request body"
            )
        
        # Validate basic input
        if not username or len(username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username"
            )
        
        if not template_id or len(template_id) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid template ID"
            )
        
        if not api_key or len(api_key) < 10:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Call public API service
        success, message, response_data = await public_api.send_email_via_public_api(
            username=username.lower(),
            template_id=template_id.lower(),
            request_data=request_data,
            api_key=api_key,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Return appropriate response
        if success:
            return {
                "success": True,
                "message": message,
                "data": response_data
            }
        else:
            # Determine appropriate HTTP status code
            if "Invalid API key" in message:
                status_code = status.HTTP_401_UNAUTHORIZED
            elif "rate limit" in message.lower():
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            elif "not found" in message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "suspended" in message.lower():
                status_code = status.HTTP_403_FORBIDDEN
            elif "required" in message.lower() or "invalid" in message.lower():
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "success": False,
                    "message": message,
                    "data": response_data
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Public API error: {e}", extra={
            "username": username,
            "template_id": template_id,
            "client_ip": client_ip,
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{username}/{template_id}")
async def get_template_info(
    username: str,
    template_id: str,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Get Template Information
    GET /{username}/{template_id}
    
    Returns template information and available variables
    """
    client_ip = get_client_ip(request)
    
    try:
        # Validate API key and get user
        from app.services.public import PublicAPIService
        service = PublicAPIService()
        
        user = await service._validate_api_key(api_key, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Get template
        template = await service._get_user_template(user.id, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Return template information (excluding sensitive content)
        return {
            "success": True,
            "data": {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "variables": template.variables,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "usage_instructions": {
                    "endpoint": f"/{username}/{template_id}",
                    "method": "POST",
                    "required_fields": ["recipients", "variables"],
                    "example_request": {
                        "recipients": ["user@example.com"],
                        "variables": {var: f"example_{var}" for var in template.variables[:3]}
                    }
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{username}")
async def get_user_templates(
    username: str,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Get User Templates List
    GET /{username}
    
    Returns list of available templates for the user
    """
    try:
        # Validate API key and get user
        from app.services.public import PublicAPIService
        service = PublicAPIService()
        
        user = await service._validate_api_key(api_key, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Get user's templates
        from app.core.database import db_manager
        
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT template_id, name, description, category, variables, created_at, updated_at
            FROM email_templates 
            WHERE (user_id = ? OR is_public = 1 OR is_system_template = 1) 
            AND is_active = 1
            ORDER BY user_id = ? DESC, name ASC
        """, (user.id, user.id))
        
        templates = []
        for row in cursor.fetchall():
            templates.append({
                "template_id": row['template_id'],
                "name": row['name'],
                "description": row['description'],
                "category": row['category'],
                "variables": json.loads(row['variables']) if row['variables'] else [],
                "endpoint": f"/{username}/{row['template_id']}",
                "created_at": row['created_at'],
                "updated_at": row['updated_at']
            })
        
        conn.close()
        
        return {
            "success": True,
            "data": {
                "username": username,
                "total_templates": len(templates),
                "templates": templates
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User templates error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.options("/{username}/{template_id}")
@router.options("/{username}")
async def handle_options(username: str, template_id: str = None):
    """Handle CORS preflight requests"""
    return {
        "methods": ["GET", "POST", "OPTIONS"],
        "headers": ["Authorization", "Content-Type", "X-API-Key"],
        "success": True
    }

# API Documentation endpoints
@router.get("/docs/api")
async def api_documentation():
    """API Documentation"""
    return {
        "title": "Kale Email API Documentation",
        "version": "2.0.0",
        "description": "Enterprise Email API Platform",
        "endpoints": {
            "send_email": {
                "url": "/{username}/{template_id}",
                "method": "POST",
                "description": "Send emails using a template",
                "authentication": "API Key (Bearer token, X-API-Key header, or api_key query param)",
                "parameters": {
                    "username": "Your username",
                    "template_id": "Template identifier"
                },
                "body": {
                    "recipients": "Array of email addresses or single email string",
                    "variables": "Object with template variables (optional)"
                },
                "response": {
                    "success": "Boolean indicating success",
                    "message": "Response message",
                    "data": {
                        "request_id": "Unique request identifier",
                        "sent_count": "Number of emails sent",
                        "failed_count": "Number of failed emails",
                        "results": "Detailed results per recipient"
                    }
                }
            },
            "get_template": {
                "url": "/{username}/{template_id}",
                "method": "GET",
                "description": "Get template information and variables",
                "authentication": "API Key",
                "response": "Template details and usage instructions"
            },
            "list_templates": {
                "url": "/{username}",
                "method": "GET",
                "description": "Get list of available templates",
                "authentication": "API Key",
                "response": "Array of available templates"
            }
        },
        "rate_limits": {
            "verified_users": "Unlimited emails per day",
            "unverified_users": "1,000 emails per day",
            "api_calls": "60 per minute, 3,600 per hour",
            "burst_limit": "100 emails per 5 minutes"
        },
        "error_codes": {
            "400": "Bad Request - Invalid input data",
            "401": "Unauthorized - Invalid or missing API key",
            "403": "Forbidden - Account suspended or insufficient permissions",
            "404": "Not Found - Template or user not found",
            "429": "Too Many Requests - Rate limit exceeded",
            "500": "Internal Server Error - Server error"
        }
    }
