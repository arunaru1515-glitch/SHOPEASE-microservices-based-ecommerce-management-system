from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ProductStatus(str, Enum):
    """Enumeration of allowed product lifecycle statuses."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class ProductBase(BaseModel):
    """Base schema holding common fields for products."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=120,
        description="Product name (2-120 characters, non-empty)",
        examples=["Wireless Noise-Canceling Headphones"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Detailed product description (up to 1000 characters)",
        examples=["Premium over-ear Bluetooth headphones with active noise cancellation."],
    )
    price: float = Field(
        ...,
        gt=0,
        description="Product price in USD (must be strictly greater than 0)",
        examples=[129.99],
    )
    stock_quantity: int = Field(
        ...,
        ge=0,
        description="Available inventory stock (must be 0 or positive integer)",
        examples=[50],
    )
    category: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Product category (2-60 characters, non-empty)",
        examples=["Electronics"],
    )
    status: ProductStatus = Field(
        default=ProductStatus.ACTIVE,
        description="Product status (Active or Inactive)",
        examples=[ProductStatus.ACTIVE],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Product name cannot be empty or contain only whitespace.")
        if len(cleaned) < 2:
            raise ValueError("Product name must be at least 2 characters long.")
        return cleaned

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Product category cannot be empty or contain only whitespace.")
        if len(cleaned) < 2:
            raise ValueError("Product category must be at least 2 characters long.")
        return cleaned

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            return cleaned if cleaned else None
        return None


class ProductCreate(ProductBase):
    """Request schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Request schema for updating an existing product (all fields optional)."""

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=120,
        description="Product name (2-120 characters)",
        examples=["Wireless Headphones Pro"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Detailed description (up to 1000 characters)",
        examples=["Upgraded wireless headphones with spatial audio."],
    )
    price: Optional[float] = Field(
        default=None,
        gt=0,
        description="Product price (strictly greater than 0)",
        examples=[149.99],
    )
    stock_quantity: Optional[int] = Field(
        default=None,
        ge=0,
        description="Available inventory stock (0 or positive integer)",
        examples=[35],
    )
    category: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=60,
        description="Product category",
        examples=["Audio"],
    )
    status: Optional[ProductStatus] = Field(
        default=None,
        description="Product status (Active or Inactive)",
        examples=[ProductStatus.ACTIVE],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Product name cannot be empty or contain only whitespace.")
            if len(cleaned) < 2:
                raise ValueError("Product name must be at least 2 characters long.")
            return cleaned
        return None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Product category cannot be empty or contain only whitespace.")
            if len(cleaned) < 2:
                raise ValueError("Product category must be at least 2 characters long.")
            return cleaned
        return None

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned = value.strip()
            return cleaned if cleaned else None
        return None


class ProductResponse(ProductBase):
    """Response schema representing a product."""

    id: int = Field(..., description="Unique product identifier", examples=[1])
    created_at: datetime = Field(..., description="Timestamp when product was created")
    updated_at: datetime = Field(..., description="Timestamp when product was last updated")

    model_config = ConfigDict(from_attributes=True)


class StandardErrorResponse(BaseModel):
    """Standardized error response payload."""

    success: bool = Field(default=False, description="Operation success flag")
    error: str = Field(..., description="Short error code / title")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(default=None, description="Detailed error breakdown")
