from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_auth_user, get_current_user_profile
from app.database.connection import get_db
from app.models.user_model import UserProfile
from app.schemas.user_schema import (
    MessageResponse,
    UserProfileCreate,
    UserProfilePatch,
    UserProfileResponse,
    UserProfileUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/profile", tags=["User Profiles"])


@router.post(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user profile",
    description="Creates a new customer profile linked to the authenticated user ID extracted from JWT.",
)
def create_profile(
    payload: UserProfileCreate,
    auth_user: Dict[str, Any] = Depends(get_current_auth_user),
    db: Session = Depends(get_db),
):
    """Create user profile for authenticated user."""
    profile = UserService.create_profile(
        db=db,
        auth_user_id=auth_user["auth_user_id"],
        req=payload,
    )
    return UserProfileResponse.model_validate(profile)


@router.get(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user's profile",
    description="Retrieves the profile of the authenticated user. Enforces strict user isolation.",
)
def get_my_profile(
    profile: UserProfile = Depends(get_current_user_profile),
):
    """Get authenticated user's profile."""
    return UserProfileResponse.model_validate(profile)


@router.put(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user's profile",
    description="Performs a full update of the authenticated user's profile.",
)
def update_my_profile(
    payload: UserProfileUpdate,
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Full update of current user profile."""
    updated = UserService.update_profile(db=db, profile=profile, req=payload)
    return UserProfileResponse.model_validate(updated)


@router.patch(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update current user's profile",
    description="Partially updates specific fields in the authenticated user's profile.",
)
def patch_my_profile(
    payload: UserProfilePatch,
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Partial update of current user profile."""
    patched = UserService.patch_profile(db=db, profile=profile, req=payload)
    return UserProfileResponse.model_validate(patched)


@router.delete(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete current user's profile",
    description="Deletes the authenticated user's profile and all associated delivery addresses.",
)
def delete_my_profile(
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Delete current user profile."""
    UserService.delete_profile(db=db, profile=profile)
    return MessageResponse(message="User profile deleted successfully.")

