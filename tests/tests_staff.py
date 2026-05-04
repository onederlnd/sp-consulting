"""
test_utils_and_staff.py — Tests for app/utils/analytics.py
and app/routes/staff/routes.py
"""

import io
from unittest.mock import patch

from tests.conftest import (
    assert_ok,
    assert_redirect,
    assert_forbidden,
    make_user,
    login,
)
from app.extensions import db as _db  # noqa
from app.models.organization import Organization, OrganizationUser
from app.models.document import Document, DocumentVersion
from app.models.user import User


def make_org(db, name="Staff Test Org", slug="staff-test-org"):
    org = Organization(
        name=name,
        slug=slug,
        billing_email=f"billing@{slug}.com",
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()
    return org


def make_doc(db, org, staff_user, name="Test Doc", client_visible=True):
    doc = Document(
        org_id=org.id,
        uploaded_by_id=staff_user.id,
        name=name,
        description="A test document",
        file_type="pdf",
        client_visible=client_visible,
        is_active=True,
    )
    db.session.add(doc)
    db.session.flush()
    return doc


def make_doc_version(db, doc, staff_user, version_number=1):
    version = DocumentVersion(
        document_id=doc.id,
        uploaded_by_id=staff_user.id,
        filename=f"v{version_number}_test.pdf",
        original_filename="test.pdf",
        file_size=1024,
        version_number=version_number,
    )
    db.session.add(version)
    db.session.flush()
    return version


# ── Staff routes: access control ──────────────────────────────────────────────


def test_staff_index_redirects_logged_out(client):
    response = client.get("/staff/", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_staff_index_accessible_to_staff(staff_client):
    assert_ok(staff_client.get("/staff/"))


def test_staff_index_accessible_to_admin(admin_client):
    assert_ok(admin_client.get("/staff/"))


def test_staff_index_forbidden_for_client(client_client):
    assert_forbidden(client_client.get("/staff/"))


def test_settings_requires_admin(staff_client):
    assert_forbidden(staff_client.get("/staff/settings"))


def test_settings_accessible_to_admin(admin_client):
    assert_ok(admin_client.get("/staff/settings"))


def test_users_requires_admin(staff_client):
    assert_forbidden(staff_client.get("/staff/users"))


def test_users_accessible_to_admin(admin_client, db):
    assert_ok(admin_client.get("/staff/users"))


# ── Staff routes: clients list ────────────────────────────────────────────────


def test_clients_list_admin_sees_all(admin_client, db):
    make_user(db, "clienta@test.com", "pw", "Client", "A", "client")
    make_user(db, "clientb@test.com", "pw", "Client", "B", "client")
    db.session.commit()
    response = admin_client.get("/staff/clients")
    assert_ok(response)
    assert b"Client" in response.data


def test_clients_list_staff_sees_assigned(app, db, client):
    staff = make_user(db, "staffcl@test.com", "password123", "Staff", "CL", "staff")
    org = make_org(db, slug="staff-cl-org")
    client_u = make_user(db, "orgclient@test.com", "pw", "Org", "Client", "client")
    db.session.add(
        OrganizationUser(user_id=client_u.id, org_id=org.id, org_role="member")
    )
    staff_obj = db.session.get(User, staff.id)
    staff_obj.assigned_orgs.append(org)
    db.session.commit()

    with app.test_client() as c:
        login(c, "staffcl@test.com", "password123")
        response = c.get("/staff/clients")
        assert_ok(response)
        assert b"Org" in response.data


# ── Staff routes: engagements ─────────────────────────────────────────────────


def test_engagements_accessible_to_staff(staff_client):
    assert_ok(staff_client.get("/staff/engagements"))


# ── Staff routes: create user ─────────────────────────────────────────────────


def test_create_user_get(admin_client):
    assert_ok(admin_client.get("/staff/users/new"))


def test_create_user_success(admin_client, db):
    response = admin_client.post(
        "/staff/users/new",
        data={
            "email": "newstaff@test.com",
            "first_name": "New",
            "last_name": "Staff",
            "role": "staff",
            "password": "Secure123!",
            "confirm_password": "Secure123!",
        },
        follow_redirects=True,
    )
    assert_ok(response)
    assert User.query.filter_by(email="newstaff@test.com").first() is not None


def test_create_user_duplicate_email(admin_client, db):
    make_user(db, "dupe@test.com", "pw", "Dupe", "User", "staff")
    db.session.commit()

    response = admin_client.post(
        "/staff/users/new",
        data={
            "email": "dupe@test.com",
            "first_name": "Another",
            "last_name": "User",
            "role": "staff",
            "password": "Secure123!",
            "confirm_password": "Secure123!",
        },
        follow_redirects=True,
    )
    assert b"already exists" in response.data


def test_create_user_requires_admin(staff_client):
    assert_forbidden(staff_client.get("/staff/users/new"))


# ── Staff routes: documents list ──────────────────────────────────────────────


def test_documents_list_accessible_to_staff(staff_client, db):
    assert_ok(staff_client.get("/staff/documents"))


def test_documents_list_admin_sees_all(admin_client, db, staff_user):
    org = make_org(db, slug="doc-list-org")
    make_doc(db, org, staff_user, name="Admin Doc")
    db.session.commit()
    response = admin_client.get("/staff/documents")
    assert_ok(response)
    assert b"Admin Doc" in response.data


def test_documents_list_staff_sees_assigned_orgs(app, db):
    staff = make_user(db, "staffdoc@test.com", "password123", "Staff", "Doc", "staff")
    org = make_org(db, slug="staffdoc-org")
    make_doc(db, org, staff, name="Staff Visible Doc")
    staff_obj = db.session.get(User, staff.id)
    staff_obj.assigned_orgs.append(org)
    db.session.commit()

    with app.test_client() as c:
        login(c, "staffdoc@test.com", "password123")
        response = c.get("/staff/documents")
        assert_ok(response)
        assert b"Staff Visible Doc" in response.data


# ── Staff routes: upload document ─────────────────────────────────────────────


def test_upload_document_get(staff_client, db):
    make_org(db, slug="upload-get-org")
    db.session.commit()
    assert_ok(staff_client.get("/staff/documents/upload"))


def test_upload_document_disallowed_extension(staff_client, db):
    org = make_org(db, slug="upload-ext-org")
    db.session.commit()

    data = {
        "name": "Bad File",
        "description": "test",
        "client_visible": "y",
        "org_id": str(org.id),
        "file": (io.BytesIO(b"bad content"), "malware.exe"),
    }
    response = staff_client.post(
        "/staff/documents/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"not allowed" in response.data


def test_upload_document_no_org_selected(staff_client, db):
    make_org(db, slug="upload-noorg-org")
    db.session.commit()

    data = {
        "name": "Missing Org",
        "description": "test",
        "client_visible": "y",
        "org_id": "99999",
        "file": (io.BytesIO(b"pdf content"), "test.pdf"),
    }
    response = staff_client.post(
        "/staff/documents/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"select an organization" in response.data


def test_upload_document_success(staff_client, db, tmp_path, app):
    org = make_org(db, slug="upload-ok-org")
    db.session.commit()

    with (
        patch("app.routes.staff.routes.get_upload_path") as mock_path,
        patch("app.routes.staff.routes.os.makedirs"),
        patch("app.routes.staff.routes.os.path.getsize", return_value=512),
    ):
        upload_file = tmp_path / "test.pdf"
        upload_file.write_bytes(b"fake pdf")
        mock_path.return_value = str(upload_file)

        data = {
            "name": "My Doc",
            "description": "desc",
            "client_visible": "y",
            "org_id": str(org.id),
            "file": (io.BytesIO(b"pdf content"), "test.pdf"),
        }
        response = staff_client.post(
            "/staff/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
    assert b"uploaded successfully" in response.data
    assert Document.query.filter_by(name="My Doc").first() is not None


# ── Staff routes: document detail ─────────────────────────────────────────────


def test_document_detail_loads(staff_client, db, staff_user):
    org = make_org(db, slug="doc-detail-org")
    doc = make_doc(db, org, staff_user, name="Detail Doc")
    db.session.commit()

    response = staff_client.get(f"/staff/documents/{doc.id}")
    assert_ok(response)
    assert b"Detail Doc" in response.data


def test_document_detail_404_unknown(staff_client):
    response = staff_client.get("/staff/documents/99999")
    assert response.status_code == 404


# ── Staff routes: edit document ───────────────────────────────────────────────


def test_edit_document_success(staff_client, db, staff_user):
    org = make_org(db, slug="edit-doc-org")
    doc = make_doc(db, org, staff_user, name="Original Name")
    db.session.commit()

    response = staff_client.post(
        f"/staff/documents/{doc.id}/edit",
        data={
            "name": "Updated Name",
            "description": "Updated desc",
            "client_visible": "y",
        },
        follow_redirects=True,
    )
    assert_ok(response)
    db.session.expire(doc)
    assert doc.name == "Updated Name"


# ── Staff routes: delete document ─────────────────────────────────────────────


def test_delete_document_soft_deletes(staff_client, db, staff_user):
    org = make_org(db, slug="delete-doc-org")
    doc = make_doc(db, org, staff_user, name="To Delete")
    db.session.commit()

    response = staff_client.post(
        f"/staff/documents/{doc.id}/delete",
        follow_redirects=True,
    )
    assert_ok(response)
    db.session.expire(doc)
    assert doc.is_active is False


def test_delete_document_404_unknown(staff_client):
    response = staff_client.post("/staff/documents/99999/delete")
    assert response.status_code == 404


# ── Staff routes: download document ──────────────────────────────────────────


def test_download_document_no_version_404(staff_client, db, staff_user):
    org = make_org(db, slug="dl-noversion-org")
    doc = make_doc(db, org, staff_user, name="No Version Doc")
    db.session.commit()

    response = staff_client.get(f"/staff/documents/{doc.id}/download")
    assert response.status_code == 404


def test_download_document_missing_file_404(staff_client, db, staff_user):
    org = make_org(db, slug="dl-missing-org")
    doc = make_doc(db, org, staff_user, name="Missing File Doc")
    make_doc_version(db, doc, staff_user)
    db.session.commit()

    response = staff_client.get(f"/staff/documents/{doc.id}/download")
    assert response.status_code == 404


def test_download_document_success(staff_client, db, staff_user, tmp_path):
    org = make_org(db, slug="dl-ok-org")
    doc = make_doc(db, org, staff_user, name="Download Doc")
    make_doc_version(db, doc, staff_user)
    db.session.commit()

    fake_file = tmp_path / "v1_test.pdf"
    fake_file.write_bytes(b"fake pdf content")

    with (
        patch("app.routes.staff.routes.get_upload_path", return_value=str(fake_file)),
        patch("app.routes.staff.routes.os.path.exists", return_value=True),
    ):
        response = staff_client.get(f"/staff/documents/{doc.id}/download")
    assert response.status_code == 200


# ── Staff routes: upload version ──────────────────────────────────────────────


def test_upload_version_disallowed_extension(staff_client, db, staff_user):
    org = make_org(db, slug="ver-ext-org")
    doc = make_doc(db, org, staff_user, name="Version Ext Doc")
    db.session.commit()

    data = {"file": (io.BytesIO(b"bad"), "bad.exe")}
    response = staff_client.post(
        f"/staff/documents/{doc.id}/upload-version",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"not allowed" in response.data


def test_upload_version_success(staff_client, db, staff_user, tmp_path):
    org = make_org(db, slug="ver-ok-org")
    doc = make_doc(db, org, staff_user, name="Version Ok Doc")
    make_doc_version(db, doc, staff_user, version_number=1)
    db.session.commit()

    with (
        patch("app.routes.staff.routes.get_upload_path") as mock_path,
        patch("app.routes.staff.routes.os.makedirs"),
        patch("app.routes.staff.routes.os.path.getsize", return_value=512),
    ):
        upload_file = tmp_path / "v2_test.pdf"
        upload_file.write_bytes(b"v2 content")
        mock_path.return_value = str(upload_file)

        data = {"file": (io.BytesIO(b"v2 pdf"), "test.pdf")}
        response = staff_client.post(
            f"/staff/documents/{doc.id}/upload-version",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
    assert b"Version 2" in response.data
    assert DocumentVersion.query.filter_by(document_id=doc.id).count() == 2
