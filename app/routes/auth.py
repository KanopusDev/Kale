from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.models.schemas import UserCreate, UserLogin, User, Token, UserUpdate
from app.services.user import user_service as user
from app.core.security import security
from app.core.deps import get_current_user, get_current_admin_user
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        logger.info(f"Registration attempt: username={user_data.username}, email={user_data.email}")
        
        # Validate password strength
        is_strong, message = security.is_strong_password(user_data.password)
        if not is_strong:
            logger.warning(f"Password validation failed for {user_data.email}: {message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Create user
        created_user = user.create_user(user_data)
        if not created_user:
            logger.warning(f"Registration failed - user already exists: username={user_data.username}, email={user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        logger.info(f"User registered successfully: {created_user.username}")
        return created_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        # Authenticate user
        authenticated_user = user.authenticate_user(user_data)
        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token = security.create_access_token(
            data={"sub": str(authenticated_user.id), "username": authenticated_user.username}
        )
        
        logger.info(f"User logged in successfully: {authenticated_user.username}")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": authenticated_user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user information"""
    try:
        # Validate new password if provided
        if user_data.new_password:
            is_strong, message = security.is_strong_password(user_data.new_password)
            if not is_strong:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message
                )
        
        # Update user
        success = user.update_user(current_user.id, user_data, current_user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed. Check your current password or email availability."
            )
        
        # Return updated user info
        updated_user = user.get_user_by_id(current_user.id)
        logger.info(f"User updated successfully: {current_user.username}")
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )

@router.post("/verify/{user_id}")
async def verify_user(
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
        logger.error(f"User verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )
