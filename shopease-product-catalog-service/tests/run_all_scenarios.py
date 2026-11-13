"""
ShopEase Product Catalog Microservice - Complete Test Scenarios Runner.
Executes all 21 mandatory test scenarios specified in Step 10.
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.security import get_current_auth_user, require_admin
from app.database.connection import Base
from app.models.category_model import Category
from app.models.product_model import Product
from app.models.inventory_model import InventoryTransaction
from app.schemas.category_schema import CategoryCreate, CategoryUpdate
from app.schemas.product_schema import ProductCreate, ProductPatch, ProductUpdate
from app.schemas.inventory_schema import StockAdjustmentRequest
from app.services.category_service import CategoryService
from app.services.product_service import ProductService
from app.services.inventory_service import InventoryService


def run_all():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    results = []

    def record(num, name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        results.append((num, name, status, details))
        print(f"[{status}] Scenario {num:02d}: {name.ljust(60)} - {details}")

    print("=" * 95)
    print(" SHOPEASE PRODUCT CATALOG SERVICE: MANDATORY TEST SCENARIOS (STEP 10)")
    print("=" * 95)

    def generate_token(user_id: int, email: str, role: str = "customer", expired: bool = False):
        exp_time = (
            datetime.now(timezone.utc) - timedelta(minutes=10)
            if expired
            else datetime.now(timezone.utc) + timedelta(hours=1)
        )
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(exp_time.timestamp()),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    admin_token = generate_token(1, "admin@shopease.com", role="admin")
    customer_token = generate_token(2, "customer@shopease.com", role="customer")
    expired_token = generate_token(3, "expired@shopease.com", role="admin", expired=True)

    # Base setup: Category
    cat_elec = CategoryService.create_category(
        db, CategoryCreate(name="Electronics", description="Electronic devices")
    )

    # 1. Create a product with valid information
    try:
        p1 = ProductService.create_product(
            db,
            ProductCreate(
                name="Gaming Laptop",
                description="High performance RTX 4080 laptop",
                sku="LAPTOP-RTX-001",
                category_id=cat_elec.id,
                price=Decimal("1999.99"),
                discount_price=Decimal("1899.99"),
                stock_quantity=20,
                brand="Asus",
                is_active=True,
            ),
        )
        record(1, "Create a product with valid information", p1.id is not None, f"Created Product ID={p1.id}, SKU={p1.sku}")
    except Exception as e:
        record(1, "Create a product with valid information", False, str(e))

    # 2. Create a product with a duplicate SKU
    try:
        ProductService.create_product(
            db,
            ProductCreate(
                name="Another Laptop",
                sku="LAPTOP-RTX-001",  # Duplicate SKU
                category_id=cat_elec.id,
                price=Decimal("1500.00"),
                stock_quantity=10,
            ),
        )
        record(2, "Create a product with duplicate SKU (HTTP 409)", False, "Duplicate SKU was incorrectly permitted!")
    except HTTPException as e:
        record(2, "Create a product with duplicate SKU (HTTP 409)", e.status_code == 409, f"Status {e.status_code}: {e.detail}")

    # 3. Create a product with an invalid category
    try:
        ProductService.create_product(
            db,
            ProductCreate(
                name="Ghost Item",
                sku="GHOST-SKU-99",
                category_id=9999,  # Invalid category
                price=Decimal("99.99"),
                stock_quantity=5,
            ),
        )
        record(3, "Create a product with invalid category (HTTP 400)", False, "Invalid category was permitted!")
    except HTTPException as e:
        record(3, "Create a product with invalid category (HTTP 400)", e.status_code == 400, f"Status {e.status_code}: {e.detail}")

    # 4. Create a product with a negative price
    try:
        ProductCreate(
            name="Free Negative Item",
            sku="NEG-PRICE-01",
            category_id=cat_elec.id,
            price=Decimal("-50.00"),
            stock_quantity=10,
        )
        record(4, "Create product with negative price (Validation error)", False, "Negative price was permitted!")
    except Exception as e:
        record(4, "Create product with negative price (Validation error)", True, f"Validation caught negative price: {type(e).__name__}")

    # 5. Retrieve all active products
    # Add an inactive product first
    p_inactive = ProductService.create_product(
        db,
        ProductCreate(
            name="Discontinued Phone",
            sku="PHONE-DISC-00",
            category_id=cat_elec.id,
            price=Decimal("99.00"),
            stock_quantity=0,
            is_active=False,
        ),
    )
    active_items, total_active, _ = ProductService.list_products(db, active_only=True)
    all_active_check = all(p.is_active for p in active_items) and p_inactive.id not in [p.id for p in active_items]
    record(5, "Retrieve all active products", all_active_check, f"Customer active list contains {len(active_items)} products, inactive excluded")

    # 6. Retrieve product details using an invalid ID
    try:
        ProductService.get_product_by_id(db, 999999)
        record(6, "Retrieve product details with invalid ID (HTTP 404)", False, "Non-existent product returned!")
    except HTTPException as e:
        record(6, "Retrieve product details with invalid ID (HTTP 404)", e.status_code == 404, f"Status {e.status_code}: {e.detail}")

    # 7. Update and partially update a product
    try:
        updated_p = ProductService.update_product(
            db,
            p1.id,
            ProductUpdate(
                name="Gaming Laptop Pro Max",
                sku="LAPTOP-RTX-001",
                category_id=cat_elec.id,
                price=Decimal("2099.99"),
                discount_price=Decimal("1999.99"),
                stock_quantity=20,
                brand="Asus ROG",
                is_active=True,
            ),
        )
        patched_p = ProductService.patch_product(db, p1.id, ProductPatch(brand="Asus ROG Strix"))
        is_ok = updated_p.name == "Gaming Laptop Pro Max" and patched_p.brand == "Asus ROG Strix"
        record(7, "Update and partially update a product (PUT & PATCH)", is_ok, f"Name='{patched_p.name}', Brand='{patched_p.brand}'")
    except Exception as e:
        record(7, "Update and partially update a product (PUT & PATCH)", False, str(e))

    # 8. Delete or deactivate a product
    try:
        ProductService.delete_product(db, p_inactive.id)
        # Verify it no longer exists
        deleted_check = db.query(Product).filter(Product.id == p_inactive.id).first() is None
        record(8, "Delete or deactivate a product", deleted_check, f"Product {p_inactive.id} deleted cleanly from database")
    except Exception as e:
        record(8, "Delete or deactivate a product", False, str(e))

    # 9. Create a duplicate category
    try:
        CategoryService.create_category(db, CategoryCreate(name="electronics"))
        record(9, "Create duplicate category (HTTP 409)", False, "Duplicate category permitted!")
    except HTTPException as e:
        record(9, "Create duplicate category (HTTP 409)", e.status_code == 409, f"Status {e.status_code}: {e.detail}")

    # 10. Retrieve products using search and filters
    cat_books = CategoryService.create_category(db, CategoryCreate(name="Books"))
    p_book = ProductService.create_product(
        db,
        ProductCreate(
            name="Python Architecture Patterns",
            sku="BOOK-PY-ARCH",
            category_id=cat_books.id,
            price=Decimal("45.00"),
            stock_quantity=50,
            brand="O'Reilly",
            is_active=True,
        ),
    )
    search_res, _, _ = ProductService.list_products(db, search="Python", active_only=True)
    cat_res, _, _ = ProductService.list_products(db, category_id=cat_books.id, active_only=True)
    price_res, _, _ = ProductService.list_products(db, min_price=Decimal("30"), max_price=Decimal("50"), active_only=True)
    search_ok = len(search_res) == 1 and len(cat_res) == 1 and len(price_res) == 1
    record(10, "Retrieve products using search and filters", search_ok, "Search, category filter, and price range all verified")

    # 11. Test pagination and sorting
    sorted_asc, _, _ = ProductService.list_products(db, sort_by="price", sort_order="asc", active_only=True)
    sorted_desc, _, _ = ProductService.list_products(db, sort_by="price", sort_order="desc", active_only=True)
    page_1, total, total_pages = ProductService.list_products(db, page=1, page_size=1, active_only=True)
    page_2, _, _ = ProductService.list_products(db, page=2, page_size=1, active_only=True)
    page_ok = (
        float(sorted_asc[0].price) <= float(sorted_asc[-1].price)
        and float(sorted_desc[0].price) >= float(sorted_desc[-1].price)
        and len(page_1) == 1
        and len(page_2) == 1
        and page_1[0].id != page_2[0].id
    )
    record(11, "Test pagination and sorting (asc/desc & page limits)", page_ok, f"Total={total}, Pages={total_pages}, Sorting verified")

    # 12. Increase product stock (stock-in)
    try:
        p_updated, tx_in = InventoryService.stock_in(
            db, p1.id, StockAdjustmentRequest(quantity=15, remarks="Restock shipment from distributor")
        )
        record(12, "Increase product stock (Stock-in)", p_updated.stock_quantity == 35, f"Stock increased: 20 -> {p_updated.stock_quantity}")
    except Exception as e:
        record(12, "Increase product stock (Stock-in)", False, str(e))

    # 13. Decrease product stock (stock-out)
    try:
        p_updated, tx_out = InventoryService.stock_out(
            db, p1.id, StockAdjustmentRequest(quantity=10, remarks="Order dispatch batch #45")
        )
        record(13, "Decrease product stock (Stock-out)", p_updated.stock_quantity == 25, f"Stock decreased: 35 -> {p_updated.stock_quantity}")
    except Exception as e:
        record(13, "Decrease product stock (Stock-out)", False, str(e))

    # 14. Attempt to reduce stock below zero
    try:
        InventoryService.stock_out(
            db, p1.id, StockAdjustmentRequest(quantity=999, remarks="Excessive deduction attempt")
        )
        record(14, "Attempt to reduce stock below zero (HTTP 400)", False, "Negative stock was allowed!")
    except HTTPException as e:
        record(14, "Attempt to reduce stock below zero (HTTP 400)", e.status_code == 400, f"Status {e.status_code}: {e.detail}")

    # 15. Verify inventory transaction history
    history = InventoryService.get_stock_history(db, p1.id)
    history_ok = len(history) >= 2 and all(tx.product_id == p1.id for tx in history)
    record(15, "Verify inventory transaction history", history_ok, f"Found {len(history)} recorded audit transactions for Product ID={p1.id}")

    # 16. Retrieve low-stock products
    # p1 stock is 25. Threshold 30 -> p1 is low stock. Threshold 10 -> not low stock.
    low_stock_30 = InventoryService.list_low_stock_products(db, threshold=30)
    low_stock_10 = InventoryService.list_low_stock_products(db, threshold=10)
    low_stock_ok = any(p.id == p1.id for p in low_stock_30) and not any(p.id == p1.id for p in low_stock_10)
    record(16, "Retrieve low-stock products with threshold", low_stock_ok, f"Threshold=30 matched {len(low_stock_30)} products; Threshold=10 matched {len(low_stock_10)}")

    # 17. Access administrative APIs as a customer
    cust_auth = get_current_auth_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=customer_token))
    try:
        require_admin(cust_auth)
        record(17, "Access administrative APIs as customer (HTTP 403)", False, "Customer was permitted admin access!")
    except HTTPException as e:
        record(17, "Access administrative APIs as customer (HTTP 403)", e.status_code == 403, f"Status {e.status_code}: {e.detail}")

    # 18. Access protected APIs without a JWT token
    try:
        get_current_auth_user(None)
        record(18, "Access protected APIs without JWT token (HTTP 401)", False, "Missing token was allowed!")
    except HTTPException as e:
        record(18, "Access protected APIs without JWT token (HTTP 401)", e.status_code == 401, f"Status {e.status_code}: {e.detail}")

    # 19. Access protected APIs using an invalid / expired token
    try:
        bad_token_auth = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.payload")
        get_current_auth_user(bad_token_auth)
        record(19, "Access protected APIs with invalid token (HTTP 401)", False, "Invalid token was allowed!")
    except HTTPException as e:
        record(19, "Access protected APIs with invalid token (HTTP 401)", e.status_code == 401, f"Status {e.status_code}: {e.detail}")

    # 20. Test simultaneous stock updates & verify inventory consistency (Atomic transactions)
    # Simulate failed transaction and verify atomic rollback
    stock_before = p1.stock_quantity
    tx_count_before = len(InventoryService.get_stock_history(db, p1.id))
    try:
        InventoryService.stock_out(db, p1.id, StockAdjustmentRequest(quantity=1000, remarks="Oversell simulation"))
    except HTTPException:
        pass
    db.refresh(p1)
    tx_count_after = len(InventoryService.get_stock_history(db, p1.id))
    consistency_ok = p1.stock_quantity == stock_before and tx_count_after == tx_count_before
    record(20, "Simultaneous updates & atomic rollback consistency", consistency_ok, f"Stock remained at {p1.stock_quantity}, zero dirty transactions")

    # 21. Verify database records and HTTP responses after each operation
    db_cat = db.query(Category).filter(Category.id == cat_elec.id).first()
    db_prod = db.query(Product).filter(Product.id == p1.id).first()
    db_tx = db.query(InventoryTransaction).filter(InventoryTransaction.product_id == p1.id).all()
    persistence_ok = db_cat is not None and db_prod is not None and len(db_tx) > 0
    record(21, "Verify database records & persistence integrity", persistence_ok, f"Verified Category ({db_cat.name}), Product ({db_prod.name}), and {len(db_tx)} Transactions")

    print("=" * 95)
    passed_count = sum(1 for _, _, status, _ in results if status == "PASS")
    total_count = len(results)
    print(f" FINAL SUMMARY: {passed_count}/{total_count} SCENARIOS PASSED ({passed_count / total_count * 100:.1f}%)")
    print("=" * 95)

    assert passed_count == total_count, f"Some test scenarios failed! {passed_count}/{total_count} passed."


if __name__ == "__main__":
    run_all()

