"""Comprehensive automated test suite for ShopEase Product Service.

Covers all Task 4, Task 5, Task 6, and Task 11 requirements.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.product_service import product_service

client = TestClient(app)


def setup_function():
    """Reset the in-memory product store before each test."""
    product_service.clear()


def test_health_check():
    """Verify health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_scenario_1_create_product_valid():
    """Scenario 1: Create a product using valid information (201 Created)."""
    payload = {
        "name": "Sony WH-1000XM5",
        "description": "Wireless Noise Canceling Headphones",
        "price": 399.99,
        "stock_quantity": 45,
        "category": "Electronics",
        "status": "Active",
    }
    response = client.post("/api/products/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == payload["name"]
    assert data["price"] == payload["price"]
    assert data["stock_quantity"] == payload["stock_quantity"]
    assert data["category"] == payload["category"]
    assert data["status"] == "Active"
    assert "created_at" in data
    assert "updated_at" in data


def test_scenario_2_create_product_empty_name():
    """Scenario 2: Create a product with an empty name (422 Validation Error)."""
    payload = {
        "name": "   ",
        "description": "Test description",
        "price": 49.99,
        "stock_quantity": 10,
        "category": "Electronics",
        "status": "Active",
    }
    response = client.post("/api/products/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "VALIDATION_ERROR"


def test_scenario_3_create_product_negative_price():
    """Scenario 3: Create a product with a negative price (422 Validation Error)."""
    payload = {
        "name": "Gaming Mouse",
        "price": -15.00,
        "stock_quantity": 10,
        "category": "Electronics",
        "status": "Active",
    }
    response = client.post("/api/products/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "VALIDATION_ERROR"


def test_scenario_3b_create_product_zero_price():
    """Scenario 3b: Create a product with zero price (422 Validation Error)."""
    payload = {
        "name": "Free Sample",
        "price": 0.00,
        "stock_quantity": 10,
        "category": "Electronics",
        "status": "Active",
    }
    response = client.post("/api/products/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "VALIDATION_ERROR"


def test_scenario_4_create_product_negative_stock():
    """Scenario 4: Create a product with negative stock (422 Validation Error)."""
    payload = {
        "name": "Mechanical Keyboard",
        "price": 89.99,
        "stock_quantity": -5,
        "category": "Electronics",
        "status": "Active",
    }
    response = client.post("/api/products/", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "VALIDATION_ERROR"


def test_scenario_5_retrieve_all_products():
    """Scenario 5: Retrieve all products (200 OK, empty list and populated)."""
    # Empty store test
    empty_res = client.get("/api/products/")
    assert empty_res.status_code == 200
    assert empty_res.json() == []

    # Populate 2 products
    client.post(
        "/api/products/",
        json={"name": "Product A", "price": 10.0, "stock_quantity": 5, "category": "Home"},
    )
    client.post(
        "/api/products/",
        json={"name": "Product B", "price": 20.0, "stock_quantity": 8, "category": "Home"},
    )

    populated_res = client.get("/api/products/")
    assert populated_res.status_code == 200
    assert len(populated_res.json()) == 2


def test_scenario_6_retrieve_product_valid_id():
    """Scenario 6: Retrieve a product using a valid ID (200 OK)."""
    create_res = client.post(
        "/api/products/",
        json={"name": "Logitech MX Master 3S", "price": 99.99, "stock_quantity": 25, "category": "Electronics"},
    )
    product_id = create_res.json()["id"]

    get_res = client.get(f"/api/products/{product_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == product_id
    assert data["name"] == "Logitech MX Master 3S"


def test_scenario_7_retrieve_product_invalid_id():
    """Scenario 7: Retrieve a product using an invalid / non-existent ID (404 Not Found)."""
    response = client.get("/api/products/9999")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "PRODUCT_NOT_FOUND"


def test_scenario_8_update_existing_product():
    """Scenario 8: Update an existing product (200 OK)."""
    create_res = client.post(
        "/api/products/",
        json={"name": "Smart Watch Series 7", "price": 299.99, "stock_quantity": 15, "category": "Wearables"},
    )
    product_id = create_res.json()["id"]

    update_payload = {"price": 249.99, "stock_quantity": 20, "description": "Discounted model"}
    update_res = client.put(f"/api/products/{product_id}", json=update_payload)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["price"] == 249.99
    assert data["stock_quantity"] == 20
    assert data["description"] == "Discounted model"
    assert data["name"] == "Smart Watch Series 7"  # Unchanged field retained


def test_scenario_9_and_10_delete_and_retrieve_deleted():
    """Scenario 9 & 10: Delete an existing product (204 No Content) and verify 404 on retrieval."""
    create_res = client.post(
        "/api/products/",
        json={"name": "Temporary Item", "price": 12.50, "stock_quantity": 3, "category": "Miscellaneous"},
    )
    product_id = create_res.json()["id"]

    # Delete (Scenario 9)
    del_res = client.delete(f"/api/products/{product_id}")
    assert del_res.status_code == 204

    # Retrieve deleted product (Scenario 10)
    get_res = client.get(f"/api/products/{product_id}")
    assert get_res.status_code == 404


def test_scenario_11_category_filtering():
    """Scenario 11: Test category filtering."""
    client.post(
        "/api/products/",
        json={"name": "Laptop", "price": 1199.0, "stock_quantity": 10, "category": "Computers"},
    )
    client.post(
        "/api/products/",
        json={"name": "Cotton T-Shirt", "price": 19.99, "stock_quantity": 50, "category": "Apparel"},
    )
    client.post(
        "/api/products/",
        json={"name": "Denim Jeans", "price": 49.99, "stock_quantity": 30, "category": "Apparel"},
    )

    apparel_res = client.get("/api/products/?category=Apparel")
    assert apparel_res.status_code == 200
    items = apparel_res.json()
    assert len(items) == 2
    assert all(item["category"] == "Apparel" for item in items)


def test_scenario_12_pagination():
    """Scenario 12: Test pagination (skip & limit)."""
    for i in range(1, 11):
        client.post(
            "/api/products/",
            json={"name": f"Product Item {i}", "price": float(10 * i), "stock_quantity": i, "category": "General"},
        )

    # First page: limit 3
    page1 = client.get("/api/products/?skip=0&limit=3")
    assert page1.status_code == 200
    items1 = page1.json()
    assert len(items1) == 3
    assert items1[0]["id"] == 1
    assert items1[2]["id"] == 3

    # Second page: skip 3, limit 3
    page2 = client.get("/api/products/?skip=3&limit=3")
    assert page2.status_code == 200
    items2 = page2.json()
    assert len(items2) == 3
    assert items2[0]["id"] == 4
    assert items2[2]["id"] == 6


def test_duplicate_product_rejection():
    """Test duplicate detection raises 400 Bad Request."""
    client.post(
        "/api/products/",
        json={"name": "Echo Dot", "price": 49.99, "stock_quantity": 100, "category": "Smart Home"},
    )
    duplicate_res = client.post(
        "/api/products/",
        json={"name": "Echo Dot", "price": 49.99, "stock_quantity": 100, "category": "Smart Home"},
    )
    assert duplicate_res.status_code == 400
    data = duplicate_res.json()
    assert data["success"] is False
    assert data["error"] == "DUPLICATE_PRODUCT"


if __name__ == "__main__":
    import pytest
    import sys
    sys.exit(pytest.main(["-v", __file__]))
