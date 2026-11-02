from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ProductStatus(str, Enum):
    """Enumeration of valid product statuses."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Product:
    """In-memory Product domain model entity."""

    def __init__(
        self,
        id: int,
        name: str,
        description: Optional[str],
        price: float,
        stock_quantity: int,
        category: str,
        status: ProductStatus = ProductStatus.ACTIVE,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.price = float(price)
        self.stock_quantity = int(stock_quantity)
        self.category = category
        self.status = status if isinstance(status, ProductStatus) else ProductStatus(status)
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> dict:
        """Convert model instance to standard dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "category": self.category,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
