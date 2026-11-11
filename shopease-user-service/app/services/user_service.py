from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import UserProfile
from app.schemas.user_schema import (
    UserProfileCreate,
    UserProfilePatch,
    UserProfileUpdate,
)


class UserService:
    """Service class encapsulating business logic for User Profiles."""

    @staticmethod
    def create_profile(
        db: Session,
        auth_user_id: int,
        req: UserProfileCreate,
    ) -> UserProfile:
        """
        Creates a new user profile linked to the authenticated user ID.
        Prevents duplicate profiles for the same auth_user_id.
        """
        existing = (
            db.query(UserProfile)
            .filter(UserProfile.auth_user_id == auth_user_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A profile already exists for this authenticated user.",
            )

        new_profile = UserProfile(
            auth_user_id=auth_user_id,
            full_name=req.full_name,
            phone_number=req.phone_number,
            date_of_birth=req.date_of_birth,
            gender=req.gender,
            profile_image=req.profile_image,
            is_active=True,
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return new_profile

    @staticmethod
    def update_profile(
        db: Session,
        profile: UserProfile,
        req: UserProfileUpdate,
    ) -> UserProfile:
        """
        Performs a full update of the current user's profile.
        """
        profile.full_name = req.full_name
        profile.phone_number = req.phone_number
        profile.date_of_birth = req.date_of_birth
        profile.gender = req.gender
        profile.profile_image = req.profile_image
        profile.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def patch_profile(
        db: Session,
        profile: UserProfile,
        req: UserProfilePatch,
    ) -> UserProfile:
        """
        Performs a partial update of the current user's profile.
        """
        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return profile

        for key, value in update_data.items():
            setattr(profile, key, value)

        profile.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete_profile(
        db: Session,
        profile: UserProfile,
    ) -> None:
        """
        Deletes the current user's profile and cascades deletion to all associated addresses.
        """
        db.delete(profile)
        db.commit()

