import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


def validate_password_strength(password: str) -> str:
    """
    Validates password complexity:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one numeric digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=\[\]\\/]", password):
        raise ValueError("Password must contain at least one special character.")
    return password


# ==========================================
# User Output Schemas
# ==========================================

class UserResponse(BaseModel):
    """Safe user profile response excluding any sensitive data."""
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    """Brief user profile for login/register responses."""
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Registration Schemas
# ==========================================

class UserRegisterRequest(BaseModel):
    """Payload for user registration."""
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=8, description="Strong password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Full name cannot be empty or whitespace.")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("password and confirm_password do not match.")
        return self


class UserRegisterResponse(BaseModel):
    """Response returned upon successful registration."""
    message: str = "User registered successfully."
    user: UserSummary


# ==========================================
# Login & Token Schemas
# ==========================================

class UserLoginRequest(BaseModel):
    """Payload for user login."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")


class TokenResponse(BaseModel):
    """JWT response structure."""
    message: str = "Login successful."
    access_token: str
    token_type: str = "bearer"
    user: UserSummary


class TokenVerifyRequest(BaseModel):
    """Payload to verify token validity."""
    token: str = Field(..., min_length=1, description="JWT token to verify")


class TokenVerifyResponse(BaseModel):
    """Response returned when verifying a token."""
    valid: bool
    message: str
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    expires_at: Optional[datetime] = None


# ==========================================
# Change Password Schemas
# ==========================================

class ChangePasswordRequest(BaseModel):
    """Payload to change the authenticated user's password."""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New strong password")
    confirm_new_password: str = Field(..., min_length=8, description="Confirmation of new password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def check_new_passwords(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("new_password and confirm_new_password do not match.")
        if self.current_password == self.new_password:
            raise ValueError("New password cannot be identical to the current password.")
        return self


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

