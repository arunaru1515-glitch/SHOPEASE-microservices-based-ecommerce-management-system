from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.database.connection import get_db
from app.models.user_model import User
from app.schemas.auth_schema import (
    ChangePasswordRequest,
    MessageResponse,
    TokenResponse,
    TokenVerifyRequest,
    TokenVerifyResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
    UserSummary,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new user, hashes their password, and assigns the default role.",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user account."""
    user = AuthService.register_user(db=db, req=payload)
    return UserRegisterResponse(
        message="User registered successfully.",
        user=UserSummary.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
    description="Authenticates user credentials and returns a JWT access token.",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate and obtain JWT access token."""
    user, access_token = AuthService.authenticate_user(db=db, req=payload)
    return TokenResponse(
        message="Login successful.",
        access_token=access_token,
        token_type="bearer",
        user=UserSummary.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the profile information of the currently authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve details of the authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/verify-token",
    response_model=TokenVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate an access token",
    description="Validates a JWT token's signature, expiration, and user account status.",
)
def verify_token(
    payload: TokenVerifyRequest,
    db: Session = Depends(get_db),
):
    """Verify validity of a given JWT token."""
    return AuthService.verify_token(token_str=payload.token, db=db)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    description="Updates the authenticated user's password after verifying the current password.",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    AuthService.change_password(db=db, current_user=current_user, req=payload)
    return MessageResponse(message="Password changed successfully.")

