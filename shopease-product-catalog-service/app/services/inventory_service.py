from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inventory_model import InventoryTransaction
from app.models.product_model import Product
from app.schemas.inventory_schema import (
    LowStockProductResponse,
    StockAdjustmentRequest,
    StockStatusResponse,
)


class InventoryService:
    @staticmethod
    def get_current_stock(
        db: Session, product_id: int, threshold: Optional[int] = None
    ) -> StockStatusResponse:
        """
        Retrieves current stock level and low-stock indicator for a product.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found.",
            )

        effective_threshold = (
            threshold if threshold is not None else settings.DEFAULT_LOW_STOCK_THRESHOLD
        )
        is_low_stock = product.stock_quantity <= effective_threshold

        return StockStatusResponse(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            current_stock=product.stock_quantity,
            is_low_stock=is_low_stock,
            low_stock_threshold=effective_threshold,
        )

    @staticmethod
    def stock_in(
        db: Session, product_id: int, request: StockAdjustmentRequest
    ) -> Tuple[Product, InventoryTransaction]:
        """
        Increases stock for a product atomically and logs the transaction.
        Uses database row locking (with_for_update) to prevent race conditions.
        """
        try:
            product = (
                db.query(Product)
                .filter(Product.id == product_id)
                .with_for_update()
                .first()
            )
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product_id} not found.",
                )

            previous_stock = product.stock_quantity
            updated_stock = previous_stock + request.quantity
            product.stock_quantity = updated_stock

            transaction = InventoryTransaction(
                product_id=product.id,
                transaction_type="IN",
                quantity=request.quantity,
                previous_stock=previous_stock,
                updated_stock=updated_stock,
                remarks=request.remarks.strip() if request.remarks else "Manual Stock IN",
            )
            db.add(transaction)
            db.commit()
            db.refresh(product)
            db.refresh(transaction)
            return product, transaction
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process stock intake: {str(e)}",
            )

    @staticmethod
    def stock_out(
        db: Session, product_id: int, request: StockAdjustmentRequest
    ) -> Tuple[Product, InventoryTransaction]:
        """
        Decreases stock for a product atomically and logs the transaction.
        Prevents stock from dropping below zero.
        Uses row locking to handle concurrent deductions safely.
        """
        try:
            product = (
                db.query(Product)
                .filter(Product.id == product_id)
                .with_for_update()
                .first()
            )
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product_id} not found.",
                )

            previous_stock = product.stock_quantity
            if request.quantity > previous_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient stock for product '{product.name}' (SKU: {product.sku}). "
                        f"Requested deduction: {request.quantity}, Available: {previous_stock}."
                    ),
                )

            updated_stock = previous_stock - request.quantity
            product.stock_quantity = updated_stock

            transaction = InventoryTransaction(
                product_id=product.id,
                transaction_type="OUT",
                quantity=request.quantity,
                previous_stock=previous_stock,
                updated_stock=updated_stock,
                remarks=request.remarks.strip() if request.remarks else "Manual Stock OUT",
            )
            db.add(transaction)
            db.commit()
            db.refresh(product)
            db.refresh(transaction)
            return product, transaction
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process stock deduction: {str(e)}",
            )

    @staticmethod
    def get_stock_history(
        db: Session, product_id: int, limit: int = 50
    ) -> List[InventoryTransaction]:
        """
        Retrieves audit trail of all inventory transactions for a product.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found.",
            )

        transactions = (
            db.query(InventoryTransaction)
            .filter(InventoryTransaction.product_id == product_id)
            .order_by(InventoryTransaction.created_at.desc())
            .limit(limit)
            .all()
        )
        return transactions

    @staticmethod
    def list_low_stock_products(
        db: Session, threshold: Optional[int] = None
    ) -> List[LowStockProductResponse]:
        """
        Lists active products whose stock quantity is at or below the threshold.
        """
        effective_threshold = (
            threshold if threshold is not None else settings.DEFAULT_LOW_STOCK_THRESHOLD
        )

        products = (
            db.query(Product)
            .filter(
                Product.stock_quantity <= effective_threshold,
                Product.is_active.is_(True),
            )
            .order_by(Product.stock_quantity.asc())
            .all()
        )

        response = []
        for p in products:
            response.append(
                LowStockProductResponse(
                    id=p.id,
                    name=p.name,
                    sku=p.sku,
                    stock_quantity=p.stock_quantity,
                    threshold=effective_threshold,
                    category_id=p.category_id,
                    category_name=p.category.name if p.category else None,
                    is_active=p.is_active,
                )
            )
        return response

