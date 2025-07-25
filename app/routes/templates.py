from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models.schemas import (
    EmailTemplate, EmailTemplateCreate, User
)
from app.services.template import template
from app.core.deps import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])

@router.post("/", response_model=EmailTemplate, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=EmailTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: EmailTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new email template"""
    try:
        logger.info(f"Template creation request from user {current_user.username}: template_id={template_data.template_id}")
        
        # Enhanced validation with detailed error messages
        if not template_data.template_id or not template_data.template_id.strip():
            logger.warning(f"Empty template_id provided by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template ID cannot be empty"
            )
        
        if not template_data.name or not template_data.name.strip():
            logger.warning(f"Empty template name provided by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template name cannot be empty"
            )
        
        if not template_data.subject or not template_data.subject.strip():
            logger.warning(f"Empty template subject provided by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template subject cannot be empty"
            )
        
        if not template_data.html_content or not template_data.html_content.strip():
            logger.warning(f"Empty template HTML content provided by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template HTML content cannot be empty"
            )
        
        # Additional validation for template_id format
        import re
        clean_id = template_data.template_id.strip().lower()
        if not re.match(r'^[a-z0-9_-]+$', clean_id):
            logger.warning(f"Invalid template_id format provided by user {current_user.username}: {template_data.template_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template ID can only contain lowercase letters, numbers, hyphens, and underscores"
            )
        
        if len(clean_id) < 3:
            logger.warning(f"Template_id too short provided by user {current_user.username}: {template_data.template_id}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Template ID must be at least 3 characters long"
            )
        
        # Create template
        new_template = template.create_template(current_user.id, template_data)
        if not new_template:
            logger.warning(f"Template ID {template_data.template_id} already exists for user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template with ID '{template_data.template_id}' already exists"
            )
        
        logger.info(f"Template created successfully: {new_template.template_id} by user {current_user.username}")
        return new_template
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.warning(f"Template validation error for user {current_user.username}: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Template creation error for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template creation failed: {str(e)}"
        )

@router.get("/", response_model=List[EmailTemplate])
@router.get("", response_model=List[EmailTemplate])
async def get_user_templates(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get user's email templates"""
    try:
        templates = template.get_user_templates(current_user.id, limit, offset)
        return templates
        
    except Exception as e:
        logger.error(f"Error getting user templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get templates"
        )

@router.get("/public", response_model=List[EmailTemplate])
async def get_public_templates(
    limit: int = 100,
    offset: int = 0,
    category: Optional[str] = None
):
    """Get public and system templates"""
    try:
        templates = template.get_public_templates(limit, offset, category)
        return templates
        
    except Exception as e:
        logger.error(f"Error getting public templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get public templates"
        )

@router.get("/categories", response_model=List[str])
async def get_template_categories():
    """Get all template categories"""
    try:
        categories = template.get_template_categories()
        return categories
        
    except Exception as e:
        logger.error(f"Error getting template categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get categories"
        )

@router.get("/{template_id}", response_model=EmailTemplate)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific template by ID"""
    try:
        template_result = template.get_template_by_id(current_user.id, template_id)
        if not template_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return template_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get template"
        )

@router.put("/{template_id}", response_model=EmailTemplate)
async def update_template(
    template_id: str,
    template_data: EmailTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """Update an existing template"""
    try:
        success = template.update_template(current_user.id, template_id, template_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )
        
        # Return updated template
        updated_template = template.get_template_by_id(current_user.id, template_id)
        logger.info(f"Template updated: {template_id} by user {current_user.username}")
        return updated_template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template update failed"
        )

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a template"""
    try:
        success = template.delete_template(current_user.id, template_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )
        
        logger.info(f"Template deleted: {template_id} by user {current_user.username}")
        return {"message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template deletion failed"
        )
