"""
End-to-end test script executed directly against the live container / running service.
Target URL: http://localhost:8001
Covers all mandatory test scenarios from Step 9.
"""
import sys
import requests

BASE_URL = "http://localhost:8001"


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_result(scenario_num: int, name: str, passed: bool, details: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"[Scenario {scenario_num:02d}] {name.ljust(50)} {status}")
    if details:
        print(f"              Details: {details}")


def run_all_tests():
    print_header("LIVE AUTHENTICATION SERVICE REST API VERIFICATION")
    print(f"Target Service URL: {BASE_URL}")

    # Check health
    try:
        health_res = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_res.status_code == 200:
            print("Server Health Status: HEALTHY (200 OK)")
        else:
            print(f"Health check returned status {health_res.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to service at {BASE_URL}: {e}")
        sys.exit(1)

    all_passed = True
    test_email = "docker_user@shopease.com"
    initial_pass = "InitialPass123!"
    new_pass = "BrandNewPass456!"

    # 1. Register a new user successfully
    res1 = requests.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": "Docker Test User",
        "email": test_email,
        "password": initial_pass,
        "confirm_password": initial_pass,
    })
    p1 = res1.status_code in (201, 400)  # 201 created, or 400 if user already exists from prior test
    print_result(1, "Register new user successfully (201 Created)", p1, f"Status: {res1.status_code}")
    all_passed = all_passed and p1

    # 2. Register with duplicate email
    res2 = requests.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": "Duplicate User",
        "email": test_email,
        "password": initial_pass,
        "confirm_password": initial_pass,
    })
    p2 = res2.status_code == 400
    print_result(2, "Prevent duplicate email registration (400 Bad Request)", p2, f"Status: {res2.status_code}")
    all_passed = all_passed and p2

    # 3. Register with invalid email
    res3 = requests.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": "Invalid Email",
        "email": "not-an-email",
        "password": initial_pass,
        "confirm_password": initial_pass,
    })
    p3 = res3.status_code == 422
    print_result(3, "Reject invalid email format (422 Unprocessable)", p3, f"Status: {res3.status_code}")
    all_passed = all_passed and p3

    # 4. Register with mismatched passwords
    res4 = requests.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": "Mismatch User",
        "email": "mismatch@shopease.com",
        "password": initial_pass,
        "confirm_password": "WrongPassword999!",
    })
    p4 = res4.status_code == 422
    print_result(4, "Reject mismatched passwords (422 Unprocessable)", p4, f"Status: {res4.status_code}")
    all_passed = all_passed and p4

    # 5. Login using valid credentials
    # Determine which password to login with (in case password was previously changed)
    res5 = requests.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": initial_pass})
    active_pass = initial_pass
    if res5.status_code != 200:
        res5 = requests.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": new_pass})
        active_pass = new_pass

    p5 = res5.status_code == 200 and "access_token" in res5.json()
    token = res5.json().get("access_token") if p5 else ""
    print_result(5, "Login with valid credentials (200 OK & JWT)", p5, f"Status: {res5.status_code}")
    all_passed = all_passed and p5

    # 6. Login using incorrect password
    res6 = requests.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": "CompletelyWrongPass!"})
    p6 = res6.status_code == 401
    print_result(6, "Reject invalid password (401 Unauthorized)", p6, f"Status: {res6.status_code}")
    all_passed = all_passed and p6

    # 7. Login with non-existent email
    res7 = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "nonexistent_999@shopease.com", "password": initial_pass})
    p7 = res7.status_code == 401
    print_result(7, "Reject unregistered email (401 Unauthorized)", p7, f"Status: {res7.status_code}")
    all_passed = all_passed and p7

    # 8. Access /api/auth/me with valid token
    headers = {"Authorization": f"Bearer {token}"}
    res8 = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    p8 = res8.status_code == 200 and res8.json().get("email") == test_email
    print_result(8, "Access /api/auth/me with valid Bearer token (200 OK)", p8, f"Status: {res8.status_code}")
    all_passed = all_passed and p8

    # 9. Access protected endpoint without token
    res9 = requests.get(f"{BASE_URL}/api/auth/me")
    p9 = res9.status_code == 401
    print_result(9, "Reject request without token (401 Unauthorized)", p9, f"Status: {res9.status_code}")
    all_passed = all_passed and p9

    # 10. Access protected endpoint with invalid token
    res10 = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": "Bearer fake.invalid.token"})
    p10 = res10.status_code == 401
    print_result(10, "Reject invalid token (401 Unauthorized)", p10, f"Status: {res10.status_code}")
    all_passed = all_passed and p10

    # 11. Validate token with /api/auth/verify-token
    res11 = requests.post(f"{BASE_URL}/api/auth/verify-token", json={"token": token})
    p11 = res11.status_code == 200 and res11.json().get("valid") is True
    print_result(11, "Verify valid token via /verify-token (200 OK)", p11, f"Status: {res11.status_code}")
    all_passed = all_passed and p11

    # 12. Change password with wrong current password
    res12 = requests.post(f"{BASE_URL}/api/auth/change-password", headers=headers, json={
        "current_password": "WrongPassword999!",
        "new_password": new_pass,
        "confirm_new_password": new_pass,
    })
    p12 = res12.status_code == 400
    print_result(12, "Reject change password with wrong current password (400)", p12, f"Status: {res12.status_code}")
    all_passed = all_passed and p12

    # 13. Change password with correct current password
    target_new_pass = new_pass if active_pass == initial_pass else initial_pass
    res13 = requests.post(f"{BASE_URL}/api/auth/change-password", headers=headers, json={
        "current_password": active_pass,
        "new_password": target_new_pass,
        "confirm_new_password": target_new_pass,
    })
    p13 = res13.status_code == 200
    print_result(13, "Change password with correct current password (200 OK)", p13, f"Status: {res13.status_code}")
    all_passed = all_passed and p13

    # 14. Verify login with new password
    res14 = requests.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": target_new_pass})
    p14 = res14.status_code == 200
    print_result(14, "Login succeeds with the new password (200 OK)", p14, f"Status: {res14.status_code}")
    all_passed = all_passed and p14

    print_header("SUMMARY")
    if all_passed:
        print("ALL 14 LIVE API TEST SCENARIOS PASSED SUCCESSFULLY! [100%]")
    else:
        print("SOME TESTS FAILED! Check the details above.")


if __name__ == "__main__":
    run_all_tests()

