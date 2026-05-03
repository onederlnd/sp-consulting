"""
test_organizations.py — Organization management tests
Covers: org creation, invite flow, access control, slug generation,
        org detail, member limits, duplicate detection.
"""

from tests.conftest import (
    assert_ok,
    assert_redirect,
    assert_forbidden,
    make_user,
    login,
)
from app.models.organization import Organization, OrganizationUser, slugify, unique_slug


# ── Slug Generation ───────────────────────────────────────────────────────────


def test_slugify_basic():
    assert slugify("Acme Corporation") == "acme-corporation"


def test_slugify_special_characters():
    assert slugify("Webb & Associates!") == "webb-associates"


def test_slugify_extra_spaces():
    assert slugify("  Chen   Consulting  ") == "chen-consulting"


def test_unique_slug_no_conflict(app):
    with app.app_context():
        slug = unique_slug("Totally New Company")
        assert slug == "totally-new-company"


def test_unique_slug_conflict(app, db):
    org = Organization(
        name="Dupe Corp",
        slug="dupe-corp",
        billing_email="dupe@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    with app.app_context():
        slug = unique_slug("Dupe Corp")
        assert slug == "dupe-corp-1"


# ── Organization Model ────────────────────────────────────────────────────────


def test_organization_owner_property(db):
    from app.models.user import User, set_password

    user = User(
        email="owner@test.com",
        first_name="Org",
        last_name="Owner",
        role="client",
        is_active=True,
    )
    set_password(user, "password123")
    db.session.add(user)

    org = Organization(
        name="Owner Test Co",
        slug="owner-test-co",
        billing_email="owner@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()

    membership = OrganizationUser(
        user_id=user.id,
        org_id=org.id,
        org_role="owner",
    )
    db.session.add(membership)
    db.session.commit()

    assert org.owner.email == "owner@test.com"


def test_organization_owner_none_when_no_members(db):
    org = Organization(
        name="Empty Co",
        slug="empty-co",
        billing_email="empty@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    assert org.owner is None


def test_organization_member_count(db):
    from app.models.user import User, set_password

    org = Organization(
        name="Count Co",
        slug="count-co",
        billing_email="count@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()

    for i in range(2):
        u = User(
            email=f"member{i}@test.com",
            first_name="Member",
            last_name=f"{i}",
            role="client",
            is_active=True,
        )
        set_password(u, "password123")
        db.session.add(u)
        db.session.flush()
        db.session.add(OrganizationUser(user_id=u.id, org_id=org.id, org_role="member"))

    db.session.commit()
    assert org.member_count == 2


def test_organization_repr(db):
    org = Organization(
        name="Repr Co",
        slug="repr-co",
        billing_email="repr@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    assert "repr-co" in repr(org)


# ── User Model ────────────────────────────────────────────────────────────────


def test_user_organization_property(db):
    from app.models.user import User, set_password

    user = User(
        email="orgprop@test.com",
        first_name="Org",
        last_name="Prop",
        role="client",
        is_active=True,
    )
    set_password(user, "password123")
    db.session.add(user)

    org = Organization(
        name="Prop Co",
        slug="prop-co",
        billing_email="orgprop@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()

    db.session.add(OrganizationUser(user_id=user.id, org_id=org.id, org_role="owner"))
    db.session.commit()

    assert user.organization.name == "Prop Co"


def test_user_organization_none_when_no_membership(db):
    from app.models.user import User, set_password

    user = User(
        email="nomembership@test.com",
        first_name="No",
        last_name="Membership",
        role="client",
        is_active=True,
    )
    set_password(user, "password123")
    db.session.add(user)
    db.session.commit()

    assert user.organization is None


def test_user_full_name(db):
    user = make_user(db, "fullname@test.com", "password123", "John", "Doe", "client")
    assert user.full_name == "John Doe"


# ── Organization Routes — Access Control ─────────────────────────────────────


def test_organizations_page_redirects_when_logged_out(client):
    response = client.get("/staff/organizations", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_staff_can_access_organizations(staff_client):
    response = staff_client.get("/staff/organizations")
    assert_ok(response)
    assert b"Organizations" in response.data


def test_admin_can_access_organizations(admin_client):
    response = admin_client.get("/staff/organizations")
    assert_ok(response)


def test_client_cannot_access_organizations(client_client):
    response = client_client.get("/staff/organizations")
    assert_forbidden(response)


def test_staff_cannot_access_create_organization(staff_client):
    response = staff_client.get("/staff/organizations/new")
    assert_forbidden(response)


def test_admin_can_access_create_organization(admin_client):
    response = admin_client.get("/staff/organizations/new")
    assert_ok(response)
    assert b"Add Organization" in response.data


# ── Organization Creation ─────────────────────────────────────────────────────


def test_admin_can_create_organization(admin_client):
    response = admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "Test Organization",
            "billing_email": "billing@testorg.com",
            "owner_first_name": "Jane",
            "owner_last_name": "Smith",
            "owner_email": "jane@testorg.com",
        },
        follow_redirects=True,
    )
    assert b"created" in response.data
    assert b"invite" in response.data.lower()


def test_create_organization_auto_generates_slug(admin_client, db):
    admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "Slug Test Company",
            "billing_email": "billing@slugtest.com",
            "owner_first_name": "Jane",
            "owner_last_name": "Smith",
            "owner_email": "jane@slugtest.com",
        },
        follow_redirects=True,
    )
    org = Organization.query.filter_by(name="Slug Test Company").first()
    assert org is not None
    assert org.slug == "slug-test-company"


def test_create_organization_creates_owner_user(admin_client, db):
    from app.models.user import User

    admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "Owner Creation Co",
            "billing_email": "billing@ownercreation.com",
            "owner_first_name": "New",
            "owner_last_name": "Owner",
            "owner_email": "newowner@ownercreation.com",
        },
        follow_redirects=True,
    )
    user = User.query.filter_by(email="newowner@ownercreation.com").first()
    assert user is not None
    assert user.role == "client"
    assert user.is_active is True


def test_create_organization_links_owner_membership(admin_client, db):
    admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "Membership Co",
            "billing_email": "billing@membership.com",
            "owner_first_name": "Mem",
            "owner_last_name": "Ber",
            "owner_email": "member@membership.com",
        },
        follow_redirects=True,
    )
    org = Organization.query.filter_by(name="Membership Co").first()
    assert org is not None
    membership = OrganizationUser.query.filter_by(
        org_id=org.id, org_role="owner"
    ).first()
    assert membership is not None
    assert membership.user.email == "member@membership.com"


