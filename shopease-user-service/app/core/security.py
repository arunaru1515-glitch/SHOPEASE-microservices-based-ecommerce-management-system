from typing import Any, Dict, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db
from app.models.user_model import UserProfile

security_scheme = HTTPBearer(auto_error=False)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token using the shared secret and algorithm.
    Raises HTTP 401 if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_auth_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    FastAPI dependency that validates Bearer JWT token from Authorization header.
    Extracts the authenticated user's ID ('sub'), email, and role.
    Raises HTTP 401 for missing or malformed tokens.
    """
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please provide Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth_header.credentials)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: Subject (user ID) missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        auth_user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user ID in authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "auth_user_id": auth_user_id,
        "email": payload.get("email"),
        "role": payload.get("role", "customer"),
    }


def get_current_user_profile(
    auth_user: Dict[str, Any] = Depends(get_current_auth_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """
    FastAPI dependency that resolves the authenticated user's local UserProfile.
    Enforces that users can only access their own profile.
    Raises HTTP 404 if profile does not exist yet.
    Raises HTTP 403 if profile is deactivated.
    """
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.auth_user_id == auth_user["auth_user_id"])
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please create your profile first.",
        )

    if not profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User profile is inactive. Please contact support.",
        )

    return profile

