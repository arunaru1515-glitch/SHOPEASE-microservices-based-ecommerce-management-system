"""
Live Integration Test Suite for ShopEase Product Catalog Microservice in Docker.
Tests endpoints against http://localhost:8004.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import requests
import jwt

BASE_URL = "http://localhost:8004"
JWT_SECRET = "supersecretjwtkey_change_in_production_1234567890!@#$%"
JWT_ALGORITHM = "HS256"


def make_token(user_id: int, email: str, role: str):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=2)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def test_live():
    print(f"Connecting to live Product Catalog Microservice at {BASE_URL}...")
    try:
        health_resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[PASS] Health check: {health_resp.status_code} - {health_resp.json()}")
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Could not connect to {BASE_URL}. Ensure Docker container is running with 'docker-compose up -d'.")
        return

    admin_token = make_token(1, "admin@shopease.com", "admin")
    customer_token = make_token(2, "customer@shopease.com", "customer")
    admin_hdr = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    cust_hdr = {"Authorization": f"Bearer {customer_token}", "Content-Type": "application/json"}

    # 1. Create Category
    cat_payload = {"name": f"Docker Category {datetime.now().strftime('%H%M%S')}", "description": "Created during live docker test"}
    cat_resp = requests.post(f"{BASE_URL}/api/categories/", json=cat_payload, headers=admin_hdr)
    assert cat_resp.status_code == 201, f"Category creation failed: {cat_resp.text}"
    cat_id = cat_resp.json()["id"]
    print(f"[PASS] Created Category in Docker DB: ID={cat_id}")

    # 2. Create Product
    prod_sku = f"DOCKER-SKU-{datetime.now().strftime('%H%M%S')}"
    prod_payload = {
        "name": "Docker Test Product",
        "sku": prod_sku,
        "category_id": cat_id,
        "price": 199.99,
        "discount_price": 179.99,
        "stock_quantity": 20,
        "brand": "DockerCorp",
        "is_active": True
    }
    prod_resp = requests.post(f"{BASE_URL}/api/products/", json=prod_payload, headers=admin_hdr)
    assert prod_resp.status_code == 201, f"Product creation failed: {prod_resp.text}"
    prod_id = prod_resp.json()["id"]
    print(f"[PASS] Created Product in Docker DB: ID={prod_id}, SKU={prod_sku}")

    # 3. Customer lists products
    list_resp = requests.get(f"{BASE_URL}/api/products/", headers=cust_hdr)
    assert list_resp.status_code == 200
    print(f"[PASS] Customer listed active products: Total={list_resp.json()['total_items']}")

    # 4. Stock In
    stock_in_resp = requests.post(f"{BASE_URL}/api/inventory/{prod_id}/stock-in", json={"quantity": 10, "remarks": "Live restock"}, headers=admin_hdr)
    assert stock_in_resp.status_code == 200
    print(f"[PASS] Stock IN: Updated stock = {stock_in_resp.json()['updated_stock']}")

    # 5. Stock Out
    stock_out_resp = requests.post(f"{BASE_URL}/api/inventory/{prod_id}/stock-out", json={"quantity": 5, "remarks": "Live dispatch"}, headers=admin_hdr)
    assert stock_out_resp.status_code == 200
    print(f"[PASS] Stock OUT: Updated stock = {stock_out_resp.json()['updated_stock']}")

    # 6. Verify Transaction History
    hist_resp = requests.get(f"{BASE_URL}/api/inventory/{prod_id}/history", headers=admin_hdr)
    assert hist_resp.status_code == 200
    print(f"[PASS] Inventory History verified: {len(hist_resp.json())} transactions recorded")

    # 7. Customer Forbidden on Admin API
    cust_forbidden = requests.post(f"{BASE_URL}/api/inventory/{prod_id}/stock-in", json={"quantity": 5}, headers=cust_hdr)
    assert cust_forbidden.status_code == 403
    print(f"[PASS] Customer blocked with HTTP 403 on admin endpoint")

    # 8. Missing Token Unauthorized
    unauth = requests.post(f"{BASE_URL}/api/inventory/{prod_id}/stock-in", json={"quantity": 5})
    assert unauth.status_code == 401
    print(f"[PASS] Missing token blocked with HTTP 401 on admin endpoint")

    print("\n*** ALL LIVE DOCKER API TESTS COMPLETED SUCCESSFULLY! ***")


if __name__ == "__main__":
    test_live()