def test_create_organization_duplicate_name(admin_client, db):
    org = Organization(
        name="Existing Org",
        slug="existing-org",
        billing_email="existing@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()

    response = admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "Existing Org",
            "billing_email": "other@test.com",
            "owner_first_name": "Jane",
            "owner_last_name": "Smith",
            "owner_email": "jane@other.com",
        },
        follow_redirects=True,
    )
    assert b"already exists" in response.data


def test_create_organization_duplicate_owner_email(admin_client, db):
    make_user(db, "taken@test.com", "password123", "Taken", "User", "client")

    response = admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "New Org",
            "billing_email": "billing@neworg.com",
            "owner_first_name": "Jane",
            "owner_last_name": "Smith",
            "owner_email": "taken@test.com",
        },
        follow_redirects=True,
    )
    assert b"already exists" in response.data


def test_create_organization_invalid_billing_email(admin_client):
    response = admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "Bad Email Org",
            "billing_email": "not-an-email",
            "owner_first_name": "Jane",
            "owner_last_name": "Smith",
            "owner_email": "jane@bademailorg.com",
        },
        follow_redirects=True,
    )
    assert b"Invalid email" in response.data


def test_create_organization_missing_org_name(admin_client):
    response = admin_client.post(
        "/staff/organizations/new",
        data={
            "org_name": "",
            "billing_email": "billing@test.com",
            "owner_first_name": "Jane",
            "owner_last_name": "Smith",
            "owner_email": "jane@test.com",
        },
        follow_redirects=True,
    )
    assert b"This field is required" in response.data


# ── Organization Detail ───────────────────────────────────────────────────────


def test_organization_detail_loads(admin_client, db):
    org = Organization(
        name="Detail Co",
        slug="detail-co",
        billing_email="detail@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()

    response = admin_client.get("/staff/organizations/detail-co")
    assert_ok(response)
    assert b"Detail Co" in response.data


def test_organization_detail_shows_members(admin_client, db):
    from app.models.user import User, set_password

    org = Organization(
        name="Members Co",
        slug="members-co",
        billing_email="members@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()

    user = User(
        email="orgmember@test.com",
        first_name="Org",
        last_name="Member",
        role="client",
        is_active=True,
    )
    set_password(user, "password123")
    db.session.add(user)
    db.session.flush()

    db.session.add(OrganizationUser(user_id=user.id, org_id=org.id, org_role="owner"))
    db.session.commit()

    response = admin_client.get("/staff/organizations/members-co")
    assert_ok(response)
    assert b"Org" in response.data
    assert b"Member" in response.data


def test_organization_detail_404_for_unknown_slug(admin_client):
    response = admin_client.get("/staff/organizations/does-not-exist")
    assert response.status_code == 404


def test_staff_can_view_assigned_org_detail(client, db, app):
    staff = make_user(db, "staffdet@test.com", "password123", "Staff", "Det", "staff")

    org = Organization(
        name="Assigned Detail Co",
        slug="assigned-detail-co",
        billing_email="assigneddetail@test.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()

    s = db.session.get(staff.__class__, staff.id)
    s.assigned_orgs.append(org)
    db.session.commit()

    with app.test_client() as c:
        login(c, "staffdet@test.com", "password123")
        response = c.get("/staff/organizations/assigned-detail-co")
        assert_ok(response)
        assert b"Assigned Detail Co" in response.data
