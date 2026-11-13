from typing import Any, Dict, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# HTTPBearer security scheme for extracting Bearer tokens from request headers
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

    role = payload.get("role", "customer")
    return {
        "auth_user_id": auth_user_id,
        "email": payload.get("email"),
        "role": str(role).lower(),
    }


def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_auth_user),
) -> Dict[str, Any]:
    """
    FastAPI dependency enforcing administrator role.
    Raises HTTP 403 Forbidden if user is not an administrator.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrative privileges required.",
        )
    return current_user


def get_optional_auth_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for endpoints accessible to the public,
    while still recognizing authenticated users (such as admin viewing inactive items).
    Raises HTTP 401 if an invalid/expired token is explicitly provided.
    """
    if not auth_header or not auth_header.credentials:
        return None
    return get_current_auth_user(auth_header)

