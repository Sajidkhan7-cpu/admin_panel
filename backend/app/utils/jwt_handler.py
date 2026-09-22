"""
utils/jwt_handler.py
Creates and decodes JWT access tokens used for student/admin auth,
plus short-lived tokens used for the developer's admin-approval workflow.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    return decode_access_token(token)


def require_admin(payload: dict = Depends(get_current_user_payload)) -> dict:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return payload


# ---------------- Admin approval tokens ----------------

def _create_approval_token(user_id: int, action: str) -> str:
    to_encode = {
        "sub": str(user_id),
        "action": action,  # "approve" or "reject"
        "purpose": "admin_approval",
        "exp": datetime.utcnow() + timedelta(minutes=settings.APPROVAL_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_approve_token(user_id: int) -> str:
    return _create_approval_token(user_id, "approve")


def create_reject_token(user_id: int) -> str:
    return _create_approval_token(user_id, "reject")


def decode_approval_token(token: str, expected_action: str) -> int:
    """Returns user_id if valid and action matches, raises HTTPException otherwise."""
    invalid_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired link",
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise invalid_exception

    if payload.get("purpose") != "admin_approval" or payload.get("action") != expected_action:
        raise invalid_exception

    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        raise invalid_exception