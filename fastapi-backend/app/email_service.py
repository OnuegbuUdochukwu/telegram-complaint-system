"""Email service for sending invitation and OTP emails."""

import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import dotenv_values
from pathlib import Path
import os

logger = logging.getLogger("app.email_service")

# Load email configuration from .env
_env_path = Path(__file__).resolve().parents[2] / ".env"
config = dotenv_values(str(_env_path))

# SMTP Configuration (with defaults for development)
SMTP_HOST = os.environ.get("SMTP_HOST") or config.get("SMTP_HOST") or "localhost"
SMTP_PORT = int(os.environ.get("SMTP_PORT") or config.get("SMTP_PORT") or "587")
SMTP_USER = os.environ.get("SMTP_USER") or config.get("SMTP_USER") or ""
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD") or config.get("SMTP_PASSWORD") or ""
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
EMAIL_FROM = (
    os.environ.get("EMAIL_FROM")
    or config.get("EMAIL_FROM")
    or "noreply@complaint-system.local"
)
FRONTEND_URL = (
    os.environ.get("FRONTEND_URL")
    or config.get("FRONTEND_URL")
    or "http://localhost:8001"
)


async def send_email(
    to_email: str, subject: str, html_body: str, text_body: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body (optional, will be generated from HTML if not provided)

    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_FROM
        message["To"] = to_email

        # Create plain text version if not provided
        if not text_body:
            # Simple HTML to text conversion (remove tags)
            import re

            text_body = re.sub(r"<[^>]+>", "", html_body)
            text_body = text_body.replace("&nbsp;", " ").replace("&amp;", "&")

        # Add both plain text and HTML versions
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)

        # Send email
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER if SMTP_USER else None,
            password=SMTP_PASSWORD if SMTP_PASSWORD else None,
            use_tls=SMTP_USE_TLS,
        )

        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        # In development, log the email content instead of failing
        if SMTP_HOST == "localhost":
            logger.info(f"[DEV MODE] Would send email to {to_email}:")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {text_body}")
        return False


async def send_invitation_email(
    email: str, invitation_token: str, invited_by_name: str
) -> bool:
    """
    Send admin invitation email with signup link.

    Args:
        email: Recipient email address
        invitation_token: Secure invitation token
        invited_by_name: Name of the admin who sent the invitation

    Returns:
        True if email was sent successfully
    """
    signup_url = f"{FRONTEND_URL}/dashboard/signup.html?token={invitation_token}"

    subject = "Admin Invitation - Complaint Management System"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #6b7280; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Admin Invitation</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>You have been invited by <strong>{invited_by_name}</strong> to become an administrator of the Complaint Management System.</p>
                <p>Click the button below to complete your registration:</p>
                <p style="text-align: center;">
                    <a href="{signup_url}" class="button">Accept Invitation & Sign Up</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #2563eb;">{signup_url}</p>
                <p><strong>This invitation will expire in 48 hours.</strong></p>
                <p>If you did not expect this invitation, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>Complaint Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Admin Invitation - Complaint Management System

    Hello,

    You have been invited by {invited_by_name} to become an administrator of the Complaint Management System.

    Complete your registration by visiting:
    {signup_url}

    This invitation will expire in 48 hours.

    If you did not expect this invitation, please ignore this email.

    Complaint Management System
    """

    return await send_email(email, subject, html_body, text_body)


async def send_otp_email(
    email: str, otp_code: str, purpose: str = "verification"
) -> bool:
    """
    Send OTP verification code email.

    Args:
        email: Recipient email address
        otp_code: 6-digit OTP code
        purpose: Purpose of OTP ('signup' or 'password_reset')

    Returns:
        True if email was sent successfully
    """
    if purpose == "password_reset":
        subject = "Password Reset Code - Complaint Management System"
        action = "reset your password"
    else:
        subject = "Verification Code - Complaint Management System"
        action = "verify your email address"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
            .otp-code {{ font-size: 32px; font-weight: bold; text-align: center; letter-spacing: 8px; color: #2563eb; padding: 20px; background-color: white; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #6b7280; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Verification Code</h1>
            </div>
            <div class="content">
                <p>Hello,</p>
                <p>Use the code below to {action}:</p>
                <div class="otp-code">{otp_code}</div>
                <p><strong>This code will expire in 10 minutes.</strong></p>
                <p>If you did not request this code, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>Complaint Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Verification Code - Complaint Management System

    Hello,

    Use the code below to {action}:

    {otp_code}

    This code will expire in 10 minutes.

    If you did not request this code, please ignore this email.

    Complaint Management System
    """

    return await send_email(email, subject, html_body, text_body)
