"""OTP generation and verification utilities."""
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlmodel import select
from .models import OTPToken
from .database import get_session, Session
from . import auth

logger = logging.getLogger("app.otp_utils")

# OTP configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 3
OTP_RATE_LIMIT_WINDOW_HOURS = 1
OTP_RATE_LIMIT_MAX_REQUESTS = 3


def generate_otp_code() -> str:
    """Generate a secure random 6-digit OTP code."""
    # Generate random number between 100000 and 999999
    return str(secrets.randbelow(900000) + 100000)


async def create_otp_token(
    session: Session,
    email: str,
    purpose: str,
    expiry_minutes: int = OTP_EXPIRY_MINUTES
) -> Tuple[Optional[str], Optional[str]]:
    """
    Create an OTP token and return both plain code (for email) and token record.
    
    Args:
        session: Database session
        email: Email address
        purpose: 'signup' or 'password_reset'
        expiry_minutes: OTP expiration time in minutes
    
    Returns:
        Tuple of (plain_otp_code, error_message). Returns (None, error) if rate limited.
    """
    # Check rate limiting: max 3 OTP requests per email per hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=OTP_RATE_LIMIT_WINDOW_HOURS)
    
    recent_otps = session.exec(
        select(OTPToken).where(
            OTPToken.email == email,
            OTPToken.purpose == purpose,
            OTPToken.created_at >= one_hour_ago
        )
    ).all()
    
    # Count non-expired requests
    now = datetime.now(timezone.utc)
    active_requests = [otp for otp in recent_otps if otp.expires_at > now and not otp.used]
    
    if len(active_requests) >= OTP_RATE_LIMIT_MAX_REQUESTS:
        error_msg = f"Too many OTP requests. Please wait before requesting another code."
        logger.warning(f"Rate limit exceeded for {email} (purpose: {purpose})")
        return None, error_msg
    
    # Generate OTP code
    otp_code = generate_otp_code()
    
    # Hash the OTP code (like passwords)
    code_hash = auth.get_password_hash(otp_code)
    
    # Create expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    
    # Invalidate previous unused OTPs for this email/purpose
    existing_otps = session.exec(
        select(OTPToken).where(
            OTPToken.email == email,
            OTPToken.purpose == purpose,
            OTPToken.used == False,
            OTPToken.expires_at > now
        )
    ).all()
    
    for existing in existing_otps:
        existing.used = True
    
    # Create new OTP token
    otp_token = OTPToken(
        email=email,
        code_hash=code_hash,
        purpose=purpose,
        expires_at=expires_at,
        attempts=0,
        max_attempts=OTP_MAX_ATTEMPTS,
        used=False
    )
    
    session.add(otp_token)
    session.commit()
    session.refresh(otp_token)
    
    logger.info(f"Created OTP token for {email} (purpose: {purpose})")
    
    return otp_code, None


async def verify_otp_token(
    session: Session,
    email: str,
    otp_code: str,
    purpose: str
) -> Tuple[bool, Optional[str]]:
    """
    Verify an OTP code.
    
    Args:
        session: Database session
        email: Email address
        otp_code: User-provided OTP code
        purpose: 'signup' or 'password_reset'
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    now = datetime.now(timezone.utc)
    
    # Find valid OTP token
    otp_token = session.exec(
        select(OTPToken).where(
            OTPToken.email == email,
            OTPToken.purpose == purpose,
            OTPToken.used == False,
            OTPToken.expires_at > now
        ).order_by(OTPToken.created_at.desc())
    ).first()
    
    if not otp_token:
        error_msg = "Invalid or expired verification code. Please request a new code."
        logger.warning(f"OTP verification failed for {email}: No valid token found")
        return False, error_msg
    
    # Check if max attempts exceeded
    if otp_token.attempts >= otp_token.max_attempts:
        otp_token.used = True  # Mark as used to prevent further attempts
        session.add(otp_token)
        session.commit()
        error_msg = "Too many failed attempts. Please request a new verification code."
        logger.warning(f"OTP verification failed for {email}: Max attempts exceeded")
        return False, error_msg
    
    # Verify the code
    is_valid = auth.verify_password(otp_code, otp_token.code_hash)
    
    # Increment attempt counter
    otp_token.attempts += 1
    
    if is_valid:
        # Mark as used
        otp_token.used = True
        logger.info(f"OTP verification successful for {email} (purpose: {purpose})")
    else:
        logger.warning(f"OTP verification failed for {email}: Invalid code (attempt {otp_token.attempts}/{otp_token.max_attempts})")
    
    session.add(otp_token)
    session.commit()
    
    if is_valid:
        return True, None
    else:
        remaining = otp_token.max_attempts - otp_token.attempts
        if remaining > 0:
            error_msg = f"Invalid verification code. {remaining} attempt(s) remaining."
        else:
            error_msg = "Too many failed attempts. Please request a new verification code."
        return False, error_msg


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    return True, None

