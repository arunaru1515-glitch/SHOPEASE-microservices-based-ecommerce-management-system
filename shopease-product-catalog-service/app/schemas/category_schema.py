from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(True, description="Whether the category is active")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated category name")
    description: Optional[str] = Field(None, description="Updated category description")
    is_active: Optional[bool] = Field(None, description="Updated category status")


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    products_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

