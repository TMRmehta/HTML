import os
from typing import Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Template

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

FRONTEND_URL = os.getenv("FRONTEND_URL")

class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)
    
    async def send_verification_email(self, email: str, verification_token: str, user_name: str) -> bool:
        """Send email verification email to user."""
        try:
            # Create verification URL
            verification_url = f"{FRONTEND_URL}/#/verify-email?token={verification_token}"
            
            # Email template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Email Verification - OncoSight AI</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to OncoSight AI</h1>
                        <p>AI-Powered Medical Platform</p>
                    </div>
                    <div class="content">
                        <h2>Hello {{ user_name }}!</h2>
                        <p>Thank you for signing up for OncoSight AI. To complete your registration and start using our platform, please verify your email address by clicking the button below:</p>
                        
                        <div style="text-align: center;">
                            <a href="{{ verification_url }}" class="button">Verify Email Address</a>
                        </div>
                        
                        <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background: #e9e9e9; padding: 10px; border-radius: 5px;">{{ verification_url }}</p>
                        
                        <p><strong>Important:</strong> This verification link will expire in 24 hours for security reasons.</p>
                        
                        <p>If you didn't create an account with OncoSight AI, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 OncoSight AI. All rights reserved.</p>
                        <p>This email was sent to {{ email }}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Render template
            template = Template(html_template)
            html_content = template.render(
                user_name=user_name,
                verification_url=verification_url,
                email=email
            )
            
            # Create message
            message = MessageSchema(
                subject="Verify Your Email - OncoSight AI",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            # Send email
            await self.fastmail.send_message(message)
            return True
            
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False
    
    async def send_welcome_email(self, email: str, user_name: str, user_type: str) -> bool:
        """Send welcome email after successful verification."""
        try:
            # Email template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to OncoSight AI</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                    .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to OncoSight AI!</h1>
                        <p>Your account has been verified successfully</p>
                    </div>
                    <div class="content">
                        <h2>Hello {{ user_name }}!</h2>
                        <p>Congratulations! Your email has been verified and your {{ user_type }} account is now active.</p>
                        
                        <p>You can now access all the features of OncoSight AI:</p>
                        <ul>
                            <li>AI-powered health information and support</li>
                            <li>Access to medical research databases</li>
                            <li>Personalized recommendations</li>
                            <li>Secure and HIPAA-compliant platform</li>
                        </ul>
                        
                        <div style="text-align: center;">
                            <a href="{{ frontend_url }}" class="button">Get Started</a>
                        </div>
                        
                        <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 OncoSight AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Render template
            template = Template(html_template)
            html_content = template.render(
                user_name=user_name,
                user_type=user_type,
                frontend_url=FRONTEND_URL
            )
            
            # Create message
            message = MessageSchema(
                subject="Welcome to OncoSight AI - Account Verified!",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            # Send email
            await self.fastmail.send_message(message)
            return True
            
        except Exception as e:
            print(f"Error sending welcome email: {e}")
            return False
    
    async def send_password_reset_email(self, email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email to user."""
        try:
            # Create reset URL
            reset_url = f"{FRONTEND_URL}/#/reset-password?token={reset_token}"
            
            # Email template
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Password Reset - OncoSight AI</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                    .button { display: inline-block; background: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                        <p>OncoSight AI - AI-Powered Medical Platform</p>
                    </div>
                    <div class="content">
                        <h2>Hello {{ user_name }}!</h2>
                        <p>We received a request to reset your password for your OncoSight AI account.</p>
                        
                        <div style="text-align: center;">
                            <a href="{{ reset_url }}" class="button">Reset Password</a>
                        </div>
                        
                        <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; background: #e9e9e9; padding: 10px; border-radius: 5px;">{{ reset_url }}</p>
                        
                        <p><strong>Important:</strong> This reset link will expire in 1 hour for security reasons.</p>
                        
                        <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                    </div>
                    <div class="footer">
                        <p>© 2024 OncoSight AI. All rights reserved.</p>
                        <p>This email was sent to {{ email }}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Render template
            template = Template(html_template)
            html_content = template.render(
                user_name=user_name,
                reset_url=reset_url,
                email=email
            )
            
            # Create message
            message = MessageSchema(
                subject="Password Reset Request - OncoSight AI",
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            
            # Send email
            await self.fastmail.send_message(message)
            return True
            
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return False

# Global email service instance
email_service = EmailService()
