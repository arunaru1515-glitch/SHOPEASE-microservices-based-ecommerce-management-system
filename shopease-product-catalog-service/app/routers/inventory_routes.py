from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.database.connection import get_db
from app.schemas.inventory_schema import (
    InventoryTransactionResponse,
    LowStockProductResponse,
    StockAdjustmentRequest,
    StockAdjustmentResponse,
    StockStatusResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/api/inventory", tags=["Inventory Management"])


@router.get(
    "/low-stock",
    response_model=List[LowStockProductResponse],
    summary="List low-stock products (Admin only)",
)
def list_low_stock(
    threshold: Optional[int] = Query(None, ge=0, description="Custom low-stock threshold"),
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Lists all active products whose stock quantity is at or below the threshold.
    Only administrators can view low stock reports.
    """
    return InventoryService.list_low_stock_products(db, threshold=threshold)


@router.get(
    "/{product_id}",
    response_model=StockStatusResponse,
    summary="Get current stock status for a product",
)
def get_current_stock(
    product_id: int,
    threshold: Optional[int] = Query(None, ge=0, description="Custom low-stock threshold"),
    db: Session = Depends(get_db),
):
    """
    Retrieves current stock count and whether the item is running low.
    Accessible to all users and integrated services.
    """
    return InventoryService.get_current_stock(db, product_id, threshold=threshold)


@router.post(
    "/{product_id}/stock-in",
    response_model=StockAdjustmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Increase product stock (Admin only)",
)
def stock_in(
    product_id: int,
    request: StockAdjustmentRequest,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Increases available stock for a product and logs an audit transaction.
    Atomic database transaction.
    """
    product, tx = InventoryService.stock_in(db, product_id, request)
    return StockAdjustmentResponse(
        message=f"Stock successfully increased by {request.quantity}.",
        product_id=product.id,
        previous_stock=tx.previous_stock,
        updated_stock=product.stock_quantity,
        transaction=InventoryTransactionResponse.model_validate(tx),
    )


@router.post(
    "/{product_id}/stock-out",
    response_model=StockAdjustmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Decrease product stock (Admin only)",
)
def stock_out(
    product_id: int,
    request: StockAdjustmentRequest,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Decreases available stock for a product and logs an audit transaction.
    Prevents stock from dropping below zero.
    Atomic database transaction with row-level locking.
    """
    product, tx = InventoryService.stock_out(db, product_id, request)
    return StockAdjustmentResponse(
        message=f"Stock successfully decreased by {request.quantity}.",
        product_id=product.id,
        previous_stock=tx.previous_stock,
        updated_stock=product.stock_quantity,
        transaction=InventoryTransactionResponse.model_validate(tx),
    )


@router.get(
    "/{product_id}/history",
    response_model=List[InventoryTransactionResponse],
    summary="View inventory transaction history (Admin only)",
)
def get_inventory_history(
    product_id: int,
    limit: int = Query(50, ge=1, le=500, description="Max history records to return"),
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Retrieves complete stock modification audit trail for a product.
    Only administrators can view stock history.
    """
    transactions = InventoryService.get_stock_history(db, product_id, limit=limit)
    return [InventoryTransactionResponse.model_validate(tx) for tx in transactions]

