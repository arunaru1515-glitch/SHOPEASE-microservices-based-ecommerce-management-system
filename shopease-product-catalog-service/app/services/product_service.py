import math
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.category_model import Category
from app.models.inventory_model import InventoryTransaction
from app.models.product_model import Product
from app.schemas.product_schema import ProductCreate, ProductPatch, ProductUpdate


class ProductService:
    @staticmethod
    def create_product(db: Session, product_in: ProductCreate) -> Product:
        """
        Creates a new product in the catalog.
        Validates category existence, SKU uniqueness, and positive pricing/stock.
        Records an initial inventory transaction if starting stock > 0.
        """
        # 1. Validate Category existence
        category = (
            db.query(Category)
            .filter(Category.id == product_in.category_id)
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {product_in.category_id} does not exist.",
            )

        # 2. Validate SKU uniqueness
        normalized_sku = product_in.sku.strip()
        existing_sku = (
            db.query(Product)
            .filter(Product.sku.ilike(normalized_sku))
            .first()
        )
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{normalized_sku}' already exists.",
            )

        # 3. Validate pricing and stock
        if product_in.price < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product price cannot be negative.",
            )
        if product_in.discount_price is not None and product_in.discount_price < Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discount price cannot be negative.",
            )
        if product_in.stock_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock quantity cannot be negative.",
            )

        new_product = Product(
            name=product_in.name.strip(),
            description=product_in.description.strip() if product_in.description else None,
            sku=normalized_sku,
            category_id=product_in.category_id,
            price=product_in.price,
            discount_price=product_in.discount_price,
            stock_quantity=product_in.stock_quantity,
            image_url=product_in.image_url.strip() if product_in.image_url else None,
            brand=product_in.brand.strip() if product_in.brand else None,
            is_active=product_in.is_active,
        )

        db.add(new_product)
        db.flush()  # Populates new_product.id

        # 4. Record initial stock transaction if stock > 0
        if product_in.stock_quantity > 0:
            initial_tx = InventoryTransaction(
                product_id=new_product.id,
                transaction_type="IN",
                quantity=product_in.stock_quantity,
                previous_stock=0,
                updated_stock=product_in.stock_quantity,
                remarks="Initial inventory intake on product creation",
            )
            db.add(initial_tx)

        db.commit()
        db.refresh(new_product)
        return new_product

    @staticmethod
    def get_product_by_id(
        db: Session, product_id: int, active_only: bool = False
    ) -> Product:
        """
        Retrieves a single product by ID.
        If active_only is True, inactive products raise HTTP 404.
        """
        query = db.query(Product).filter(Product.id == product_id)
        if active_only:
            query = query.filter(Product.is_active.is_(True))

        product = query.first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found.",
            )
        return product

    @staticmethod
    def list_products(
        db: Session,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock: Optional[bool] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
        active_only: bool = False,
    ) -> Tuple[List[Product], int, int]:
        """
        Searches, filters, sorts, and paginates products.
        Returns: (items, total_items, total_pages)
        """
        query = db.query(Product)

        # Enforce active products for customers
        if active_only:
            query = query.filter(Product.is_active.is_(True))
        elif is_active is not None:
            query = query.filter(Product.is_active == is_active)

        # Search by name or SKU
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.sku.ilike(search_pattern),
                    Product.brand.ilike(search_pattern),
                )
            )

        # Filter by category
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)

        # Filter by price range
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Filter by stock availability
        if in_stock is True:
            query = query.filter(Product.stock_quantity > 0)
        elif in_stock is False:
            query = query.filter(Product.stock_quantity == 0)

        # Sorting
        sort_column_map = {
            "price": Product.price,
            "name": Product.name,
            "created_at": Product.created_at,
            "stock_quantity": Product.stock_quantity,
        }
        sort_col = sort_column_map.get(sort_by, Product.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        total_items = query.count()
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total_items, total_pages

    @staticmethod
    def update_product(
        db: Session, product_id: int, product_in: ProductUpdate
    ) -> Product:
        """
        Updates all fields of an existing product.
        """
        product = ProductService.get_product_by_id(db, product_id)

        # Validate category if changed
        if product_in.category_id != product.category_id:
            cat = (
                db.query(Category)
                .filter(Category.id == product_in.category_id)
                .first()
            )
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with ID {product_in.category_id} does not exist.",
                )
            product.category_id = product_in.category_id

        # Validate SKU uniqueness if changed
        normalized_sku = product_in.sku.strip()
        if normalized_sku.lower() != product.sku.lower():
            conflict = (
                db.query(Product)
                .filter(Product.sku.ilike(normalized_sku), Product.id != product_id)
                .first()
            )
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with SKU '{normalized_sku}' already exists.",
                )
            product.sku = normalized_sku

        # Validate stock change & audit trail
        old_stock = product.stock_quantity
        if product_in.stock_quantity != old_stock:
            diff = product_in.stock_quantity - old_stock
            tx_type = "IN" if diff > 0 else "OUT"
            tx = InventoryTransaction(
                product_id=product.id,
                transaction_type=tx_type,
                quantity=abs(diff),
                previous_stock=old_stock,
                updated_stock=product_in.stock_quantity,
                remarks=f"Manual stock adjustment via PUT: {old_stock} -> {product_in.stock_quantity}",
            )
            db.add(tx)
            product.stock_quantity = product_in.stock_quantity

        product.name = product_in.name.strip()
        product.description = product_in.description.strip() if product_in.description else None
        product.price = product_in.price
        product.discount_price = product_in.discount_price
        product.image_url = product_in.image_url.strip() if product_in.image_url else None
        product.brand = product_in.brand.strip() if product_in.brand else None
        product.is_active = product_in.is_active

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def patch_product(
        db: Session, product_id: int, product_in: ProductPatch
    ) -> Product:
        """
        Partially updates specific fields of a product.
        """
        product = ProductService.get_product_by_id(db, product_id)

        if product_in.category_id is not None and product_in.category_id != product.category_id:
            cat = (
                db.query(Category)
                .filter(Category.id == product_in.category_id)
                .first()
            )
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with ID {product_in.category_id} does not exist.",
                )
            product.category_id = product_in.category_id

        if product_in.sku is not None:
            normalized_sku = product_in.sku.strip()
            if normalized_sku.lower() != product.sku.lower():
                conflict = (
                    db.query(Product)
                    .filter(Product.sku.ilike(normalized_sku), Product.id != product_id)
                    .first()
                )
                if conflict:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Product with SKU '{normalized_sku}' already exists.",
                    )
                product.sku = normalized_sku

        if product_in.name is not None:
            product.name = product_in.name.strip()
        if product_in.description is not None:
            product.description = product_in.description.strip() if product_in.description else None
        if product_in.price is not None:
            product.price = product_in.price
        if product_in.discount_price is not None:
            product.discount_price = product_in.discount_price
        if product_in.image_url is not None:
            product.image_url = product_in.image_url.strip() if product_in.image_url else None
        if product_in.brand is not None:
            product.brand = product_in.brand.strip() if product_in.brand else None
        if product_in.is_active is not None:
            product.is_active = product_in.is_active

        if product_in.stock_quantity is not None and product_in.stock_quantity != product.stock_quantity:
            old_stock = product.stock_quantity
            diff = product_in.stock_quantity - old_stock
            tx_type = "IN" if diff > 0 else "OUT"
            tx = InventoryTransaction(
                product_id=product.id,
                transaction_type=tx_type,
                quantity=abs(diff),
                previous_stock=old_stock,
                updated_stock=product_in.stock_quantity,
                remarks=f"Manual stock adjustment via PATCH: {old_stock} -> {product_in.stock_quantity}",
            )
            db.add(tx)
            product.stock_quantity = product_in.stock_quantity

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_product(db: Session, product_id: int) -> None:
        """
        Deletes a product by ID. Associated inventory transaction history
        is cascaded or deleted cleanly.
        """
        product = ProductService.get_product_by_id(db, product_id)
        db.delete(product)
        db.commit()

