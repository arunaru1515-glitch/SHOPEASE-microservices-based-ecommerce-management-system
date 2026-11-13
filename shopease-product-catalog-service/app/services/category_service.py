from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.category_model import Category
from app.models.product_model import Product
from app.schemas.category_schema import CategoryCreate, CategoryUpdate


class CategoryService:
    @staticmethod
    def create_category(db: Session, category_in: CategoryCreate) -> Category:
        """
        Creates a new product category.
        Enforces uniqueness on category name.
        """
        normalized_name = category_in.name.strip()
        existing = (
            db.query(Category)
            .filter(Category.name.ilike(normalized_name))
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{normalized_name}' already exists.",
            )

        new_category = Category(
            name=normalized_name,
            description=category_in.description.strip() if category_in.description else None,
            is_active=category_in.is_active,
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return new_category

    @staticmethod
    def get_category_by_id(
        db: Session, category_id: int, active_only: bool = False
    ) -> Category:
        """
        Retrieves a category by ID.
        If active_only is True, inactive categories return 404.
        """
        query = db.query(Category).filter(Category.id == category_id)
        if active_only:
            query = query.filter(Category.is_active.is_(True))

        category = query.first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found.",
            )
        return category

    @staticmethod
    def list_categories(
        db: Session, is_active: Optional[bool] = None
    ) -> List[Category]:
        """
        Lists categories, optionally filtering by active status.
        """
        query = db.query(Category)
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)

        return query.order_by(Category.name.asc()).all()

    @staticmethod
    def update_category(
        db: Session, category_id: int, category_in: CategoryUpdate
    ) -> Category:
        """
        Updates an existing category.
        Ensures unique name across other categories.
        """
        category = CategoryService.get_category_by_id(db, category_id)

        if category_in.name is not None:
            normalized_name = category_in.name.strip()
            conflict = (
                db.query(Category)
                .filter(Category.name.ilike(normalized_name), Category.id != category_id)
                .first()
            )
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category with name '{normalized_name}' already exists.",
                )
            category.name = normalized_name

        if category_in.description is not None:
            category.description = category_in.description.strip() if category_in.description else None

        if category_in.is_active is not None:
            category.is_active = category_in.is_active

        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete_category(db: Session, category_id: int) -> None:
        """
        Deletes a category if it does not contain products.
        If products are attached, prevents deletion and returns HTTP 400.
        """
        category = CategoryService.get_category_by_id(db, category_id)

        products_count = (
            db.query(Product)
            .filter(Product.category_id == category_id)
            .count()
        )
        if products_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot delete category '{category.name}' because it contains "
                    f"{products_count} associated product(s). Please delete or reassign "
                    f"these products first."
                ),
            )

        db.delete(category)
        db.commit()

