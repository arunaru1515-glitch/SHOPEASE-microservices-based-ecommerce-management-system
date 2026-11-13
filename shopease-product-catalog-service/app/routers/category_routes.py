from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_optional_auth_user, require_admin
from app.database.connection import get_db
from app.schemas.category_schema import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category (Admin only)",
)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Creates a new category. Only administrators can perform this operation.
    Enforces uniqueness on category name.
    """
    category = CategoryService.create_category(db, category_in)
    return category


@router.get(
    "/",
    response_model=List[CategoryResponse],
    summary="List all categories",
)
def list_categories(
    is_active: Optional[bool] = Query(None, description="Filter categories by active status"),
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_auth_user),
):
    """
    Lists categories.
    Customers and anonymous visitors see active categories by default.
    Administrators can see both active and inactive categories.
    """
    is_admin = current_user is not None and current_user.get("role") == "admin"
    if not is_admin and is_active is None:
        # Default customers to active categories only
        is_active = True

    categories = CategoryService.list_categories(db, is_active=is_active)
    # Populate products_count
    for cat in categories:
        cat.products_count = len(cat.products)
    return categories


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category details by ID",
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_auth_user),
):
    """
    Retrieves details for a specific category.
    Non-admins cannot view deactivated categories.
    """
    is_admin = current_user is not None and current_user.get("role") == "admin"
    category = CategoryService.get_category_by_id(
        db, category_id, active_only=not is_admin
    )
    category.products_count = len(category.products)
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category (Admin only)",
)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Updates category information. Only administrators can update categories.
    """
    category = CategoryService.update_category(db, category_id, category_in)
    category.products_count = len(category.products)
    return category


@router.delete(
    "/{category_id}",
    summary="Delete a category (Admin only)",
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """
    Deletes a category. Only administrators can delete categories.
    Prevents deletion if products are attached to the category.
    """
    CategoryService.delete_category(db, category_id)
    return {"message": f"Category with ID {category_id} successfully deleted."}

