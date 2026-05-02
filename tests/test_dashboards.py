"""
test_dashboards.py — Dashboard and portal route tests
Covers: page loads, role access, redirects, content assertions.
"""

from tests.conftest import (
    assert_ok,
    assert_redirect,
    assert_forbidden,
    login,
    logout,
    make_user,
)


# ── Client Portal ─────────────────────────────────────────────────────────────


def test_client_dashboard_loads(client_client):
    response = client_client.get("/client/")
    assert_ok(response)
    assert b"Dashboard" in response.data


def test_client_documents_loads(client_client):
    response = client_client.get("/client/documents")
    assert_ok(response)
    assert b"Documents" in response.data


def test_client_messages_loads(client_client):
    response = client_client.get("/client/messages")
    assert_ok(response)
    assert b"Messages" in response.data


def test_client_reports_loads(client_client):
    response = client_client.get("/client/reports")
    assert_ok(response)
    assert b"Reports" in response.data


def test_client_send_empty_message(client_client):
    response = client_client.post(
        "/client/messages/send",
        data={"body": ""},
        follow_redirects=True,
    )
    assert b"Message cannot be empty" in response.data


def test_client_send_message(client_client):
    response = client_client.post(
        "/client/messages/send",
        data={"body": "Hello, I have a question about my engagement."},
        follow_redirects=True,
    )
    assert b"Message sent" in response.data


# ── Client Portal — Access Control ───────────────────────────────────────────


