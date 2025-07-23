from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.deps import get_current_user
from typing import Optional

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/docs", response_class=HTMLResponse)
async def api_documentation(request: Request, user = Depends(get_current_user)):
    """
    API Documentation page - shows comprehensive API usage guide for authenticated users
    """
    return templates.TemplateResponse("docs.html", {
        "request": request,
        "user": user,
        "title": "API Documentation - Kale"
    })
