"""End-to-end test script executed directly against the live Docker container.

Host URL: http://localhost:8003
Covers all 12 Task 11 test scenarios.
"""

import json
import sys
import requests

BASE_URL = "http://localhost:8003/api/products"


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_result(scenario_num: int, name: str, passed: bool, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"[Scenario {scenario_num:02d}] {name.ljust(45)} {status}")
    if details:
        print(f"             Details: {details}")


def run_all_docker_tests():
    print_header("TASK 11: LIVE DOCKER CONTAINER REST API VERIFICATION")
    print(f"Target Container URL: {BASE_URL}")

    # Check container health first
    try:
        health_res = requests.get("http://localhost:8003/health", timeout=5)
        if health_res.status_code == 200:
            print("Server Health Status: HEALTHY (200 OK)")
        else:
            print(f"Server Health check failed with code {health_res.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Docker container on http://localhost:8003: {e}")
        sys.exit(1)

    all_passed = True

    # -------------------------------------------------------------
    # Scenario 1: Create a product using valid information
    # -------------------------------------------------------------
    payload_valid = {
        "name": "Sony Wireless Headphones",
        "description": "High performance noise-canceling headphones",
        "price": 299.99,
        "stock_quantity": 40,
        "category": "Electronics",
        "status": "Active",
    }
    res1 = requests.post(f"{BASE_URL}/", json=payload_valid)
    scen1_pass = res1.status_code == 201 and res1.json().get("name") == payload_valid["name"]
    created_id_1 = res1.json().get("id") if scen1_pass else None
    print_result(1, "Create product with valid info", scen1_pass, f"Status: {res1.status_code}, ID: {created_id_1}")
    all_passed = all_passed and scen1_pass

    # -------------------------------------------------------------
    # Scenario 2: Create a product with an empty name
    # -------------------------------------------------------------
    payload_empty_name = {
        "name": "   ",
        "description": "Empty name test",
        "price": 49.99,
        "stock_quantity": 10,
        "category": "Electronics",
        "status": "Active",
    }
    res2 = requests.post(f"{BASE_URL}/", json=payload_empty_name)
    scen2_pass = res2.status_code == 422 and res2.json().get("error") == "VALIDATION_ERROR"
    print_result(2, "Create product with empty name", scen2_pass, f"Status: {res2.status_code} (Validation Error caught)")
    all_passed = all_passed and scen2_pass

    # -------------------------------------------------------------
    # Scenario 3: Create a product with a negative price
    # -------------------------------------------------------------
    payload_neg_price = {
        "name": "Invalid Price Item",
        "description": "Negative price test",
        "price": -15.50,
        "stock_quantity": 10,
        "category": "Electronics",
        "status": "Active",
    }
    res3 = requests.post(f"{BASE_URL}/", json=payload_neg_price)
    scen3_pass = res3.status_code == 422 and res3.json().get("error") == "VALIDATION_ERROR"
    print_result(3, "Create product with negative price", scen3_pass, f"Status: {res3.status_code} (Negative price rejected)")
    all_passed = all_passed and scen3_pass

    # -------------------------------------------------------------
    # Scenario 4: Create a product with negative stock
    # -------------------------------------------------------------
    payload_neg_stock = {
        "name": "Invalid Stock Item",
        "description": "Negative stock test",
        "price": 19.99,
        "stock_quantity": -20,
        "category": "Electronics",
        "status": "Active",
    }
    res4 = requests.post(f"{BASE_URL}/", json=payload_neg_stock)
    scen4_pass = res4.status_code == 422 and res4.json().get("error") == "VALIDATION_ERROR"
    print_result(4, "Create product with negative stock", scen4_pass, f"Status: {res4.status_code} (Negative stock rejected)")
    all_passed = all_passed and scen4_pass

    # -------------------------------------------------------------
    # Scenario 5: Retrieve all products
    # -------------------------------------------------------------
    res5 = requests.get(f"{BASE_URL}/")
    scen5_pass = res5.status_code == 200 and isinstance(res5.json(), list) and len(res5.json()) >= 1
    print_result(5, "Retrieve all products", scen5_pass, f"Status: {res5.status_code}, Count: {len(res5.json())}")
    all_passed = all_passed and scen5_pass

    # -------------------------------------------------------------
    # Scenario 6: Retrieve a product using a valid ID
    # -------------------------------------------------------------
    res6 = requests.get(f"{BASE_URL}/{created_id_1}")
    scen6_pass = res6.status_code == 200 and res6.json().get("id") == created_id_1
    print_result(6, "Retrieve product by valid ID", scen6_pass, f"Status: {res6.status_code}, Found: '{res6.json().get('name')}'")
    all_passed = all_passed and scen6_pass

    # -------------------------------------------------------------
    # Scenario 7: Retrieve a product using an invalid ID
    # -------------------------------------------------------------
    res7 = requests.get(f"{BASE_URL}/99999")
    scen7_pass = res7.status_code == 404 and res7.json().get("error") == "PRODUCT_NOT_FOUND"
    print_result(7, "Retrieve product by invalid ID", scen7_pass, f"Status: {res7.status_code} (404 Not Found returned)")
    all_passed = all_passed and scen7_pass

    # -------------------------------------------------------------
    # Scenario 8: Update an existing product
    # -------------------------------------------------------------
    update_payload = {
        "price": 249.99,
        "stock_quantity": 65,
        "description": "Updated active noise cancellation model",
    }
    res8 = requests.put(f"{BASE_URL}/{created_id_1}", json=update_payload)
    scen8_pass = (
        res8.status_code == 200
        and res8.json().get("price") == 249.99
        and res8.json().get("stock_quantity") == 65
        and res8.json().get("name") == payload_valid["name"]  # preserved
    )
    print_result(8, "Update an existing product", scen8_pass, f"Status: {res8.status_code}, Updated Price: $249.99")
    all_passed = all_passed and scen8_pass

    # -------------------------------------------------------------
    # Scenario 9: Delete an existing product
    # -------------------------------------------------------------
    res9 = requests.delete(f"{BASE_URL}/{created_id_1}")
    scen9_pass = res9.status_code == 204
    print_result(9, "Delete an existing product", scen9_pass, f"Status: {res9.status_code} (204 No Content)")
    all_passed = all_passed and scen9_pass

    # -------------------------------------------------------------
    # Scenario 10: Retrieve the deleted product
    # -------------------------------------------------------------
    res10 = requests.get(f"{BASE_URL}/{created_id_1}")
    scen10_pass = res10.status_code == 404 and res10.json().get("error") == "PRODUCT_NOT_FOUND"
    print_result(10, "Retrieve deleted product (verify 404)", scen10_pass, f"Status: {res10.status_code} (Correctly confirms 404)")
    all_passed = all_passed and scen10_pass

    # -------------------------------------------------------------
    # Scenario 11: Test category filtering
    # -------------------------------------------------------------
    # Populate test products across distinct categories
    requests.post(f"{BASE_URL}/", json={"name": "Gaming Laptop", "price": 1200.0, "stock_quantity": 10, "category": "Computers"})
    requests.post(f"{BASE_URL}/", json={"name": "Office Chair", "price": 150.0, "stock_quantity": 25, "category": "Furniture"})
    requests.post(f"{BASE_URL}/", json={"name": "Standing Desk", "price": 320.0, "stock_quantity": 15, "category": "Furniture"})

    res11 = requests.get(f"{BASE_URL}/?category=Furniture")
    items11 = res11.json() if res11.status_code == 200 else []
    scen11_pass = (
        res11.status_code == 200
        and len(items11) == 2
        and all(item["category"] == "Furniture" for item in items11)
    )
    print_result(11, "Category filtering (?category=Furniture)", scen11_pass, f"Status: {res11.status_code}, Matching Count: {len(items11)}")
    all_passed = all_passed and scen11_pass

    # -------------------------------------------------------------
    # Scenario 12: Test pagination (skip & limit)
    # -------------------------------------------------------------
    # Stored products total is at least 3 (Gaming Laptop, Office Chair, Standing Desk)
    res12_page1 = requests.get(f"{BASE_URL}/?skip=0&limit=2")
    res12_page2 = requests.get(f"{BASE_URL}/?skip=2&limit=2")
    items12_p1 = res12_page1.json()
    items12_p2 = res12_page2.json()

    scen12_pass = (
        res12_page1.status_code == 200
        and res12_page2.status_code == 200
        and len(items12_p1) == 2
        and len(items12_p2) >= 1
        and items12_p1[0]["id"] != items12_p2[0]["id"]
    )
    print_result(12, "Pagination (?skip=0&limit=2 vs skip=2)", scen12_pass, f"Page 1: {len(items12_p1)} items, Page 2: {len(items12_p2)} items")
    all_passed = all_passed and scen12_pass

    print_header("FINAL TEST RESULT")
    if all_passed:
        print("SUCCESS: ALL 12 TEST SCENARIOS PASSED AGAINST THE DOCKER CONTAINER!")
    else:
        print("WARNING: SOME TEST SCENARIOS FAILED. Check details above.")

    return all_passed


if __name__ == "__main__":
    success = run_all_docker_tests()
    sys.exit(0 if success else 1)