def test_client_dashboard_redirects_when_logged_out(client):
    response = client.get("/client/", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_staff_cannot_access_client_portal(staff_client):
    response = staff_client.get("/client/")
    assert_forbidden(response)


def test_admin_cannot_access_client_portal(admin_client):
    response = admin_client.get("/client/")
    assert_forbidden(response)


# ── Staff Portal ──────────────────────────────────────────────────────────────


def test_staff_dashboard_loads(staff_client):
    response = staff_client.get("/staff/")
    assert_ok(response)
    assert b"Staff Overview" in response.data


def test_staff_clients_loads(staff_client):
    response = staff_client.get("/staff/clients")
    assert_ok(response)
    assert b"Clients" in response.data


def test_staff_engagements_loads(staff_client):
    response = staff_client.get("/staff/engagements")
    assert_ok(response)
    assert b"Engagements" in response.data


def test_staff_documents_loads(staff_client):
    response = staff_client.get("/staff/documents")
    assert_ok(response)
    assert b"Documents" in response.data


# ── Staff Portal — Access Control ────────────────────────────────────────────


def test_staff_dashboard_redirects_when_logged_out(client):
    response = client.get("/staff/", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_client_cannot_access_staff_portal(client_client):
    response = client_client.get("/staff/")
    assert_forbidden(response)


# ── Admin-only Staff Routes ───────────────────────────────────────────────────


def test_staff_cannot_access_user_management(staff_client):
    response = staff_client.get("/staff/users")
    assert_forbidden(response)


def test_admin_can_access_user_management(admin_client):
    response = admin_client.get("/staff/users")
    assert_ok(response)
    assert b"User Management" in response.data


def test_staff_cannot_access_create_user(staff_client):
    response = staff_client.get("/staff/users/new")
    assert_forbidden(response)


def test_admin_can_access_create_user(admin_client):
    response = admin_client.get("/staff/users/new")
    assert_ok(response)
    assert b"Add User" in response.data


def test_admin_can_create_user(admin_client):
    response = admin_client.post(
        "/staff/users/new",
        data={
            "first_name": "New",
            "last_name": "Client",
            "email": "newclient@test.com",
            "role": "client",
            "password": "password123",
            "confirm": "password123",
        },
        follow_redirects=True,
    )
    assert b"created successfully" in response.data


def test_admin_create_user_duplicate_email(admin_client, admin_user):
    response = admin_client.post(
        "/staff/users/new",
        data={
            "first_name": "Dupe",
            "last_name": "User",
            "email": "admin@test.com",
            "role": "client",
            "password": "password123",
            "confirm": "password123",
        },
        follow_redirects=True,
    )
    assert b"already exists" in response.data


"""
test_dashboards_extended.py — Extended dashboard, portal, and security tests
Covers: token flow, role redirects, empty states, validation, cross-role access.
"""


# ── Auth — Already Authenticated Redirects ────────────────────────────────────


def test_authenticated_staff_hitting_login_redirects_to_staff(client, staff_user):
    login(client, "staff@test.com", "password123")
    response = client.get("/auth/login", follow_redirects=False)
    assert_redirect(response, to="/staff/")
    logout(client)


def test_authenticated_admin_hitting_login_redirects_to_staff(client, admin_user):
    login(client, "admin@test.com", "password123")
    response = client.get("/auth/login", follow_redirects=False)
    assert_redirect(response, to="/staff/")
    logout(client)


def test_authenticated_client_hitting_login_redirects_to_client(client, client_user):
    login(client, "client@test.com", "password123")
    response = client.get("/auth/login", follow_redirects=False)
    assert_redirect(response, to="/client/")
    logout(client)


# ── Auth — Next Parameter ─────────────────────────────────────────────────────


def test_login_next_param_redirects_correctly(client, client_user):
    response = client.get("/client/documents", follow_redirects=False)
    assert_redirect(response, to="/auth/login")

    response = client.post(
        "/auth/login?next=/client/documents",
        data={"email": "client@test.com", "password": "password123"},
        follow_redirects=False,
    )
    assert_redirect(response, to="/client/documents")


# ── Auth — Password Reset Token Flow ─────────────────────────────────────────


def test_reset_password_invalid_token_redirects(client):
    response = client.get(
        "/auth/reset-password/invalid-token-xyz",
        follow_redirects=True,
    )
    assert b"invalid or has expired" in response.data


def test_reset_password_valid_token_loads_form(client, admin_user, app):
    from app.routes.auth.routes import generate_reset_token

    with app.app_context():
        token = generate_reset_token("admin@test.com")
    response = client.get(
        f"/auth/reset-password/{token}",
        follow_redirects=False,
    )
    assert_ok(response)
    assert b"Reset" in response.data


def test_reset_password_valid_token_updates_password(client, admin_user, app):
    from app.routes.auth.routes import generate_reset_token

    with app.app_context():
        token = generate_reset_token("admin@test.com")
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword123", "confirm": "newpassword123"},
        follow_redirects=True,
    )
    assert b"password has been updated" in response.data
    # Confirm new password works
    response = login(client, "admin@test.com", "newpassword123")
    assert_ok(response)


def test_reset_password_mismatched_passwords(client, admin_user, app):
    from app.routes.auth.routes import generate_reset_token

    with app.app_context():
        token = generate_reset_token("admin@test.com")
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword123", "confirm": "wrongpassword"},
        follow_redirects=True,
    )
    assert b"Passwords must match" in response.data


# ── Auth — Session Security ───────────────────────────────────────────────────


