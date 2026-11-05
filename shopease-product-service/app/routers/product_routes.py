from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Query, Response, status

from app.exceptions import ProductNotFoundException
from app.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StandardErrorResponse,
)
from app.services.product_service import product_service

router = APIRouter()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Accepts product details, validates fields, and stores in-memory. Returns HTTP 201 on success.",
    responses={
        201: {"description": "Product successfully created", "model": ProductResponse},
        400: {"description": "Bad Request or Duplicate Product", "model": StandardErrorResponse},
        422: {"description": "Validation Error", "model": StandardErrorResponse},
    },
)
def create_product(product_in: ProductCreate):
    """Create a new product."""
    new_product = product_service.create_product(product_in)
    return new_product


@router.get(
    "/",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all products",
    description="Retrieve all available products. Supports optional category filtering and pagination (skip/limit).",
    responses={
        200: {"description": "List of products matching criteria", "model": List[ProductResponse]},
    },
)
def get_all_products(
    category: Optional[str] = Query(
        None,
        description="Filter products by category (case-insensitive)",
        examples=["Electronics"],
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip for pagination",
        examples=[0],
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of records to return",
        examples=[10],
    ),
):
    """Retrieve all products with filtering and pagination."""
    return product_service.get_all_products(category=category, skip=skip, limit=limit)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve product by ID",
    description="Retrieve details of a single product using its unique ID. Returns 404 if not found.",
    responses={
        200: {"description": "Product found and returned", "model": ProductResponse},
        404: {"description": "Product not found", "model": StandardErrorResponse},
        422: {"description": "Invalid product ID format", "model": StandardErrorResponse},
    },
)
def get_product_by_id(
    product_id: int = Path(..., gt=0, description="The positive integer ID of the product", examples=[1]),
):
    """Retrieve single product by ID."""
    return product_service.get_product_by_id(product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing product",
    description="Update fields of an existing product. Returns updated product or HTTP 404 if not found.",
    responses={
        200: {"description": "Product updated successfully", "model": ProductResponse},
        400: {"description": "Invalid update data", "model": StandardErrorResponse},
        404: {"description": "Product not found", "model": StandardErrorResponse},
        422: {"description": "Validation error", "model": StandardErrorResponse},
    },
)
def update_product(
    product_id: int = Path(..., gt=0, description="The positive integer ID of the product", examples=[1]),
    product_update: ProductUpdate = ...,
):
    """Update existing product details."""
    return product_service.update_product(product_id, product_update)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    description="Deletes a product by ID. Returns HTTP 204 No Content on success, or HTTP 404 if not found.",
    responses={
        204: {"description": "Product deleted successfully"},
        404: {"description": "Product not found", "model": StandardErrorResponse},
        422: {"description": "Invalid product ID", "model": StandardErrorResponse},
    },
)
def delete_product(
    product_id: int = Path(..., gt=0, description="The positive integer ID of the product", examples=[1]),
):
    """Delete a product by ID."""
    product_service.delete_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
