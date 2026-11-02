import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import get_settings
from app.exceptions import (
    DuplicateProductException,
    InvalidProductDataException,
    ProductAppException,
    ProductNotFoundException,
)
from app.routers import product_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("shopease-product-service")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ShopEase Microservices-Based E-Commerce Management System — Product Service API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for cross-origin frontend support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Exception Handlers (Task 6: Proper Exception Handling)
# ---------------------------------------------------------

@app.exception_handler(ProductNotFoundException)
async def product_not_found_handler(request: Request, exc: ProductNotFoundException):
    """Handle 404 Not Found errors for products."""
    logger.warning("Product not found: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error": "PRODUCT_NOT_FOUND",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(DuplicateProductException)
async def duplicate_product_handler(request: Request, exc: DuplicateProductException):
    """Handle 400 Bad Request for duplicate product attributes."""
    logger.warning("Duplicate product conflict: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": "DUPLICATE_PRODUCT",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(InvalidProductDataException)
async def invalid_product_data_handler(request: Request, exc: InvalidProductDataException):
    """Handle 400 Bad Request for invalid product information."""
    logger.warning("Invalid product data: %s", exc.message)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": "INVALID_PRODUCT_DATA",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle 422 Unprocessable Entity for schema validation failures."""
    errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        errors.append(
            {
                "field": field or "body",
                "message": err.get("msg", "Invalid input"),
                "type": err.get("type", "value_error"),
            }
        )
    logger.warning("Request validation failed on %s: %s", request.url.path, errors)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "Input validation failed. Please check the supplied fields.",
            "details": errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle standard FastAPI HTTPExceptions."""
    logger.warning("HTTPException %s on %s: %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP_ERROR",
            "message": str(exc.detail),
            "details": None,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server Errors."""
    logger.error("Unhandled exception on %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred. Please try again later.",
            "details": None,
        },
    )


# ---------------------------------------------------------
# Routers Registration (Task 2 & 4)
# ---------------------------------------------------------

app.include_router(product_router, prefix=settings.api_prefix, tags=["Products"])


# ---------------------------------------------------------
# Health & Root Endpoints
# ---------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    tags=["Health"],
    summary="Service Health Check",
    description="Check operational health status of the Product Service.",
)
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.app_env == "development"),
    )
