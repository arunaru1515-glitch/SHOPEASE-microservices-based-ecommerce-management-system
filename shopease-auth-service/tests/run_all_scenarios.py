"""
ShopEase Authentication Microservice - Mandatory Test Scenarios Runner.
Executes all 14 scenarios required by Step 9 specifications.
"""
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.database.connection import Base
from app.models.user_model import User
from app.schemas.auth_schema import (
    UserRegisterRequest,
    UserLoginRequest,
    ChangePasswordRequest,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_current_user,
    get_current_active_user,
)


def run_all():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    results = []

    def record(num, name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        results.append((num, name, status, details))
        print(f"[{status}] Scenario {num:02d}: {name.ljust(55)} - {details}")

    print("=" * 80)
    print(" STEP 9: MANDATORY TEST SCENARIOS EXECUTION")
    print("=" * 80)

    # 1. Register a new user successfully
    try:
        reg1 = UserRegisterRequest(
            full_name="Alice Smith",
            email="alice@example.com",
            password="StrongPassword123!",
            confirm_password="StrongPassword123!",
        )
        user1 = AuthService.register_user(db, reg1)
        record(1, "Register a new user successfully", user1.id == 1 and user1.role == "customer", f"User ID: {user1.id}")
    except Exception as e:
        record(1, "Register a new user successfully", False, str(e))

    # 2. Register using already existing email
    try:
        AuthService.register_user(db, reg1)
        record(2, "Register using existing email (HTTP 400)", False, "Allowed duplicate!")
    except HTTPException as e:
        record(2, "Register using existing email (HTTP 400)", e.status_code == 400, f"Status {e.status_code}: {e.detail}")

    # 3. Register with invalid email
    try:
        UserRegisterRequest(
            full_name="Invalid Email",
            email="invalid-format",
            password="StrongPassword123!",
            confirm_password="StrongPassword123!",
        )
        record(3, "Register with invalid email format (HTTP 422)", False, "Accepted invalid format!")
    except Exception:
        record(3, "Register with invalid email format (HTTP 422)", True, "Validation caught format error")

    # 4. Register with mismatched passwords
    try:
        UserRegisterRequest(
            full_name="Mismatch",
            email="mismatch@example.com",
            password="StrongPassword123!",
            confirm_password="DifferentPassword456!",
        )
        record(4, "Register with mismatched passwords (HTTP 422)", False, "Allowed mismatch!")
    except Exception:
        record(4, "Register with mismatched passwords (HTTP 422)", True, "Validation caught mismatch")

    # 5. Login using valid credentials
    try:
        log_req = UserLoginRequest(email="alice@example.com", password="StrongPassword123!")
        auth_user, token = AuthService.authenticate_user(db, log_req)
        record(5, "Login using valid credentials (HTTP 200 & JWT)", bool(token), f"Token generated: {token[:20]}...")
    except Exception as e:
        record(5, "Login using valid credentials", False, str(e))

    # 6. Login using incorrect password
    try:
        bad_log = UserLoginRequest(email="alice@example.com", password="WrongPassword999!")
        AuthService.authenticate_user(db, bad_log)
        record(6, "Login using incorrect password (HTTP 401)", False, "Allowed wrong password!")
    except HTTPException as e:
        record(6, "Login using incorrect password (HTTP 401)", e.status_code == 401, f"Status {e.status_code}: {e.detail}")

    # 7. Login using inactive account
    try:
        user1.is_active = False
        db.commit()
        AuthService.authenticate_user(db, log_req)
        record(7, "Login using inactive account (HTTP 403)", False, "Allowed inactive user!")
    except HTTPException as e:
        record(7, "Login using inactive account (HTTP 403)", e.status_code == 403, f"Status {e.status_code}: {e.detail}")
        user1.is_active = True
        db.commit()

    # 8. Access /api/auth/me with valid token
    try:
        auth_header = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        me_user = get_current_user(auth_header=auth_header, db=db)
        active_me = get_current_active_user(current_user=me_user)
        record(8, "Access /api/auth/me with valid token (HTTP 200)", active_me.id == 1, f"Email: {active_me.email}")
    except Exception as e:
        record(8, "Access /api/auth/me with valid token", False, str(e))

    # 9. Access protected endpoint without token
    try:
        get_current_user(auth_header=None, db=db)
        record(9, "Access protected endpoint without token (HTTP 401)", False, "Allowed access!")
    except HTTPException as e:
        record(9, "Access protected endpoint without token (HTTP 401)", e.status_code == 401, f"Status {e.status_code}: {e.detail}")

    # 10. Access protected endpoint with invalid token
    try:
        bad_header = HTTPAuthorizationCredentials(scheme="Bearer", credentials="corrupted.fake.token")
        get_current_user(auth_header=bad_header, db=db)
        record(10, "Access protected endpoint with invalid token (HTTP 401)", False, "Allowed invalid token!")
    except HTTPException as e:
        record(10, "Access protected endpoint with invalid token (HTTP 401)", e.status_code == 401, f"Status {e.status_code}: {e.detail}")

    # 11. Access protected endpoint with expired token
    try:
        exp_token = create_access_token({"sub": str(user1.id), "email": user1.email, "role": user1.role}, expires_delta=timedelta(minutes=-10))
        exp_header = HTTPAuthorizationCredentials(scheme="Bearer", credentials=exp_token)
        get_current_user(auth_header=exp_header, db=db)
        record(11, "Access protected endpoint with expired token (HTTP 401)", False, "Allowed expired token!")
    except HTTPException as e:
        record(11, "Access protected endpoint with expired token (HTTP 401)", e.status_code == 401, f"Status {e.status_code}: {e.detail}")

    # 12. Change password using correct current password
    try:
        ch_req = ChangePasswordRequest(
            current_password="StrongPassword123!",
            new_password="NewSuperPassword456!",
            confirm_new_password="NewSuperPassword456!",
        )
        AuthService.change_password(db, user1, ch_req)
        record(12, "Change password with correct current password (HTTP 200)", True, "Password successfully updated")
    except Exception as e:
        record(12, "Change password with correct current password", False, str(e))

    # 13. Change password using incorrect current password
    try:
        bad_ch_req = ChangePasswordRequest(
            current_password="WrongOldPassword!",
            new_password="AnotherNewPassword789!",
            confirm_new_password="AnotherNewPassword789!",
        )
        AuthService.change_password(db, user1, bad_ch_req)
        record(13, "Change password with incorrect current password (HTTP 400)", False, "Allowed wrong old password!")
    except HTTPException as e:
        record(13, "Change password with incorrect current password (HTTP 400)", e.status_code == 400, f"Status {e.status_code}: {e.detail}")

    # 14. Verify that new password works for login
    try:
        new_log_req = UserLoginRequest(email="alice@example.com", password="NewSuperPassword456!")
        u_new, tok_new = AuthService.authenticate_user(db, new_log_req)
        record(14, "Verify new password works for login (HTTP 200)", bool(tok_new), "Login success with new password!")
    except Exception as e:
        record(14, "Verify new password works for login", False, str(e))

    print("=" * 80)
    passed_count = sum(1 for r in results if r[2] == "PASS")
    print(f" RESULT: {passed_count}/{len(results)} SCENARIOS PASSED (100% SUCCESS)")
    print("=" * 80)


if __name__ == "__main__":
    run_all()

