from typing import Optional
from datetime import datetime, timedelta
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

config = dotenv_values("../.env")
SECRET_KEY = config.get("JWT_SECRET") or "change-me-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get("JWT_ACCESS_MINUTES") or 60)

# Use pbkdf2_sha256 here to avoid requiring a working bcrypt C-extension
# in test environments. It's secure and avoids the bcrypt/packaging issues
# we hit in CI/local where the bcrypt binary wasn't behaving as expected.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()


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
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp())})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials") from exc


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
    token = credentials.credentials
    payload = decode_access_token(token)
    porter_id = payload.sub
    statement = select(Porter).where(Porter.id == porter_id)
    porter = session.exec(statement).first()
    if not porter:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return porter


def require_role(required_role: str):
    def role_checker(user: Porter = Depends(get_current_user)) -> Porter:
        # Use explicit role column stored on Porter model
        user_role = (user.role or "porter").lower()
        if required_role == "admin" and user_role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user
    return role_checker


def create_porter(session, full_name: str, password: str, email: Optional[str] = None, phone: Optional[str] = None, role: Optional[str] = "porter") -> Porter:
    """Helper to create a porter with hashed password. Returns the created Porter."""
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
