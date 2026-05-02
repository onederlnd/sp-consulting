# flake8: noqa: E402
"""
conftest.py — Sunceray Patterson Consulting
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User, set_password

# ── App & Client ─────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def app():
    """Single app instance for the entire test session."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="session")
def db(app):
    """Session-scoped DB — schema created once, shared across all tests."""
    return _db


@pytest.fixture(autouse=True)
def clean_db(db):
    """Delete all rows between tests. No app param — context already active."""
    yield
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()
    db.session.remove()


@pytest.fixture()
def client(app):
    """Fresh test client per test — prevents session bleed between tests."""
    with app.test_client() as c:
        yield c


# ── User Factories ────────────────────────────────────────────────────────────


def make_user(db, email, password, first_name, last_name, role, is_active=True):
    """Low-level user factory. Accepts db explicitly to stay in the right session."""
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=is_active,
    )
    set_password(user, password)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def admin_user(db):
    return make_user(db, "admin@test.com", "password123", "Admin", "User", "admin")


@pytest.fixture()
def staff_user(db):
    return make_user(db, "staff@test.com", "password123", "Staff", "User", "staff")


@pytest.fixture()
def client_user(db):
    return make_user(db, "client@test.com", "password123", "Client", "User", "client")


@pytest.fixture()
def inactive_user(db):
    return make_user(
        db,
        "inactive@test.com",
        "password123",
        "Inactive",
        "User",
        "client",
        is_active=False,
    )


# ── Auth Helpers ──────────────────────────────────────────────────────────────


def login(client, email, password, follow_redirects=True):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=follow_redirects,
    )


def logout(client, follow_redirects=True):
    return client.get("/auth/logout", follow_redirects=follow_redirects)


# ── Authenticated Client Fixtures ─────────────────────────────────────────────


@pytest.fixture()
def admin_client(client, admin_user):
    login(client, "admin@test.com", "password123")
    yield client
    logout(client)


@pytest.fixture()
def staff_client(client, staff_user):
    response = login(client, "staff@test.com", "password123")
    # login(client, "staff@test.com", "password123")
    print(f"\n[DEBUG] login status: {response.status_code}")
    print(f"\n[DEBUG] login data snippet: {response.data[1400:1600]}")
    yield client
    logout(client)


@pytest.fixture()
def client_client(client, client_user):
    login(client, "client@test.com", "password123")
    yield client
    logout(client)


# ── API Helpers ───────────────────────────────────────────────────────────────


def api_get(client, url, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.get(url, headers=headers, **kwargs)


def api_post(client, url, json=None, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post(url, json=json, headers=headers, **kwargs)


def api_put(client, url, json=None, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.put(url, json=json, headers=headers, **kwargs)


def api_delete(client, url, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.delete(url, headers=headers, **kwargs)


# ── Response Assertion Helpers ────────────────────────────────────────────────


def assert_ok(response):
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def assert_redirect(response, to=None):
    assert response.status_code in (
        301,
        302,
    ), f"Expected redirect, got {response.status_code}"
    if to:
        assert (
            to in response.headers["Location"]
        ), f"Expected redirect to '{to}', got '{response.headers['Location']}'"


def assert_forbidden(response):
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"


def assert_unauthorized(response):
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


def assert_json(response, key=None, value=None):
    data = response.get_json()
    assert data is not None, "Response is not JSON"
    if key is not None:
        assert key in data, f"Key '{key}' not in response JSON"
    if value is not None:
        assert data[key] == value, f"Expected {key}={value}, got {data[key]}"
    return data
