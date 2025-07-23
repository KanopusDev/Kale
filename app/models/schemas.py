from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v.lower()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    is_verified: bool
    is_admin: bool
    api_key: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class SMTPConfigBase(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    use_tls: bool = True
    from_email: EmailStr
    from_name: Optional[str] = None

class SMTPConfigCreate(SMTPConfigBase):
    pass

class SMTPConfig(SMTPConfigBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmailTemplateBase(BaseModel):
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: Optional[List[str]] = []
    category: Optional[str] = None
    description: Optional[str] = None

class EmailTemplateCreate(EmailTemplateBase):
    template_id: str
    
    @validator('template_id')
    def validate_template_id(cls, v):
        if len(v) < 3 or len(v) > 100:
            raise ValueError('Template ID must be between 3 and 100 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Template ID must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

class EmailTemplate(EmailTemplateBase):
    id: int
    user_id: Optional[int]
    template_id: str
    is_public: bool
    is_system_template: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EmailSendRequest(BaseModel):
    recipients: List[EmailStr]
    variables: Optional[Dict[str, Any]] = {}
    
    @validator('recipients')
    def validate_recipients(cls, v):
        if not v:
            raise ValueError('At least one recipient is required')
        if len(v) > 100:
            raise ValueError('Maximum 100 recipients allowed per request')
        return v

class EmailLog(BaseModel):
    id: int
    user_id: int
    template_id: str
    recipient_email: str
    subject: str
    status: str
    error_message: Optional[str]
    sent_at: datetime
    
    class Config:
        from_attributes = True

class APIUsageLog(BaseModel):
    id: int
    user_id: int
    endpoint: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_data: Optional[str]
    response_status: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional['User'] = None

class DashboardStats(BaseModel):
    total_emails_sent: int
    emails_sent_today: int
    total_templates: int
    active_smtp_configs: int
    daily_limit: int
    remaining_today: int

class AdminStats(BaseModel):
    total_users: int
    verified_users: int
    total_emails_sent: int
    emails_sent_today: int
    total_templates: int
    system_templates: int
    active_users_today: int
