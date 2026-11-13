from decimal import Decimal
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_optional_auth_user, require_admin
from app.database.connection import get_db
from app.schemas.product_schema import (
    ProductCreate,
    ProductListResponse,
    ProductPatch,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/products", tags=["Products"])


def _to_product_response(product) -> ProductResponse:
    """Helper to attach category_name to product response."""
    res = ProductResponse.model_validate(product)
    if product.category:
        res.category_name = product.category.name
    return res


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin only)",
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Creates a new product in the catalog.
    Only administrators can create products.
    """
    product = ProductService.create_product(db, product_in)
    return _to_product_response(product)


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List products with search, filter, and pagination",
)
def list_products(
    search: Optional[str] = Query(None, description="Search by product name, SKU, or brand"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability (True/False)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (Admin only)"),
    sort_by: str = Query("created_at", description="Sort field: price, name, created_at, stock_quantity"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_auth_user),
):
    """
    Retrieves products with query parameters for search, filtering, sorting, and pagination.
    Customers and anonymous visitors can only browse active products.
    """
    is_admin = current_user is not None and current_user.get("role") == "admin"
    active_only = not is_admin

    # Validate sort parameters
    valid_sort_fields = {"price", "name", "created_at", "stock_quantity"}
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"

    if sort_order.lower() not in {"asc", "desc"}:
        sort_order = "desc"

    items, total_items, total_pages = ProductService.list_products(
        db=db,
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        is_active=is_active if is_admin else None,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        active_only=active_only,
    )

    response_items = [_to_product_response(item) for item in items]
    return ProductListResponse(
        items=response_items,
        total_items=total_items,
        total_pages=total_pages,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Retrieve product details by ID",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_auth_user),
):
    """
    Retrieves details for a specific product.
    Customers cannot view inactive products.
    """
    is_admin = current_user is not None and current_user.get("role") == "admin"
    product = ProductService.get_product_by_id(db, product_id, active_only=not is_admin)
    return _to_product_response(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details (Admin only)",
)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Replaces all product details. Only administrators can perform this operation.
    """
    product = ProductService.update_product(db, product_id, product_in)
    return _to_product_response(product)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Partially update a product (Admin only)",
)
def patch_product(
    product_id: int,
    product_in: ProductPatch,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Partially updates specific fields of a product. Only administrators can perform this operation.
    """
    product = ProductService.patch_product(db, product_id, product_in)
    return _to_product_response(product)


@router.delete(
    "/{product_id}",
    summary="Delete a product (Admin only)",
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Deletes a product by ID. Only administrators can perform this operation.
    """
    ProductService.delete_product(db, product_id)
    return {"message": f"Product with ID {product_id} successfully deleted."}

