from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_auth_user
from app.database.connection import get_db
from app.models.user_model import UserProfile
from app.schemas.address_schema import AddressResponse
from app.schemas.user_schema import MessageResponse, UserProfileResponse

router = APIRouter(prefix="/account", tags=["User Account Management"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get complete account overview",
    description="Returns customer profile information, all saved addresses, and active status.",
)
def get_account_overview(
    auth_user: Dict[str, Any] = Depends(get_current_auth_user),
    db: Session = Depends(get_db),
):
    """Retrieve full account dashboard for current user."""
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.auth_user_id == auth_user["auth_user_id"])
        .first()
    )

    if not profile:
        return {
            "status": "profile_incomplete",
            "auth_user_id": auth_user["auth_user_id"],
            "email": auth_user["email"],
            "role": auth_user["role"],
            "profile": None,
            "addresses": [],
            "message": "User profile has not been created yet.",
        }

    return {
        "status": "active" if profile.is_active else "deactivated",
        "auth_user_id": auth_user["auth_user_id"],
        "email": auth_user["email"],
        "role": auth_user["role"],
        "profile": UserProfileResponse.model_validate(profile),
        "total_addresses": len(profile.addresses),
        "addresses": [AddressResponse.model_validate(a) for a in profile.addresses],
    }


@router.patch(
    "/deactivate",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate user profile",
    description="Deactivates customer profile and addresses in User Service without deleting the core auth credentials.",
)
def deactivate_account(
    auth_user: Dict[str, Any] = Depends(get_current_auth_user),
    db: Session = Depends(get_db),
):
    """Deactivate profile in User Service."""
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.auth_user_id == auth_user["auth_user_id"])
        .first()
    )
    if not profile:
        return MessageResponse(message="No active profile found to deactivate.")

    profile.is_active = False
    db.commit()
    return MessageResponse(
        message=(
            "User profile has been deactivated in the User Service. "
            "Profile and address data are preserved but restricted from operations."
        )
    )


@router.patch(
    "/reactivate",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate user profile",
    description="Reactivates customer profile in User Service.",
)
def reactivate_account(
    auth_user: Dict[str, Any] = Depends(get_current_auth_user),
    db: Session = Depends(get_db),
):
    """Reactivate profile in User Service."""
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.auth_user_id == auth_user["auth_user_id"])
        .first()
    )
    if not profile:
        return MessageResponse(message="No profile found to reactivate.")

    profile.is_active = True
    db.commit()
    return MessageResponse(message="User profile has been successfully reactivated.")

