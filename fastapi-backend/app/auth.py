from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from .database import get_session
from .models import Porter
from sqlmodel import select

# Settings (in real deploy these should come from env variables)
from dotenv import dotenv_values
from pathlib import Path
import logging

logger = logging.getLogger("app.auth")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)

_env_path = Path(__file__).resolve().parents[2] / ".env"
config = dotenv_values(str(_env_path))
SECRET_KEY = config.get("JWT_SECRET") or "change-me-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get("JWT_ACCESS_MINUTES") or 60)

# Use pbkdf2_sha256 here to avoid requiring a working bcrypt C-extension
# in test environments. It's secure and avoids the bcrypt/packaging issues
# we hit in CI/local where the bcrypt binary wasn't behaving as expected.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
# Use auto_error=False so the dependency doesn't raise before we can
# provide a consistent 401 message (this avoids intermittent differences
# between HTTP client and FastAPI's security layer during tests).
security = HTTPBearer(auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: Optional[str] = None
    exp: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, role: Optional[str] = None, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject}
    if role:
        to_encode["role"] = role
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp())})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tp = TokenPayload(**payload)
        logger.debug("Decoded token payload: %s", tp.dict())
        return tp
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", headers={"X-Auth-Reason": "Invalid token"}) from exc


def authenticate_porter(username: str, password: str, session) -> Optional[Porter]:
    # Allow login by email or phone
    statement = select(Porter).where((Porter.email == username) | (Porter.phone == username))
    porter = session.exec(statement).first()
    if not porter or not porter.password_hash:
        return None
    if not verify_password(password, porter.password_hash):
        return None
    return porter


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session=Depends(get_session)) -> Porter:
    # HTTPBearer(auto_error=False) returns None when no credentials were provided
    if not credentials or not getattr(credentials, "credentials", None):
        # Normalize to a consistent 401 for the callers
        logger.info("[auth.debug] No credentials provided or empty credentials object: %s", credentials)
        print(f"[auth.debug] No credentials provided or empty credentials object: {credentials}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"X-Auth-Reason": "No credentials"})

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except HTTPException:
        # decode_access_token already raises a 401; re-raise to preserve semantics
        logger.info("[auth.debug] decode_access_token failed for token: %s", token)
        print(f"[auth.debug] decode_access_token failed for token: {token}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", headers={"X-Auth-Reason": "Token decode failed"})

    porter_id = payload.sub
    # Debug: print the token payload and subject type to help diagnose mapping issues
    # Use logger to ensure lines appear in uvicorn/app logs
    try:
        p_dict = payload.dict()
    except Exception:
        p_dict = getattr(payload, "__dict__", str(payload))
    logger.info("[auth.debug] Decoded token payload: %s", p_dict)
    logger.info("[auth.debug] Token subject (sub) value: %r (type=%s)", porter_id, type(porter_id))
    print(f"[auth.debug] Decoded token payload: {p_dict}")
    print(f"[auth.debug] Token subject (sub) value: {porter_id!r} (type={type(porter_id)})")
    statement = select(Porter).where(Porter.id == porter_id)
    porter = session.exec(statement).first()
    if not porter:
        # Token subject did not map to a valid porter
        logger.info("[auth.debug] No porter found matching id: %r", porter_id)
        print(f"[auth.debug] No porter found matching id: {porter_id!r}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials", headers={"X-Auth-Reason": "Token subject not found"})
    return porter


def require_role(required_role: str):
    def role_checker(user: Porter = Depends(get_current_user)) -> Porter:
        # Use explicit role column stored on Porter model
        user_role = (user.role or "porter").lower()
        if required_role == "admin" and user_role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user
    return role_checker


def get_token_subject(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Return the token subject (sub) from the Authorization header.

    This helper decodes the token and returns its subject so handlers
    can compare directly against request payloads when needed.
    """
    if not credentials or not getattr(credentials, "credentials", None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"X-Auth-Reason": "No credentials"})
    token = credentials.credentials
    payload = decode_access_token(token)
    return payload.sub


def create_porter(session, full_name: str, password: str, email: Optional[str] = None, phone: Optional[str] = None, role: Optional[str] = "porter") -> Porter:
    """Helper to create a porter with hashed password. Returns the created Porter."""
    # If a porter with the same email or phone already exists, return it
    # to avoid creating duplicate rows which can make login/registration
    # behavior non-deterministic in tests.
    if email:
        stmt = select(Porter).where(Porter.email == email)
        existing = session.exec(stmt).first()
        if existing:
            return existing
    if phone:
        stmt = select(Porter).where(Porter.phone == phone)
        existing = session.exec(stmt).first()
        if existing:
            return existing

    ph = get_password_hash(password)
    data = {"full_name": full_name, "password_hash": ph, "role": role}
    if email:
        data["email"] = email
    if phone:
        data["phone"] = phone
    porter = Porter(**data)
    session.add(porter)
    session.commit()
    session.refresh(porter)
    return porter


# RBAC / status transition rules
ALLOWED_TRANSITIONS = {
    "reported": {"in_progress"},
    "in_progress": {"resolved", "reported"},
    "resolved": {"closed", "in_progress"},
    "closed": set(),
}


def can_transition(role: Optional[str], old_status: str, new_status: str) -> Tuple[bool, int, str]:
    """Return (allowed, http_code, message) for the requested transition.

    - Returns (False, 400, msg) for invalid transitions.
    - Returns (False, 403, msg) for role-not-allowed transitions (e.g., only admin can 'closed').
    - Returns (True, 200, '') for allowed transitions.
    """
    old = old_status or "reported"
    if new_status not in ALLOWED_TRANSITIONS.get(old, set()):
        return False, 400, f"Invalid status transition from {old} to {new_status}"
    # Only admin may set 'closed'
    if new_status == "closed" and (role or "porter") != "admin":
        return False, 403, "Only admin can set status to 'closed'"
    return True, 200, ""
