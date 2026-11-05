from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Optional

from app.exceptions import DuplicateProductException, ProductNotFoundException
from app.models.product_model import Product, ProductStatus
from app.schemas.product_schema import ProductCreate, ProductUpdate


class ProductService:
    """Business logic and in-memory repository for Product management."""

    def __init__(self):
        self._products: Dict[int, Product] = {}
        self._id_counter: int = 0
        self._lock: Lock = Lock()

    def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product with auto-generated ID and persist to memory."""
        with self._lock:
            # Check for duplicate product by name and category (case-insensitive)
            for existing in self._products.values():
                if (
                    existing.name.strip().lower() == product_data.name.strip().lower()
                    and existing.category.strip().lower() == product_data.category.strip().lower()
                ):
                    raise DuplicateProductException(
                        f"'{product_data.name}' in category '{product_data.category}'"
                    )

            self._id_counter += 1
            new_id = self._id_counter
            now = datetime.now(timezone.utc)

            new_product = Product(
                id=new_id,
                name=product_data.name,
                description=product_data.description,
                price=product_data.price,
                stock_quantity=product_data.stock_quantity,
                category=product_data.category,
                status=product_data.status,
                created_at=now,
                updated_at=now,
            )

            self._products[new_id] = new_product
            return new_product

    def get_all_products(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Product]:
        """Retrieve products with optional category filtering and pagination."""
        with self._lock:
            products_list = list(self._products.values())

            # Apply category filter (case-insensitive substring or exact match)
            if category:
                target_cat = category.strip().lower()
                products_list = [
                    p for p in products_list if p.category.strip().lower() == target_cat
                ]

            # Apply pagination (skip and limit)
            start = max(0, skip)
            end = start + max(1, limit)
            return products_list[start:end]

    def get_product_by_id(self, product_id: int) -> Product:
        """Retrieve a single product by its unique identifier."""
        with self._lock:
            if product_id not in self._products:
                raise ProductNotFoundException(product_id)
            return self._products[product_id]

    def update_product(self, product_id: int, update_data: ProductUpdate) -> Product:
        """Update existing product fields and refresh updated_at timestamp."""
        with self._lock:
            if product_id not in self._products:
                raise ProductNotFoundException(product_id)

            existing = self._products[product_id]

            # If name or category changed, check for conflict with other products
            new_name = update_data.name or existing.name
            new_category = update_data.category or existing.category
            for other_id, other in self._products.items():
                if other_id != product_id:
                    if (
                        other.name.strip().lower() == new_name.strip().lower()
                        and other.category.strip().lower() == new_category.strip().lower()
                    ):
                        raise DuplicateProductException(
                            f"'{new_name}' in category '{new_category}'"
                        )

            # Apply partial updates
            if update_data.name is not None:
                existing.name = update_data.name
            if update_data.description is not None:
                existing.description = update_data.description
            if update_data.price is not None:
                existing.price = float(update_data.price)
            if update_data.stock_quantity is not None:
                existing.stock_quantity = int(update_data.stock_quantity)
            if update_data.category is not None:
                existing.category = update_data.category
            if update_data.status is not None:
                existing.status = (
                    update_data.status
                    if isinstance(update_data.status, ProductStatus)
                    else ProductStatus(update_data.status)
                )

            existing.updated_at = datetime.now(timezone.utc)
            return existing

    def delete_product(self, product_id: int) -> None:
        """Delete a product by ID from in-memory storage."""
        with self._lock:
            if product_id not in self._products:
                raise ProductNotFoundException(product_id)
            del self._products[product_id]

    def total_count(self) -> int:
        """Return total number of stored products."""
        with self._lock:
            return len(self._products)

    def clear(self) -> None:
        """Clear all stored products (useful for isolated testing)."""
        with self._lock:
            self._products.clear()
            self._id_counter = 0


# Singleton service instance
product_service = ProductService()
