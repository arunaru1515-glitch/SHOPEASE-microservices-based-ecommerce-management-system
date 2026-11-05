from datetime import timedelta
import pytest
from app.core.security import create_access_token
from app.models.user_model import User


def test_register_success(client):
    """Scenario 1: Register a new user successfully."""
    payload = {
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User registered successfully."
    assert data["user"]["full_name"] == "John Doe"
    assert data["user"]["email"] == "johndoe@example.com"
    assert data["user"]["role"] == "customer"
    assert data["user"]["is_active"] is True
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_duplicate_email(client):
    """Scenario 2: Register using an already existing email."""
    payload = {
        "full_name": "John Doe",
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_invalid_email(client):
    """Scenario 3: Register with an invalid email."""
    payload = {
        "full_name": "Invalid Email",
        "email": "invalid-email-format",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_register_mismatched_passwords(client):
    """Scenario 4: Register with mismatched passwords."""
    payload = {
        "full_name": "Mismatch Tester",
        "email": "mismatch@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "DifferentPassword123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


def test_register_weak_password(client):
    """Scenario 5: Register with weak passwords."""
    # Too short
    res_short = client.post("/api/auth/register", json={
        "full_name": "Short",
        "email": "short@example.com",
        "password": "abc",
        "confirm_password": "abc",
    })
    assert res_short.status_code == 422

    # No number or special char
    res_no_num = client.post("/api/auth/register", json={
        "full_name": "NoNum",
        "email": "nonum@example.com",
        "password": "PasswordOnly",
        "confirm_password": "PasswordOnly",
    })
    assert res_no_num.status_code == 422


def test_login_success(client):
    """Scenario 6: Login using valid credentials."""
    client.post("/api/auth/register", json={
        "full_name": "Login User",
        "email": "login@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    })

    response = client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "StrongPassword123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful."
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@example.com"


def test_login_incorrect_password(client):
    """Scenario 7: Login using an incorrect password."""
    client.post("/api/auth/register", json={
        "full_name": "Wrong Pass",
        "email": "wrongpass@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    })

    response = client.post("/api/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "IncorrectPassword999!",
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_email(client):
    """Scenario 8: Login with an unregistered email."""
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "StrongPassword123!",
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_inactive_user(client, db_session):
    """Scenario 9: Login using an inactive account."""
    client.post("/api/auth/register", json={
        "full_name": "Inactive User",
        "email": "inactive@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    })

    # Deactivate the user directly in database
    user = db_session.query(User).filter(User.email == "inactive@example.com").first()
    user.is_active = False
    db_session.commit()

    response = client.post("/api/auth/login", json={
        "email": "inactive@example.com",
        "password": "StrongPassword123!",
    })
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"]


def test_get_me_success(client):
    """Scenario 10: Access /api/auth/me with a valid token."""
    client.post("/api/auth/register", json={
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    })

    login_res = client.post("/api/auth/login", json={
        "email": "alice@example.com",
        "password": "StrongPassword123!",
    })
    token = login_res.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_get_me_missing_token(client):
    """Scenario 11: Access a protected endpoint without a token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    """Scenario 12: Access a protected endpoint with an invalid token."""
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


def test_get_me_expired_token(client):
    """Scenario 13: Access a protected endpoint with an expired token."""
    # Create an expired token (-10 minutes)
    expired_token = create_access_token(
        data={"sub": "1", "email": "test@example.com", "role": "customer"},
        expires_delta=timedelta(minutes=-10),
    )
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"]


def test_verify_token_api(client):
    """Scenario 14: Validate token via /api/auth/verify-token."""
    client.post("/api/auth/register", json={
        "full_name": "Token Verifier",
        "email": "verify@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    })
    login_res = client.post("/api/auth/login", json={
        "email": "verify@example.com",
        "password": "StrongPassword123!",
    })
    token = login_res.json()["access_token"]

    # Verify valid token
    res_valid = client.post("/api/auth/verify-token", json={"token": token})
    assert res_valid.status_code == 200
    assert res_valid.json()["valid"] is True
    assert res_valid.json()["email"] == "verify@example.com"

    # Verify invalid token
    res_invalid = client.post("/api/auth/verify-token", json={"token": "gibberish"})
    assert res_invalid.status_code == 200
    assert res_invalid.json()["valid"] is False


def test_change_password_flow(client):
    """Scenario 15, 16, 17: Change password flow & subsequent login."""
    client.post("/api/auth/register", json={
        "full_name": "Change Pass User",
        "email": "changepass@example.com",
        "password": "OldPassword123!",
        "confirm_password": "OldPassword123!",
    })

    login_res = client.post("/api/auth/login", json={
        "email": "changepass@example.com",
        "password": "OldPassword123!",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt with wrong current password (Scenario 16)
    bad_change = client.post("/api/auth/change-password", headers=headers, json={
        "current_password": "WrongPassword123!",
        "new_password": "NewStrongPassword456!",
        "confirm_new_password": "NewStrongPassword456!",
    })
    assert bad_change.status_code == 400
    assert "Incorrect current password" in bad_change.json()["detail"]

    # Attempt with correct current password (Scenario 15)
    good_change = client.post("/api/auth/change-password", headers=headers, json={
        "current_password": "OldPassword123!",
        "new_password": "NewStrongPassword456!",
        "confirm_new_password": "NewStrongPassword456!",
    })
    assert good_change.status_code == 200
    assert good_change.json()["message"] == "Password changed successfully."

    # Login with old password should fail
    old_login = client.post("/api/auth/login", json={
        "email": "changepass@example.com",
        "password": "OldPassword123!",
    })
    assert old_login.status_code == 401

    # Login with new password should succeed (Scenario 17)
    new_login = client.post("/api/auth/login", json={
        "email": "changepass@example.com",
        "password": "NewStrongPassword456!",
    })
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()

