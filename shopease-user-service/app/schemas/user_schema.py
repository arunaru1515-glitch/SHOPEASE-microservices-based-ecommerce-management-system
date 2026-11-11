import re
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_phone(phone: Optional[str]) -> Optional[str]:
    """Validates international or local phone number format."""
    if phone is None:
        return None
    cleaned = phone.strip()
    if not cleaned:
        return None
    # Allows + followed by digits, spaces, hyphens, min 7 digits, max 15 digits
    digits_only = re.sub(r"[^\d]", "", cleaned)
    if len(digits_only) < 7 or len(digits_only) > 15:
        raise ValueError("Phone number must contain between 7 and 15 digits.")
    return cleaned


class UserProfileCreate(BaseModel):
    """Payload to create a new user profile."""
    full_name: str = Field(..., min_length=2, max_length=255, description="Full customer name")
    phone_number: Optional[str] = Field(None, description="Contact phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, max_length=20, description="Gender (e.g. Male, Female, Other)")
    profile_image: Optional[str] = Field(None, max_length=500, description="Profile image URL or path")

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Full name cannot be empty.")
        return trimmed

    @field_validator("phone_number")
    @classmethod
    def validate_phone_field(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone(v)


class UserProfileUpdate(BaseModel):
    """Payload for full update (PUT) of user profile."""
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    profile_image: Optional[str] = Field(None, max_length=500)

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Full name cannot be empty.")
        return trimmed

    @field_validator("phone_number")
    @classmethod
    def validate_phone_field(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone(v)


class UserProfilePatch(BaseModel):
    """Payload for partial update (PATCH) of user profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    profile_image: Optional[str] = Field(None, max_length=500)

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Full name cannot be empty.")
            return trimmed
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_field(cls, v: Optional[str]) -> Optional[str]:
        return validate_phone(v)


class UserProfileResponse(BaseModel):
    """Safe profile response."""
    id: int
    auth_user_id: int
    full_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

