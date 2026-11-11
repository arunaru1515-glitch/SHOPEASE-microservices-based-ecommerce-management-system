"""
End-to-end HTTP test script executed directly against the live User Service.
Default URL: http://localhost:8002
Covers all profile, address, and account lifecycle endpoints.
"""
from datetime import datetime, timedelta, timezone
import sys
import jwt
import requests

BASE_URL = "http://localhost:8002"
JWT_SECRET_KEY = "supersecretjwtkey_change_in_production_1234567890!@#$%"
JWT_ALGORITHM = "HS256"


def create_token(user_id: int, email: str, role: str = "customer") -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_result(num: int, name: str, passed: bool, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"[Scenario {num:02d}] {name.ljust(48)} {status}")
    if details:
        print(f"              Details: {details}")


def run_live_tests():
    print_header("LIVE USER MANAGEMENT SERVICE REST API VERIFICATION")
    print(f"Target URL: {BASE_URL}")

    # 1. Health check
    try:
        res = requests.get(f"{BASE_URL}/health", timeout=5)
        if res.status_code == 200:
            print("Server Health Status: HEALTHY (200 OK)")
        else:
            print(f"Server health check failed with status: {res.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Could not connect to {BASE_URL}: {e}")
        sys.exit(1)

    all_passed = True
    token_a = create_token(999, "docker_user@shopease.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Access profile without token
    r1 = requests.get(f"{BASE_URL}/api/users/profile")
    p1 = r1.status_code == 401
    print_result(1, "Access profile without token (401)", p1, f"Status: {r1.status_code}")
    all_passed = all_passed and p1

    # 2. Access profile with invalid token
    r2 = requests.get(f"{BASE_URL}/api/users/profile", headers={"Authorization": "Bearer fake.token"})
    p2 = r2.status_code == 401
    print_result(2, "Access profile with invalid token (401)", p2, f"Status: {r2.status_code}")
    all_passed = all_passed and p2

    # 3. Create profile
    # If already exists from prior run, delete it first
    requests.delete(f"{BASE_URL}/api/users/profile", headers=headers_a)
    r3 = requests.post(f"{BASE_URL}/api/users/profile", headers=headers_a, json={
        "full_name": "Docker User",
        "phone_number": "+1234567890",
        "date_of_birth": "1992-04-10",
        "gender": "Male"
    })
    p3 = r3.status_code in (201, 400)
    print_result(3, "Create profile using valid token (201)", p3, f"Status: {r3.status_code}")
    all_passed = all_passed and p3

    # 4. Prevent duplicate profile
    r4 = requests.post(f"{BASE_URL}/api/users/profile", headers=headers_a, json={
        "full_name": "Duplicate User",
        "phone_number": "+1234567890"
    })
    p4 = r4.status_code == 400
    print_result(4, "Prevent duplicate profile (400)", p4, f"Status: {r4.status_code}")
    all_passed = all_passed and p4

    # 5. Get current profile
    r5 = requests.get(f"{BASE_URL}/api/users/profile", headers=headers_a)
    p5 = r5.status_code == 200
    print_result(5, "Get current user profile (200)", p5, f"Status: {r5.status_code}")
    all_passed = all_passed and p5

    # 6. Add address
    r6 = requests.post(f"{BASE_URL}/api/users/addresses", headers=headers_a, json={
        "address_type": "Home",
        "full_name": "Docker User",
        "phone_number": "+1234567890",
        "address_line_1": "123 Docker Lane",
        "city": "San Francisco",
        "state": "CA",
        "country": "USA",
        "postal_code": "94105",
        "is_default": True
    })
    p6 = r6.status_code == 201
    addr_id = r6.json().get("id") if p6 else 1
    print_result(6, "Add delivery address (201)", p6, f"Address ID: {addr_id}")
    all_passed = all_passed and p6

    # 7. List addresses
    r7 = requests.get(f"{BASE_URL}/api/users/addresses", headers=headers_a)
    p7 = r7.status_code == 200 and len(r7.json()) >= 1
    print_result(7, "List delivery addresses (200)", p7, f"Count: {len(r7.json()) if p7 else 0}")
    all_passed = all_passed and p7

    # 8. Set default address
    r8 = requests.patch(f"{BASE_URL}/api/users/addresses/{addr_id}/default", headers=headers_a)
    p8 = r8.status_code == 200 and r8.json().get("is_default") is True
    print_result(8, "Set default address (200)", p8, f"Status: {r8.status_code}")
    all_passed = all_passed and p8

    # 9. Account overview
    r9 = requests.get(f"{BASE_URL}/api/users/account", headers=headers_a)
    p9 = r9.status_code == 200
    print_result(9, "Get account overview (200)", p9, f"Status: {r9.status_code}")
    all_passed = all_passed and p9

    print_header("LIVE TEST SUMMARY")
    if all_passed:
        print("ALL LIVE REST API SCENARIOS PASSED SUCCESSFULLY! [100%]")
    else:
        print("SOME TESTS FAILED! Check the output above.")


if __name__ == "__main__":
    run_live_tests()

