from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StockAdjustmentRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Stock quantity to adjust (must be greater than 0)")
    remarks: Optional[str] = Field(None, max_length=255, description="Audit reason for stock adjustment")


class InventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    transaction_type: str
    quantity: int
    previous_stock: int
    updated_stock: int
    remarks: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StockStatusResponse(BaseModel):
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    is_low_stock: bool
    low_stock_threshold: int


class StockAdjustmentResponse(BaseModel):
    message: str
    product_id: int
    previous_stock: int
    updated_stock: int
    transaction: InventoryTransactionResponse


class LowStockProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    stock_quantity: int
    threshold: int
    category_id: int
    category_name: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

