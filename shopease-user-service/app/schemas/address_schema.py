from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.user_schema import validate_phone


class AddressBase(BaseModel):
    """Base schema for address fields."""
    address_type: str = Field(default="Home", description="Address type: Home, Office, or Other")
    full_name: str = Field(..., min_length=2, max_length=255, description="Recipient full name")
    phone_number: str = Field(..., description="Recipient contact phone number")
    address_line_1: str = Field(..., min_length=3, max_length=255, description="Primary street address")
    address_line_2: Optional[str] = Field(None, max_length=255, description="Apartment, suite, unit, etc.")
    city: str = Field(..., min_length=2, max_length=100, description="City name")
    state: str = Field(..., min_length=2, max_length=100, description="State / Province")
    country: str = Field(..., min_length=2, max_length=100, description="Country name")
    postal_code: str = Field(..., min_length=2, max_length=20, description="Postal / ZIP code")
    is_default: bool = Field(default=False, description="Whether this is the default delivery address")

    @field_validator("address_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        trimmed = v.strip().title()
        if trimmed not in ("Home", "Office", "Other"):
            return "Other"
        return trimmed

    @field_validator("full_name", "address_line_1", "city", "state", "country", "postal_code")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace.")
        return trimmed

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        return validate_phone(v) or v


class AddressCreate(AddressBase):
    """Payload to create a new delivery address."""
    pass


class AddressUpdate(AddressBase):
    """Payload to update an existing delivery address."""
    pass


class AddressResponse(AddressBase):
    """Delivery address response representation."""
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

