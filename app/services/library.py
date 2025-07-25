"""
Kale Template Management System - Enterprise Implementation
Production-ready template management with variable handling
"""

from typing import Dict, List, Optional, Any
import json
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TemplateVariable:
    """Template variable definition"""
    name: str
    type: str  # text, number, email, url, date, boolean
    label: str
    description: str
    required: bool = True
    default_value: Optional[str] = None
    validation_pattern: Optional[str] = None


@dataclass
class EmailTemplate:
    """Email template with metadata and content"""
    id: str
    name: str
    category: str
    subject: str
    html_content: str
    text_content: str
    variables: List[TemplateVariable]
    is_system: bool = False
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: List[str] = None
    preview_data: Dict[str, Any] = None


class TemplateLibrary:
    """Enterprise template library with pre-built templates"""
    
    @staticmethod
    def get_system_templates() -> List[EmailTemplate]:
        """Get all system templates"""
        return [
            # Welcome Email Template
            EmailTemplate(
                id="welcome_user",
                name="Welcome Email",
                category="Onboarding",
                subject="Welcome to {{company_name}}, {{user_name}}!",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Welcome</title>
                    <style>
                        body { font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }
                        .container { max-width: 600px; margin: 0 auto; background: white; }
                        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; }
                        .logo { color: white; font-size: 32px; font-weight: bold; margin-bottom: 10px; }
                        .tagline { color: rgba(255,255,255,0.9); font-size: 16px; }
                        .content { padding: 40px 30px; }
                        .greeting { font-size: 24px; font-weight: 600; color: #1f2937; margin-bottom: 20px; }
                        .message { font-size: 16px; line-height: 1.6; color: #4b5563; margin-bottom: 30px; }
                        .cta-button { display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; }
                        .footer { background: #f8fafc; padding: 30px; text-align: center; font-size: 14px; color: #6b7280; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="logo">🌱 {{company_name}}</div>
                            <div class="tagline">Enterprise Email Platform</div>
                        </div>
                        <div class="content">
                            <h1 class="greeting">Welcome, {{user_name}}!</h1>
                            <p class="message">
                                Thank you for joining {{company_name}}. We're excited to help you streamline your email communications with our powerful API platform.
                            </p>
                            <p class="message">
                                Your account is now active and ready to use. You can start sending emails immediately through our API or explore our template library.
                            </p>
                            <p style="text-align: center; margin: 40px 0;">
                                <a href="{{dashboard_url}}" class="cta-button">Access Your Dashboard</a>
                            </p>
                            <p class="message">
                                If you have any questions, our support team is here to help at {{support_email}}.
                            </p>
                        </div>
                        <div class="footer">
                            <p>This email was sent by {{company_name}}</p>
                            <p>{{company_address}}</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_content="""
                Welcome to {{company_name}}, {{user_name}}!
                
                Thank you for joining {{company_name}}. We're excited to help you streamline your email communications with our powerful API platform.
                
                Your account is now active and ready to use. You can start sending emails immediately through our API or explore our template library.
                
                Access your dashboard: {{dashboard_url}}
                
                If you have any questions, our support team is here to help at {{support_email}}.
                
                Best regards,
                The {{company_name}} Team
                """,
                variables=[
                    TemplateVariable("company_name", "text", "Company Name", "Your company or organization name"),
                    TemplateVariable("user_name", "text", "User Name", "Recipient's name"),
                    TemplateVariable("dashboard_url", "url", "Dashboard URL", "Link to user dashboard"),
                    TemplateVariable("support_email", "email", "Support Email", "Support contact email"),
                    TemplateVariable("company_address", "text", "Company Address", "Your company address", required=False)
                ],
                is_system=True,
                tags=["welcome", "onboarding", "user"],
                preview_data={
                    "company_name": "Acme Corp",
                    "user_name": "John Doe",
                    "dashboard_url": "https://kale.kanopus.org/dashboard",
                    "support_email": "support@acme.com",
                    "company_address": "123 Business St, City, State 12345"
                }
            ),
            
            # Password Reset Template
            EmailTemplate(
                id="password_reset",
                name="Password Reset",
                category="Security",
                subject="Reset your {{service_name}} password",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Password Reset</title>
                    <style>
                        body { font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }
                        .container { max-width: 600px; margin: 0 auto; background: white; }
                        .header { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 40px 20px; text-align: center; }
                        .icon { color: white; font-size: 48px; margin-bottom: 10px; }
                        .title { color: white; font-size: 24px; font-weight: bold; }
                        .content { padding: 40px 30px; }
                        .alert { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin-bottom: 30px; }
                        .alert-text { color: #b91c1c; font-size: 14px; font-weight: 500; }
                        .message { font-size: 16px; line-height: 1.6; color: #4b5563; margin-bottom: 30px; }
                        .reset-button { display: inline-block; background: #ef4444; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }
                        .expire-notice { background: #f3f4f6; padding: 15px; border-radius: 6px; font-size: 14px; color: #6b7280; }
                        .footer { background: #f8fafc; padding: 30px; text-align: center; font-size: 14px; color: #6b7280; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="icon">🔒</div>
                            <div class="title">Password Reset Request</div>
                        </div>
                        <div class="content">
                            <div class="alert">
                                <div class="alert-text">🛡️ Security Notice: Password reset requested</div>
                            </div>
                            <p class="message">
                                Hi {{user_name}},
                            </p>
                            <p class="message">
                                We received a request to reset your password for your {{service_name}} account. If you requested this change, click the button below to set a new password:
                            </p>
                            <p style="text-align: center;">
                                <a href="{{reset_url}}" class="reset-button">Reset Password</a>
                            </p>
                            <div class="expire-notice">
                                ⏰ This link will expire in {{expiry_hours}} hours for security purposes.
                            </div>
                            <p class="message">
                                If you didn't request this password reset, please ignore this email. Your account remains secure.
                            </p>
                            <p class="message">
                                For security questions, contact us at {{security_email}}.
                            </p>
                        </div>
                        <div class="footer">
                            <p>This is an automated security email from {{service_name}}</p>
                            <p>Please do not reply to this email</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_content="""
                Password Reset Request
                
                Hi {{user_name}},
                
                We received a request to reset your password for your {{service_name}} account.
                
                Reset your password: {{reset_url}}
                
                This link will expire in {{expiry_hours}} hours for security purposes.
                
                If you didn't request this password reset, please ignore this email. Your account remains secure.
                
                For security questions, contact us at {{security_email}}.
                
                {{service_name}} Security Team
                """,
                variables=[
                    TemplateVariable("user_name", "text", "User Name", "Recipient's name"),
                    TemplateVariable("service_name", "text", "Service Name", "Your service or platform name"),
                    TemplateVariable("reset_url", "url", "Reset URL", "Password reset link"),
                    TemplateVariable("expiry_hours", "number", "Expiry Hours", "Hours until link expires", default_value="24"),
                    TemplateVariable("security_email", "email", "Security Email", "Security team contact email")
                ],
                is_system=True,
                tags=["security", "password", "reset"],
                preview_data={
                    "user_name": "Jane Smith",
                    "service_name": "Kale Platform",
                    "reset_url": "https://kale.kanopus.org/reset-password?token=abc123",
                    "expiry_hours": "24",
                    "security_email": "security@kale.kanopus.org"
                }
            ),
            
            # Invoice Template
            EmailTemplate(
                id="invoice_notification",
                name="Invoice Notification",
                category="Billing",
                subject="Invoice #{{invoice_number}} from {{company_name}}",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Invoice</title>
                    <style>
                        body { font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }
                        .container { max-width: 600px; margin: 0 auto; background: white; }
                        .header { background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 40px 20px; text-align: center; }
                        .invoice-icon { color: white; font-size: 48px; margin-bottom: 10px; }
                        .title { color: white; font-size: 24px; font-weight: bold; }
                        .content { padding: 40px 30px; }
                        .invoice-details { background: #f9fafb; border-radius: 8px; padding: 25px; margin: 30px 0; }
                        .detail-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
                        .detail-label { font-weight: 600; color: #374151; }
                        .detail-value { color: #6b7280; }
                        .amount { font-size: 32px; font-weight: bold; color: #059669; text-align: center; margin: 30px 0; }
                        .pay-button { display: inline-block; background: #059669; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; }
                        .footer { background: #f8fafc; padding: 30px; text-align: center; font-size: 14px; color: #6b7280; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="invoice-icon">📄</div>
                            <div class="title">Invoice Ready</div>
                        </div>
                        <div class="content">
                            <p style="font-size: 18px; color: #1f2937; margin-bottom: 20px;">
                                Hi {{customer_name}},
                            </p>
                            <p style="font-size: 16px; color: #4b5563; margin-bottom: 30px;">
                                Your invoice for {{service_period}} is now available. Thank you for your continued business with {{company_name}}.
                            </p>
                            
                            <div class="invoice-details">
                                <div class="detail-row">
                                    <span class="detail-label">Invoice Number:</span>
                                    <span class="detail-value">#{{invoice_number}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Issue Date:</span>
                                    <span class="detail-value">{{issue_date}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Due Date:</span>
                                    <span class="detail-value">{{due_date}}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Service Period:</span>
                                    <span class="detail-value">{{service_period}}</span>
                                </div>
                            </div>
                            
                            <div class="amount">
                                ${{total_amount}}
                            </div>
                            
                            <p style="text-align: center; margin: 40px 0;">
                                <a href="{{payment_url}}" class="pay-button">Pay Invoice</a>
                            </p>
                            
                            <p style="font-size: 14px; color: #6b7280; text-align: center;">
                                You can also download your invoice as PDF from your billing dashboard.
                            </p>
                        </div>
                        <div class="footer">
                            <p>{{company_name}} | {{company_address}}</p>
                            <p>Questions? Contact us at {{billing_email}}</p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_content="""
                Invoice #{{invoice_number}} from {{company_name}}
                
                Hi {{customer_name}},
                
                Your invoice for {{service_period}} is now available.
                
                Invoice Details:
                - Invoice Number: #{{invoice_number}}
                - Issue Date: {{issue_date}}
                - Due Date: {{due_date}}
                - Service Period: {{service_period}}
                - Total Amount: ${{total_amount}}
                
                Pay your invoice: {{payment_url}}
                
                Thank you for your business!
                
                {{company_name}}
                Questions? Contact us at {{billing_email}}
                """,
                variables=[
                    TemplateVariable("customer_name", "text", "Customer Name", "Customer's name"),
                    TemplateVariable("company_name", "text", "Company Name", "Your company name"),
                    TemplateVariable("invoice_number", "text", "Invoice Number", "Unique invoice identifier"),
                    TemplateVariable("issue_date", "date", "Issue Date", "Invoice issue date"),
                    TemplateVariable("due_date", "date", "Due Date", "Payment due date"),
                    TemplateVariable("service_period", "text", "Service Period", "Billing period description"),
                    TemplateVariable("total_amount", "number", "Total Amount", "Invoice total amount"),
                    TemplateVariable("payment_url", "url", "Payment URL", "Link to payment page"),
                    TemplateVariable("company_address", "text", "Company Address", "Your company address", required=False),
                    TemplateVariable("billing_email", "email", "Billing Email", "Billing support email")
                ],
                is_system=True,
                tags=["billing", "invoice", "payment"],
                preview_data={
                    "customer_name": "Alex Johnson",
                    "company_name": "TechCorp Solutions",
                    "invoice_number": "INV-2025-001",
                    "issue_date": "January 23, 2025",
                    "due_date": "February 7, 2025",
                    "service_period": "January 2025",
                    "total_amount": "299.00",
                    "payment_url": "https://billing.techcorp.com/pay/INV-2025-001",
                    "company_address": "456 Innovation Drive, Tech City, TC 67890",
                    "billing_email": "billing@techcorp.com"
                }
            ),
            
            # Newsletter Template
            EmailTemplate(
                id="newsletter_template",
                name="Company Newsletter",
                category="Marketing",
                subject="{{newsletter_title}} - {{month}} {{year}}",
                html_content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Newsletter</title>
                    <style>
                        body { font-family: 'Inter', Arial, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }
                        .container { max-width: 600px; margin: 0 auto; background: white; }
                        .header { background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 40px 20px; text-align: center; }
                        .newsletter-icon { color: white; font-size: 48px; margin-bottom: 10px; }
                        .title { color: white; font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .subtitle { color: rgba(255,255,255,0.9); font-size: 16px; }
                        .content { padding: 40px 30px; }
                        .section-title { font-size: 20px; font-weight: 600; color: #1f2937; margin: 30px 0 15px 0; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
                        .article { margin-bottom: 30px; padding-bottom: 30px; border-bottom: 1px solid #e5e7eb; }
                        .article-title { font-size: 18px; font-weight: 600; color: #374151; margin-bottom: 10px; }
                        .article-content { font-size: 16px; line-height: 1.6; color: #4b5563; margin-bottom: 15px; }
                        .read-more { color: #8b5cf6; text-decoration: none; font-weight: 500; }
                        .cta-section { background: #f3f4f6; padding: 30px; text-align: center; border-radius: 8px; margin: 30px 0; }
                        .cta-button { display: inline-block; background: #8b5cf6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; }
                        .footer { background: #f8fafc; padding: 30px; text-align: center; font-size: 14px; color: #6b7280; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div class="newsletter-icon">📰</div>
                            <div class="title">{{newsletter_title}}</div>
                            <div class="subtitle">{{month}} {{year}} Edition</div>
                        </div>
                        <div class="content">
                            <p style="font-size: 18px; color: #1f2937; margin-bottom: 30px;">
                                Hello {{subscriber_name}},
                            </p>
                            <p style="font-size: 16px; color: #4b5563; margin-bottom: 30px;">
                                {{intro_message}}
                            </p>
                            
                            <div class="section-title">🚀 Featured Article</div>
                            <div class="article">
                                <div class="article-title">{{featured_article_title}}</div>
                                <div class="article-content">{{featured_article_excerpt}}</div>
                                <a href="{{featured_article_url}}" class="read-more">Read full article →</a>
                            </div>
                            
                            <div class="section-title">📈 Company Updates</div>
                            <div class="article-content">{{company_updates}}</div>
                            
                            <div class="section-title">🎯 Upcoming Events</div>
                            <div class="article-content">{{upcoming_events}}</div>
                            
                            <div class="cta-section">
                                <h3 style="margin-bottom: 15px; color: #1f2937;">{{cta_title}}</h3>
                                <p style="margin-bottom: 25px; color: #4b5563;">{{cta_description}}</p>
                                <a href="{{cta_url}}" class="cta-button">{{cta_button_text}}</a>
                            </div>
                        </div>
                        <div class="footer">
                            <p>{{company_name}} | {{company_website}}</p>
                            <p>You're receiving this because you subscribed to our newsletter.</p>
                            <p><a href="{{unsubscribe_url}}" style="color: #6b7280;">Unsubscribe</a> | <a href="{{manage_preferences_url}}" style="color: #6b7280;">Manage Preferences</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """,
                text_content="""
                {{newsletter_title}} - {{month}} {{year}}
                
                Hello {{subscriber_name}},
                
                {{intro_message}}
                
                FEATURED ARTICLE
                {{featured_article_title}}
                {{featured_article_excerpt}}
                Read more: {{featured_article_url}}
                
                COMPANY UPDATES
                {{company_updates}}
                
                UPCOMING EVENTS
                {{upcoming_events}}
                
                {{cta_title}}
                {{cta_description}}
                {{cta_button_text}}: {{cta_url}}
                
                {{company_name}} | {{company_website}}
                Unsubscribe: {{unsubscribe_url}}
                """,
                variables=[
                    TemplateVariable("newsletter_title", "text", "Newsletter Title", "Your newsletter name"),
                    TemplateVariable("month", "text", "Month", "Current month"),
                    TemplateVariable("year", "text", "Year", "Current year"),
                    TemplateVariable("subscriber_name", "text", "Subscriber Name", "Recipient's name"),
                    TemplateVariable("intro_message", "text", "Introduction Message", "Opening message for this edition"),
                    TemplateVariable("featured_article_title", "text", "Featured Article Title", "Main article headline"),
                    TemplateVariable("featured_article_excerpt", "text", "Featured Article Excerpt", "Brief summary of featured article"),
                    TemplateVariable("featured_article_url", "url", "Featured Article URL", "Link to full article"),
                    TemplateVariable("company_updates", "text", "Company Updates", "Latest company news"),
                    TemplateVariable("upcoming_events", "text", "Upcoming Events", "Event announcements"),
                    TemplateVariable("cta_title", "text", "CTA Title", "Call-to-action heading"),
                    TemplateVariable("cta_description", "text", "CTA Description", "Call-to-action description"),
                    TemplateVariable("cta_button_text", "text", "CTA Button Text", "Button text"),
                    TemplateVariable("cta_url", "url", "CTA URL", "Call-to-action link"),
                    TemplateVariable("company_name", "text", "Company Name", "Your company name"),
                    TemplateVariable("company_website", "url", "Company Website", "Your website URL"),
                    TemplateVariable("unsubscribe_url", "url", "Unsubscribe URL", "Unsubscribe link"),
                    TemplateVariable("manage_preferences_url", "url", "Manage Preferences URL", "Preference management link", required=False)
                ],
                is_system=True,
                tags=["newsletter", "marketing", "updates"],
                preview_data={
                    "newsletter_title": "Innovation Weekly",
                    "month": "January",
                    "year": "2025",
                    "subscriber_name": "Sarah Connor",
                    "intro_message": "Welcome to our latest edition packed with exciting updates and insights from the world of technology.",
                    "featured_article_title": "The Future of AI in Business Communication",
                    "featured_article_excerpt": "Discover how artificial intelligence is revolutionizing the way businesses communicate with their customers and streamline their operations.",
                    "featured_article_url": "https://blog.company.com/ai-business-communication",
                    "company_updates": "We're excited to announce our new API features, expanded template library, and enhanced security measures that make your email campaigns more effective than ever.",
                    "upcoming_events": "Join us for our virtual webinar series starting February 15th, covering advanced email automation techniques and best practices.",
                    "cta_title": "Ready to Boost Your Email Performance?",
                    "cta_description": "Upgrade to our Premium plan and unlock advanced analytics, unlimited templates, and priority support.",
                    "cta_button_text": "Upgrade Now",
                    "cta_url": "https://kale.kanopus.org/upgrade",
                    "company_name": "InnovateTech Solutions",
                    "company_website": "https://innovatetech.com",
                    "unsubscribe_url": "https://kale.kanopus.org/unsubscribe?token=abc123",
                    "manage_preferences_url": "https://kale.kanopus.org/preferences?token=abc123"
                }
            )
        ]


class TemplateProcessor:
    """Process templates with variable substitution"""
    
    @staticmethod
    def render_template(template: EmailTemplate, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render template with provided variables"""
        try:
            # Validate required variables
            missing_vars = []
            for var in template.variables:
                if var.required and var.name not in variables:
                    missing_vars.append(var.name)
            
            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
            
            # Merge with default values
            render_vars = {}
            for var in template.variables:
                if var.name in variables:
                    render_vars[var.name] = variables[var.name]
                elif var.default_value is not None:
                    render_vars[var.name] = var.default_value
            
            # Validate variable types and patterns
            for var in template.variables:
                if var.name in render_vars:
                    TemplateProcessor._validate_variable(var, render_vars[var.name])
            
            # Render subject, HTML, and text content
            subject = TemplateProcessor._substitute_variables(template.subject, render_vars)
            html_content = TemplateProcessor._substitute_variables(template.html_content, render_vars)
            text_content = TemplateProcessor._substitute_variables(template.text_content, render_vars)
            
            return {
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content
            }
            
        except Exception as e:
            raise ValueError(f"Template rendering failed: {str(e)}")
    
    @staticmethod
    def _substitute_variables(content: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in content using {{variable_name}} syntax"""
        def replace_var(match):
            var_name = match.group(1).strip()
            return str(variables.get(var_name, f"{{{{{var_name}}}}}"))
        
        # Use regex to find and replace {{variable_name}} patterns
        pattern = r'\{\{\s*([^}]+)\s*\}\}'
        return re.sub(pattern, replace_var, content)
    
    @staticmethod
    def _validate_variable(var: TemplateVariable, value: Any) -> None:
        """Validate variable value according to its type and pattern"""
        if var.validation_pattern:
            if not re.match(var.validation_pattern, str(value)):
                raise ValueError(f"Variable '{var.name}' does not match required pattern")
        
        if var.type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                raise ValueError(f"Variable '{var.name}' must be a valid email address")
        
        elif var.type == "url":
            url_pattern = r'^https?://.+'
            if not re.match(url_pattern, str(value)):
                raise ValueError(f"Variable '{var.name}' must be a valid URL")
        
        elif var.type == "number":
            try:
                float(value)
            except (ValueError, TypeError):
                raise ValueError(f"Variable '{var.name}' must be a number")


class TemplateManager:
    """Enterprise template management system"""
    
    def __init__(self):
        self.templates: Dict[str, EmailTemplate] = {}
        self.load_system_templates()
    
    def load_system_templates(self):
        """Load all system templates"""
        system_templates = TemplateLibrary.get_system_templates()
        for template in system_templates:
            self.templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None, user_id: Optional[str] = None) -> List[EmailTemplate]:
        """List templates with optional filtering"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category.lower() == category.lower()]
        
        if user_id:
            templates = [t for t in templates if t.is_system or t.created_by == user_id]
        
        return sorted(templates, key=lambda t: (not t.is_system, t.name))
    
    def create_custom_template(self, template_data: Dict[str, Any], user_id: str) -> EmailTemplate:
        """Create a custom user template"""
        # Process variables - handle both string array and dict array formats
        variables = []
        if "variables" in template_data and template_data["variables"]:
            # Handle variables that come as comma-separated string from frontend
            if isinstance(template_data["variables"], str):
                var_list = [v.strip() for v in template_data["variables"].split(",") if v.strip()]
            elif isinstance(template_data["variables"], list):
                var_list = template_data["variables"]
            else:
                var_list = []
            
            for var in var_list:
                if isinstance(var, str):
                    # Handle frontend format: array of strings or comma-separated string
                    variables.append(TemplateVariable(
                        name=var.strip(),
                        type="text",
                        label=var.strip().replace("_", " ").title(),
                        description=f"Variable: {var.strip()}",
                        required=True
                    ))
                elif isinstance(var, dict):
                    # Handle API format: array of dicts
                    variables.append(TemplateVariable(**var))
                else:
                    # Skip invalid variable formats
                    continue
        
        # Generate template ID
        if "template_id" in template_data and template_data["template_id"]:
            # Use provided template_id (sanitize it)
            template_id = template_data["template_id"].strip().lower().replace(" ", "_")
            # Ensure uniqueness
            if template_id in self.templates:
                template_id = f"{template_id}_{user_id}_{int(datetime.now().timestamp())}"
        else:
            # Auto-generate template ID
            template_id = f"custom_{user_id}_{len([t for t in self.templates.values() if t.created_by == user_id]) + 1}"
        
        template = EmailTemplate(
            id=template_id,
            name=template_data["name"],
            category=template_data["category"],
            subject=template_data["subject"],
            html_content=template_data["html_content"],
            text_content=template_data["text_content"],
            variables=variables,
            is_system=False,
            created_by=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=template_data.get("tags", [])
        )
        
        self.templates[template.id] = template
        return template
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render a template with variables"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        return TemplateProcessor.render_template(template, variables)
    
    def get_template_preview(self, template_id: str) -> Dict[str, str]:
        """Get template preview using default preview data"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        preview_data = template.preview_data or {}
        return TemplateProcessor.render_template(template, preview_data)


# Global template manager instance
template_manager = TemplateManager()
