from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

templates = Jinja2Templates(directory="templates")
router = APIRouter()
logger = logging.getLogger(__name__)


class SupportRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    priority: str
    message: str

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """Privacy Policy page"""
    return templates.TemplateResponse("privacy.html", {
        "request": request,
        "title": "Privacy Policy - Kale"
    })

@router.get("/terms", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    """Terms of Service page"""
    return templates.TemplateResponse("terms.html", {
        "request": request,
        "title": "Terms of Service - Kale"
    })

@router.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    """Support page"""
    return templates.TemplateResponse("support.html", {
        "request": request,
        "title": "Support - Kale"
    })

@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """System status page"""
    return templates.TemplateResponse("status.html", {
        "request": request,
        "title": "System Status - Kale"
    })

@router.post("/api/support/contact")
async def submit_support_request(support_request: SupportRequest):
    """Handle support form submission"""
    try:
        # Log the support request
        logger.info(f"Support request received from {support_request.email}: {support_request.subject}")
        
        # In production, you could:
        # 1. Send email to support team
        # 2. Create ticket in support system
        # 3. Store in database
        
        # For now, just return success
        return {"message": "Support request submitted successfully", "status": "success"}
        
    except Exception as e:
        logger.error(f"Error handling support request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit support request"
        )


@router.post("/api/support/contact")
async def submit_support_request(request: SupportRequest):
    """Handle support form submissions"""
    try:
        # Log the support request
        logger.info(f"Support request from {request.email}: {request.subject}")
        
        # In a real implementation, you would:
        # 1. Save to database
        # 2. Send email notification to support team
        # 3. Send confirmation email to user
        # 4. Create ticket in support system
        
        # For now, just log and return success
        logger.info(f"Support request details: {request.dict()}")
        
        return JSONResponse(
            content={"message": "Support request submitted successfully"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error handling support request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit support request"
        )
