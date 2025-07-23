from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.core.security import security
from app.services.user import user_service
from app.models.schemas import User
import logging

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Debug logging
        logger.info(f"Received token: {credentials.credentials[:50]}...")
        
        # Verify JWT token
        payload = security.verify_token(credentials.credentials)
        logger.info(f"Token payload: {payload}")
        
        if payload is None:
            logger.error("Token verification failed - payload is None")
            raise credentials_exception
        
        # Get user ID from token
        user_id_str: str = payload.get("sub")
        logger.info(f"User ID string from token: {user_id_str}")
        
        if user_id_str is None:
            logger.error("User ID not found in token payload")
            raise credentials_exception
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id_str}")
            raise credentials_exception
        
        # Get user from database
        user_obj = user_service.get_user_by_id(user_id)
        if user_obj is None:
            logger.error(f"User not found in database: {user_id}")
            raise credentials_exception
        
        logger.info(f"Authentication successful for user: {user_obj.username}")
        return user_obj
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise credentials_exception

async def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified"
        )
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_user_from_api_key(api_key: str) -> Optional[User]:
    """Get user from API key"""
    try:
        if not api_key or not api_key.startswith("kale_"):
            return None
        
        user_obj = user_service.get_user_by_api_key(api_key)
        return user_obj
        
    except Exception as e:
        logger.error(f"API key authentication error: {e}")
        return None

async def verify_api_access(api_key: str, username: str) -> User:
    """Verify API access with key and username"""
    # Get user by API key
    user_obj = await get_user_from_api_key(api_key)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Verify username matches
    if user_obj.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not match username"
        )
    
    return user_obj
