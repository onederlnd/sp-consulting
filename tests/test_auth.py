"""
test_auth.py — Authentication & authorization tests
Covers: login, logout, password reset, route protection, role enforcement.
"""

from tests.conftest import login, logout, assert_ok, assert_redirect, assert_forbidden

# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_page_loads(client):
    response = client.get("/auth/login")
    assert_ok(response)
    assert b"Sign In" in response.data


def test_login_valid_credentials(client, admin_user):
    response = login(client, "admin@test.com", "password123")
    assert_ok(response)
    logout(client)


def test_login_invalid_password(client, admin_user):
    response = login(client, "admin@test.com", "wrongpassword")
    assert b"Invalid email or password" in response.data


def test_login_invalid_email(client):
    response = login(client, "nobody@test.com", "password123")
    assert b"Invalid email or password" in response.data


def test_login_inactive_user(client, inactive_user):
    response = login(client, "inactive@test.com", "password123")
    assert b"Invalid email or password" in response.data


# ── Logout ────────────────────────────────────────────────────────────────────


def test_logout(client, admin_user):
    login(client, "admin@test.com", "password123")
    response = logout(client)
    assert_ok(response)
    assert b"logged out" in response.data


# ── Password Reset ────────────────────────────────────────────────────────────


def test_reset_password_request_page_loads(client):
    response = client.get("/auth/reset-password")
    assert_ok(response)
    assert b"Reset Password" in response.data


def test_reset_password_request_unknown_email(client):
    response = client.post(
        "/auth/reset-password",
        data={"email": "nobody@test.com"},
        follow_redirects=True,
    )
    assert b"reset link has been sent" in response.data


def test_reset_password_request_known_email(client, admin_user):
    response = client.post(
        "/auth/reset-password",
        data={"email": "admin@test.com"},
        follow_redirects=True,
    )
    assert b"reset link has been sent" in response.data


# ── Route Protection ──────────────────────────────────────────────────────────


def test_protected_route_redirects_when_logged_out(client):
    response = client.get("/client/", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_client_cannot_access_staff(client_client):
    response = client_client.get("/staff/")
    assert_forbidden(response)


def test_staff_can_access_staff_area(staff_client):
    response = staff_client.get("/staff/")
    assert_ok(response)
