"""
Email service for user verification and password reset
"""
import secrets
import string
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Template

from app.core.config import settings
from app.models.user import User
from app.core.security import get_password_hash

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Email templates
EMAIL_VERIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Email Verification - {{ app_name }}</title>
</head>
<body>
    <h2>Welcome to {{ app_name }}!</h2>
    <p>Hello {{ user_name }},</p>
    <p>Thank you for registering with {{ app_name }}. Please click the link below to verify your email address:</p>
    <p><a href="{{ verification_url }}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
    <p>If you didn't create an account, please ignore this email.</p>
    <p>This link will expire in 24 hours.</p>
    <p>Best regards,<br>{{ app_name }} Team</p>
</body>
</html>
"""

PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Password Reset - {{ app_name }}</title>
</head>
<body>
    <h2>Password Reset Request</h2>
    <p>Hello {{ user_name }},</p>
    <p>You requested a password reset for your {{ app_name }} account. Click the link below to reset your password:</p>
    <p><a href="{{ reset_url }}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
    <p>If you didn't request this reset, please ignore this email.</p>
    <p>This link will expire in 1 hour.</p>
    <p>Best regards,<br>{{ app_name }} Team</p>
</body>
</html>
"""

class EmailService:
    """Service for email operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fastmail = FastMail(conf)
    
    def generate_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def send_verification_email(self, user: User) -> bool:
        """Send email verification to user"""
        try:
            # Generate verification token
            verification_token = self.generate_token()
            
            # Store token in user record (you might want a separate table for tokens)
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    verification_token=verification_token,
                    verification_token_expires=datetime.utcnow() + timedelta(hours=24)
                )
            )
            await self.db.commit()
            
            # Create verification URL
            verification_url = f"https://your-domain.com/verify-email?token={verification_token}"
            
            # Render email template
            template = Template(EMAIL_VERIFICATION_TEMPLATE)
            html_content = template.render(
                app_name=settings.APP_NAME,
                user_name=user.full_name or user.email,
                verification_url=verification_url
            )
            
            # Send email
            message = MessageSchema(
                subject=f"Email Verification - {settings.APP_NAME}",
                recipients=[user.email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            return True
            
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False
    
    async def verify_email(self, token: str) -> bool:
        """Verify user email with token"""
        try:
            # Find user with token
            result = await self.db.execute(
                select(User).where(
                    User.verification_token == token,
                    User.verification_token_expires > datetime.utcnow()
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Mark email as verified
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    is_verified=True,
                    verification_token=None,
                    verification_token_expires=None
                )
            )
            await self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Failed to verify email: {e}")
            return False
    
    async def send_password_reset_email(self, email: str) -> bool:
        """Send password reset email"""
        try:
            # Find user by email
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists
                return True
            
            # Generate reset token
            reset_token = self.generate_token()
            
            # Store token in user record
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    reset_token=reset_token,
                    reset_token_expires=datetime.utcnow() + timedelta(hours=1)
                )
            )
            await self.db.commit()
            
            # Create reset URL
            reset_url = f"https://your-domain.com/reset-password?token={reset_token}"
            
            # Render email template
            template = Template(PASSWORD_RESET_TEMPLATE)
            html_content = template.render(
                app_name=settings.APP_NAME,
                user_name=user.full_name or user.email,
                reset_url=reset_url
            )
            
            # Send email
            message = MessageSchema(
                subject=f"Password Reset - {settings.APP_NAME}",
                recipients=[user.email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            return True
            
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password with token"""
        try:
            # Find user with token
            result = await self.db.execute(
                select(User).where(
                    User.reset_token == token,
                    User.reset_token_expires > datetime.utcnow()
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Update password and clear token
            await self.db.execute(
                update(User)
                .where(User.id == user.id)
                .values(
                    hashed_password=get_password_hash(new_password),
                    reset_token=None,
                    reset_token_expires=None
                )
            )
            await self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Failed to reset password: {e}")
            return False
    
    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to new user"""
        try:
            welcome_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Welcome to {{ app_name }}</title>
            </head>
            <body>
                <h2>Welcome to {{ app_name }}!</h2>
                <p>Hello {{ user_name }},</p>
                <p>Your account has been successfully created. You can now start using our Odoo SaaS platform.</p>
                <p><a href="https://your-domain.com/dashboard" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a></p>
                <p>If you have any questions, feel free to contact our support team.</p>
                <p>Best regards,<br>{{ app_name }} Team</p>
            </body>
            </html>
            """
            
            template = Template(welcome_template)
            html_content = template.render(
                app_name=settings.APP_NAME,
                user_name=user.full_name or user.email
            )
            
            message = MessageSchema(
                subject=f"Welcome to {settings.APP_NAME}",
                recipients=[user.email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            return True
            
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            return False
    
    async def send_instance_ready_email(self, user: User, instance_name: str, instance_url: str) -> bool:
        """Send notification when Odoo instance is ready"""
        try:
            instance_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Your Odoo Instance is Ready - {{ app_name }}</title>
            </head>
            <body>
                <h2>Your Odoo Instance is Ready!</h2>
                <p>Hello {{ user_name }},</p>
                <p>Your Odoo instance "{{ instance_name }}" has been successfully created and is now ready to use.</p>
                <p><strong>Instance URL:</strong> <a href="{{ instance_url }}">{{ instance_url }}</a></p>
                <p>You can now access your Odoo instance and start configuring your business applications.</p>
                <p>Best regards,<br>{{ app_name }} Team</p>
            </body>
            </html>
            """
            
            template = Template(instance_template)
            html_content = template.render(
                app_name=settings.APP_NAME,
                user_name=user.full_name or user.email,
                instance_name=instance_name,
                instance_url=instance_url
            )
            
            message = MessageSchema(
                subject=f"Your Odoo Instance is Ready - {settings.APP_NAME}",
                recipients=[user.email],
                body=html_content,
                subtype="html"
            )
            
            await self.fastmail.send_message(message)
            return True
            
        except Exception as e:
            print(f"Failed to send instance ready email: {e}")
            return False

