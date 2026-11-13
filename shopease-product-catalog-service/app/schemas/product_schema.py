from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Detailed product description")
    sku: str = Field(..., min_length=1, max_length=100, description="Unique Stock Keeping Unit")
    category_id: int = Field(..., description="ID of the parent category")
    price: Decimal = Field(..., ge=0, description="Product price (cannot be negative)")
    discount_price: Optional[Decimal] = Field(None, ge=0, description="Discounted price (optional)")
    stock_quantity: int = Field(0, ge=0, description="Available stock quantity (cannot be negative)")
    image_url: Optional[str] = Field(None, max_length=500, description="Image URL")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    is_active: bool = Field(True, description="Whether the product is active/available")

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.discount_price is not None and self.discount_price > self.price:
            raise ValueError("Discount price cannot exceed the original price.")
        return self


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    sku: str = Field(..., min_length=1, max_length=100)
    category_id: int
    price: Decimal = Field(..., ge=0)
    discount_price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: int = Field(..., ge=0)
    image_url: Optional[str] = None
    brand: Optional[str] = None
    is_active: bool

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.discount_price is not None and self.discount_price > self.price:
            raise ValueError("Discount price cannot exceed the original price.")
        return self


class ProductPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[int] = None
    price: Optional[Decimal] = Field(None, ge=0)
    discount_price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    brand: Optional[str] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.price is not None and self.discount_price is not None:
            if self.discount_price > self.price:
                raise ValueError("Discount price cannot exceed the original price.")
        return self


class ProductResponse(ProductBase):
    id: int
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total_items: int
    total_pages: int
    page: int
    page_size: int

