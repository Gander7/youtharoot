"""
Authentication and authorization utilities for the Youtharoot system.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.repositories import get_user_repository
from app.models import User

# JWT settings
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# Security scheme for Bearer token
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash using bcrypt directly."""
    try:
        # Convert strings to bytes
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        
        # Truncate password if it's longer than 72 bytes (bcrypt limitation)
        if len(password_bytes) > 72:
            print(f"⚠️ Password too long ({len(password_bytes)} bytes), truncating to 72 bytes")
            password_bytes = password_bytes[:72]
        
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password for storing using bcrypt directly."""
    try:
        # Convert to bytes
        password_bytes = password.encode('utf-8')
        
        # Truncate password if it's longer than 72 bytes (bcrypt limitation)
        if len(password_bytes) > 72:
            print(f"⚠️ Password too long ({len(password_bytes)} bytes), truncating to 72 bytes")
            password_bytes = password_bytes[:72]
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error hashing password"
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode the JWT token
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # Extract user information from token
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    # Get user from database
    user_repo = get_user_repository(db)
    user = await user_repo.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current user and verify they have admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user


async def authenticate_user(username: str, password: str, db: Session) -> Union[User, bool]:
    """Authenticate a user by username and password."""
    user_repo = get_user_repository(db)
    user = await user_repo.get_user_by_username(username)
    
    if not user:
        return False
    
    if not verify_password(password, user.password_hash):
        return False
    
    return user