def test_protected_route_inaccessible_after_logout(client, client_user):
    login(client, "client@test.com", "password123")
    logout(client)
    response = client.get("/client/", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_next_param_preserved_on_redirect(client, client_user):
    response = client.get("/client/documents", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


# ── Client Portal — Empty States ─────────────────────────────────────────────


def test_client_dashboard_empty_state(client_client):
    response = client_client.get("/client/")
    assert_ok(response)
    assert b"No active engagements" in response.data
    assert b"No documents available" in response.data


def test_client_documents_empty_state(client_client):
    response = client_client.get("/client/documents")
    assert_ok(response)
    assert b"No documents available" in response.data


def test_client_messages_empty_state(client_client):
    response = client_client.get("/client/messages")
    assert_ok(response)
    assert b"No messages yet" in response.data


def test_client_reports_empty_state(client_client):
    response = client_client.get("/client/reports")
    assert_ok(response)
    assert b"No reports available" in response.data


def test_client_dashboard_shows_name(client_client, client_user):
    response = client_client.get("/client/")
    assert_ok(response)
    assert b"Client" in response.data


# ── Staff Portal — Role-based Client Visibility ───────────────────────────────


def test_admin_sees_all_clients(admin_client, db):
    make_user(db, "c1@test.com", "password123", "Alice", "One", "client")
    make_user(db, "c2@test.com", "password123", "Bob", "Two", "client")
    response = admin_client.get("/staff/clients")
    assert_ok(response)
    assert b"Alice" in response.data
    assert b"Bob" in response.data


def test_staff_sees_only_assigned_clients(client, db, app):
    staff = make_user(db, "mystaff@test.com", "password123", "My", "Staff", "staff")
    assigned = make_user(
        db, "assigned@test.com", "password123", "Assigned", "Client", "client"
    )
    make_user(db, "other@test.com", "password123", "Other", "Client", "client")

    with app.app_context():
        from app.models.user import User

        s = db.session.get(User, staff.id)
        c = db.session.get(User, assigned.id)
        s.assigned_clients.append(c)
        db.session.commit()

    with app.test_client() as c:
        login(c, "mystaff@test.com", "password123")
        response = c.get("/staff/clients")
        assert_ok(response)
        assert b"Assigned" in response.data
        assert b"Other" not in response.data


# ── Staff Portal — Settings Access ───────────────────────────────────────────


def test_staff_cannot_access_settings(staff_client):
    response = staff_client.get("/staff/settings")
    assert_forbidden(response)


def test_admin_can_access_settings(admin_client):
    response = admin_client.get("/staff/settings")
    assert_ok(response)


# ── User Management — Validation ─────────────────────────────────────────────


def test_create_user_password_mismatch(admin_client):
    response = admin_client.post(
        "/staff/users/new",
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@test.com",
            "role": "client",
            "password": "password123",
            "confirm": "wrongpassword",
        },
        follow_redirects=True,
    )
    assert b"Passwords must match" in response.data


def test_create_user_invalid_email(admin_client):
    response = admin_client.post(
        "/staff/users/new",
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "not-an-email",
            "role": "client",
            "password": "password123",
            "confirm": "password123",
        },
        follow_redirects=True,
    )
    assert b"Invalid email" in response.data


def test_create_user_short_password(admin_client):
    response = admin_client.post(
        "/staff/users/new",
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@test.com",
            "role": "client",
            "password": "short",
            "confirm": "short",
        },
        follow_redirects=True,
    )
    assert b"Field must be at least 8 characters" in response.data


def test_user_list_ordered_by_last_name(admin_client, db):
    make_user(db, "z@test.com", "password123", "Zara", "Zee", "client")
    make_user(db, "a@test.com", "password123", "Adam", "Aaa", "client")
    response = admin_client.get("/staff/users")
    assert_ok(response)
    aaa_pos = response.data.find(b"Aaa")
    zee_pos = response.data.find(b"Zee")
    assert aaa_pos < zee_pos, "Users should be ordered by last name"


# ── Cross-role Access — Individual Client Routes ──────────────────────────────


def test_staff_cannot_access_client_documents(staff_client):
    response = staff_client.get("/client/documents")
    assert_forbidden(response)


def test_staff_cannot_access_client_messages(staff_client):
    response = staff_client.get("/client/messages")
    assert_forbidden(response)


def test_staff_cannot_access_client_reports(staff_client):
    response = staff_client.get("/client/reports")
    assert_forbidden(response)


def test_client_cannot_access_staff_clients(client_client):
    response = client_client.get("/staff/clients")
    assert_forbidden(response)


def test_client_cannot_access_staff_documents(client_client):
    response = client_client.get("/staff/documents")
    assert_forbidden(response)


def test_client_cannot_access_staff_engagements(client_client):
    response = client_client.get("/staff/engagements")
    assert_forbidden(response)


# ── Cross-role Access — Admin can access staff portal ────────────────────────


def test_admin_can_access_staff_dashboard(admin_client):
    response = admin_client.get("/staff/")
    assert_ok(response)


def test_admin_can_access_staff_clients(admin_client):
    response = admin_client.get("/staff/clients")
    assert_ok(response)


def test_admin_can_access_staff_engagements(admin_client):
    response = admin_client.get("/staff/engagements")
    assert_ok(response)


def test_admin_can_access_staff_documents(admin_client):
    response = admin_client.get("/staff/documents")
    assert_ok(response)
