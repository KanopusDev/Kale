from typing import Optional, List, Dict, Any
from app.core.database import db_manager
from app.models.schemas import EmailTemplate, EmailTemplateCreate
from app.services.email import EmailService
import logging
import json

logger = logging.getLogger(__name__)

class TemplateService:
    @staticmethod
    def create_template(user_id: int, template_data: EmailTemplateCreate) -> Optional[EmailTemplate]:
        """Create email template"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if template_id already exists for this user
                cursor.execute(
                    "SELECT id FROM email_templates WHERE template_id = ? AND user_id = ?",
                    (template_data.template_id, user_id)
                )
                if cursor.fetchone():
                    return None
                
                # Extract variables from content
                variables = EmailService.extract_variables(template_data.html_content)
                if template_data.text_content:
                    variables.extend(EmailService.extract_variables(template_data.text_content))
                variables.extend(EmailService.extract_variables(template_data.subject))
                variables = list(set(variables))
                
                # Insert template
                cursor.execute("""
                    INSERT INTO email_templates 
                    (user_id, template_id, name, subject, html_content, text_content, 
                     variables, category, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, template_data.template_id, template_data.name,
                    template_data.subject, template_data.html_content, template_data.text_content,
                    json.dumps(variables), template_data.category, template_data.description
                ))
                
                template_id = cursor.lastrowid
                conn.commit()
                
                # Fetch created template
                cursor.execute("SELECT * FROM email_templates WHERE id = ?", (template_id,))
                template_row = cursor.fetchone()
                
                return EmailTemplate(
                    id=template_row['id'],
                    user_id=template_row['user_id'],
                    template_id=template_row['template_id'],
                    name=template_row['name'],
                    subject=template_row['subject'],
                    html_content=template_row['html_content'],
                    text_content=template_row['text_content'],
                    variables=json.loads(template_row['variables']) if template_row['variables'] else [],
                    is_public=bool(template_row['is_public']),
                    is_system_template=bool(template_row['is_system_template']),
                    category=template_row['category'],
                    description=template_row['description'],
                    created_at=template_row['created_at'],
                    updated_at=template_row['updated_at']
                )
                
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return None
    
    @staticmethod
    def get_user_templates(user_id: int, limit: int = 100, offset: int = 0) -> List[EmailTemplate]:
        """Get templates for user"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM email_templates 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                template_rows = cursor.fetchall()
                
                return [
                    EmailTemplate(
                        id=row['id'],
                        user_id=row['user_id'],
                        template_id=row['template_id'],
                        name=row['name'],
                        subject=row['subject'],
                        html_content=row['html_content'],
                        text_content=row['text_content'],
                        variables=json.loads(row['variables']) if row['variables'] else [],
                        is_public=bool(row['is_public']),
                        is_system_template=bool(row['is_system_template']),
                        category=row['category'],
                        description=row['description'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in template_rows
                ]
            
        except Exception as e:
            logger.error(f"Error getting user templates: {e}")
            return []
    
    @staticmethod
    def get_template_by_id(user_id: int, template_id: str) -> Optional[EmailTemplate]:
        """Get template by template_id for user"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM email_templates 
                    WHERE template_id = ? AND (user_id = ? OR is_public = ? OR is_system_template = ?)
                """, (template_id, user_id, True, True))
                
                template_row = cursor.fetchone()
                
                if not template_row:
                    return None
                
                return EmailTemplate(
                    id=template_row['id'],
                    user_id=template_row['user_id'],
                    template_id=template_row['template_id'],
                    name=template_row['name'],
                    subject=template_row['subject'],
                    html_content=template_row['html_content'],
                    text_content=template_row['text_content'],
                    variables=json.loads(template_row['variables']) if template_row['variables'] else [],
                    is_public=bool(template_row['is_public']),
                    is_system_template=bool(template_row['is_system_template']),
                    category=template_row['category'],
                    description=template_row['description'],
                    created_at=template_row['created_at'],
                    updated_at=template_row['updated_at']
                )
                
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return None
    
    @staticmethod
    def get_public_templates(limit: int = 100, offset: int = 0, category: Optional[str] = None) -> List[EmailTemplate]:
        """Get public and system templates"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM email_templates 
                    WHERE (is_public = ? OR is_system_template = ?)
                """
                params = [True, True]
                
                if category:
                    query += " AND category = ?"
                    params.append(category)
                
                query += " ORDER BY is_system_template DESC, created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                template_rows = cursor.fetchall()
                
                return [
                    EmailTemplate(
                        id=row['id'],
                        user_id=row['user_id'],
                        template_id=row['template_id'],
                        name=row['name'],
                        subject=row['subject'],
                        html_content=row['html_content'],
                        text_content=row['text_content'],
                        variables=json.loads(row['variables']) if row['variables'] else [],
                        is_public=bool(row['is_public']),
                        is_system_template=bool(row['is_system_template']),
                        category=row['category'],
                        description=row['description'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in template_rows
                ]
                
        except Exception as e:
            logger.error(f"Error getting public templates: {e}")
            return []
    
    @staticmethod
    def update_template(user_id: int, template_id: str, template_data: EmailTemplateCreate) -> bool:
        """Update template"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if template exists and belongs to user
                cursor.execute(
                    "SELECT id FROM email_templates WHERE template_id = ? AND user_id = ?",
                    (template_id, user_id)
                )
                if not cursor.fetchone():
                    return False
                
                # Extract variables
                variables = EmailService.extract_variables(template_data.html_content)
                if template_data.text_content:
                    variables.extend(EmailService.extract_variables(template_data.text_content))
                variables.extend(EmailService.extract_variables(template_data.subject))
                variables = list(set(variables))
                
                # Update template
                cursor.execute("""
                    UPDATE email_templates 
                    SET name = ?, subject = ?, html_content = ?, text_content = ?, 
                        variables = ?, category = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE template_id = ? AND user_id = ?
                """, (
                    template_data.name, template_data.subject, template_data.html_content,
                    template_data.text_content, json.dumps(variables), template_data.category,
                    template_data.description, template_id, user_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return False
    
    @staticmethod
    def delete_template(user_id: int, template_id: str) -> bool:
        """Delete template"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM email_templates WHERE template_id = ? AND user_id = ?",
                    (template_id, user_id)
                )
                
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
                
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
    
    @staticmethod
    def get_template_categories() -> List[str]:
        """Get all template categories"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT DISTINCT category FROM email_templates 
                    WHERE category IS NOT NULL AND category != ''
                    ORDER BY category
                """)
                
                categories = [row['category'] for row in cursor.fetchall()]
                return categories
                
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    @staticmethod
    def create_system_templates():
        """Create default system templates"""
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if system templates already exist
                cursor.execute("SELECT COUNT(*) as count FROM email_templates WHERE is_system_template = ?", (True,))
                if cursor.fetchone()['count'] > 0:
                    return
            
            system_templates = [
                {
                    'template_id': 'welcome-email',
                    'name': 'Welcome Email',
                    'subject': 'Welcome to {{company_name}}!',
                    'html_content': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h1 style="color: #2c3e50;">Welcome to {{company_name}}!</h1>
                            <p>Hi {{first_name}},</p>
                            <p>Thank you for joining {{company_name}}. We're excited to have you on board!</p>
                            <p>Here are your next steps:</p>
                            <ul>
                                <li>Complete your profile</li>
                                <li>Explore our features</li>
                                <li>Contact support if you need help</li>
                            </ul>
                            <p>Best regards,<br>The {{company_name}} Team</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'text_content': '''Welcome to {{company_name}}!

Hi {{first_name}},

Thank you for joining {{company_name}}. We're excited to have you on board!

Here are your next steps:
- Complete your profile
- Explore our features
- Contact support if you need help

Best regards,
The {{company_name}} Team''',
                    'category': 'Onboarding',
                    'description': 'Welcome email for new users'
                },
                {
                    'template_id': 'password-reset',
                    'name': 'Password Reset',
                    'subject': 'Reset Your Password - {{company_name}}',
                    'html_content': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h1 style="color: #e74c3c;">Password Reset Request</h1>
                            <p>Hi {{first_name}},</p>
                            <p>You requested to reset your password for your {{company_name}} account.</p>
                            <p style="margin: 30px 0;">
                                <a href="{{reset_link}}" style="background-color: #3498db; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a>
                            </p>
                            <p>This link will expire in 24 hours. If you didn't request this, please ignore this email.</p>
                            <p>Best regards,<br>The {{company_name}} Team</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'text_content': '''Password Reset Request

Hi {{first_name}},

You requested to reset your password for your {{company_name}} account.

Reset your password: {{reset_link}}

This link will expire in 24 hours. If you didn't request this, please ignore this email.

Best regards,
The {{company_name}} Team''',
                    'category': 'Authentication',
                    'description': 'Password reset email template'
                },
                {
                    'template_id': 'invoice-notification',
                    'name': 'Invoice Notification',
                    'subject': 'Invoice #{{invoice_number}} from {{company_name}}',
                    'html_content': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h1 style="color: #27ae60;">Invoice #{{invoice_number}}</h1>
                            <p>Hi {{customer_name}},</p>
                            <p>Thank you for your business! Your invoice is ready.</p>
                            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                                <p><strong>Invoice Number:</strong> {{invoice_number}}</p>
                                <p><strong>Amount:</strong> {{amount}}</p>
                                <p><strong>Due Date:</strong> {{due_date}}</p>
                            </div>
                            <p style="margin: 30px 0;">
                                <a href="{{invoice_link}}" style="background-color: #27ae60; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block;">View Invoice</a>
                            </p>
                            <p>Best regards,<br>The {{company_name}} Team</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'text_content': '''Invoice #{{invoice_number}}

Hi {{customer_name}},

Thank you for your business! Your invoice is ready.

Invoice Number: {{invoice_number}}
Amount: {{amount}}
Due Date: {{due_date}}

View your invoice: {{invoice_link}}

Best regards,
The {{company_name}} Team''',
                    'category': 'Business',
                    'description': 'Invoice notification email template'
                }
            ]
            
            for template in system_templates:
                variables = EmailService.extract_variables(template['html_content'])
                variables.extend(EmailService.extract_variables(template['text_content']))
                variables.extend(EmailService.extract_variables(template['subject']))
                variables = list(set(variables))
                
                cursor.execute("""
                    INSERT INTO email_templates 
                    (template_id, name, subject, html_content, text_content, 
                     variables, category, description, is_system_template)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template['template_id'], template['name'], template['subject'],
                    template['html_content'], template['text_content'],
                    json.dumps(variables), template['category'], 
                    template['description'], True
                ))
            
            conn.commit()
            logger.info("System templates created successfully")
            
        except Exception as e:
            logger.error(f"Error creating system templates: {e}")

template = TemplateService()
