class ProductAppException(Exception):
    """Base exception class for Product Service."""

    def __init__(self, message: str, status_code: int = 400, details: dict | list | None = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ProductNotFoundException(ProductAppException):
    """Raised when a product with the requested ID cannot be found."""

    def __init__(self, product_id: int):
        super().__init__(
            message=f"Product with ID {product_id} not found.",
            status_code=404,
            details={"product_id": product_id},
        )


class DuplicateProductException(ProductAppException):
    """Raised when attempting to create a product with duplicate unique attributes."""

    def __init__(self, identifier: str):
        super().__init__(
            message=f"Product '{identifier}' already exists.",
            status_code=400,
            details={"conflict": identifier},
        )


class InvalidProductDataException(ProductAppException):
    """Raised when product information fails business validation."""

    def __init__(self, message: str, details: dict | list | None = None):
        super().__init__(
            message=message,
            status_code=400,
            details=details,
        )
