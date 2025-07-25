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