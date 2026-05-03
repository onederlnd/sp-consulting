"""
test_documents.py — Document management tests
Covers: upload, download, versioning, visibility, access control,
        model properties, form validation.
"""

import io
import os
from tests.conftest import (
    assert_ok,
    assert_redirect,
    assert_forbidden,
    make_user,
)
from app.models.document import Document, DocumentVersion, allowed_file, get_upload_path
from app.models.organization import Organization


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_org(db, name, slug, email="billing@test.com"):
    org = Organization(
        name=name,
        slug=slug,
        billing_email=email,
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()
    return org


def make_document(db, org, uploader, name="Test Doc", client_visible=True):
    doc = Document(
        org_id=org.id,
        uploaded_by_id=uploader.id,
        name=name,
        description="A test document.",
        file_type="pdf",
        client_visible=client_visible,
        is_active=True,
    )
    db.session.add(doc)
    db.session.flush()
    return doc


def make_version(db, doc, uploader, version_number=1, filename="test.pdf"):
    version = DocumentVersion(
        document_id=doc.id,
        uploaded_by_id=uploader.id,
        filename=f"v{version_number}_{filename}",
        original_filename=filename,
        file_size=1024,
        version_number=version_number,
    )
    db.session.add(version)
    db.session.flush()
    return version


def fake_file(filename="test.pdf", content=b"fake pdf content"):
    return (io.BytesIO(content), filename)


# ── allowed_file ──────────────────────────────────────────────────────────────


def test_allowed_file_pdf():
    assert allowed_file("report.pdf") is True


def test_allowed_file_docx():
    assert allowed_file("report.docx") is True


def test_allowed_file_xlsx():
    assert allowed_file("data.xlsx") is True


def test_allowed_file_csv():
    assert allowed_file("data.csv") is True


def test_allowed_file_pptx():
    assert allowed_file("slides.pptx") is True


def test_allowed_file_png():
    assert allowed_file("image.png") is True


def test_allowed_file_jpg():
    assert allowed_file("image.jpg") is True


def test_allowed_file_disallowed():
    assert allowed_file("malware.exe") is False


def test_allowed_file_zip_disallowed():
    assert allowed_file("archive.zip") is False


def test_allowed_file_no_extension():
    assert allowed_file("nodotfile") is False


# ── Document model ────────────────────────────────────────────────────────────


def test_document_latest_version(db, admin_user):
    org = make_org(db, "Latest Co", "latest-co")
    doc = make_document(db, org, admin_user)
    make_version(db, doc, admin_user, version_number=1)
    make_version(db, doc, admin_user, version_number=2)
    db.session.commit()

    assert doc.latest_version.version_number == 2


def test_document_latest_version_none_when_no_versions(db, admin_user):
    org = make_org(db, "No Version Co", "no-version-co")
    doc = make_document(db, org, admin_user)
    db.session.commit()

    assert doc.latest_version is None


def test_document_version_count(db, admin_user):
    org = make_org(db, "Count Co", "count-co")
    doc = make_document(db, org, admin_user)
    make_version(db, doc, admin_user, version_number=1)
    make_version(db, doc, admin_user, version_number=2)
    make_version(db, doc, admin_user, version_number=3)
    db.session.commit()

    assert doc.version_count == 3


def test_document_repr(db, admin_user):
    org = make_org(db, "Repr Co", "repr-doc-co")
    doc = make_document(db, org, admin_user, name="My Report")
    db.session.commit()

    assert "My Report" in repr(doc)


# ── DocumentVersion model ─────────────────────────────────────────────────────


def test_version_file_size_display_bytes(db, admin_user):
    org = make_org(db, "Size Co B", "size-co-b")
    doc = make_document(db, org, admin_user)
    version = DocumentVersion(
        document_id=doc.id,
        uploaded_by_id=admin_user.id,
        filename="v1_test.pdf",
        original_filename="test.pdf",
        file_size=512,
        version_number=1,
    )
    db.session.add(version)
    db.session.commit()
    assert "B" in version.file_size_display


def test_version_file_size_display_kb(db, admin_user):
    org = make_org(db, "Size Co KB", "size-co-kb")
    doc = make_document(db, org, admin_user)
    version = DocumentVersion(
        document_id=doc.id,
        uploaded_by_id=admin_user.id,
        filename="v1_test.pdf",
        original_filename="test.pdf",
        file_size=2048,
        version_number=1,
    )
    db.session.add(version)
    db.session.commit()
    assert "KB" in version.file_size_display


def test_version_file_size_display_mb(db, admin_user):
    org = make_org(db, "Size Co MB", "size-co-mb")
    doc = make_document(db, org, admin_user)
    version = DocumentVersion(
        document_id=doc.id,
        uploaded_by_id=admin_user.id,
        filename="v1_test.pdf",
        original_filename="test.pdf",
        file_size=2 * 1024 * 1024,
        version_number=1,
    )
    db.session.add(version)
    db.session.commit()
    assert "MB" in version.file_size_display


def test_version_repr(db, admin_user):
    org = make_org(db, "Repr Version Co", "repr-version-co")
    doc = make_document(db, org, admin_user)
    version = make_version(db, doc, admin_user)
    db.session.commit()
    assert "v1" in repr(version)


# ── Staff document routes — access control ────────────────────────────────────


def test_documents_page_redirects_when_logged_out(client):
    response = client.get("/staff/documents", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_staff_can_access_documents(staff_client):
    response = staff_client.get("/staff/documents")
    assert_ok(response)
    assert b"Documents" in response.data


def test_admin_can_access_documents(admin_client):
    response = admin_client.get("/staff/documents")
    assert_ok(response)


def test_client_cannot_access_staff_documents_page(client_client):
    response = client_client.get("/staff/documents")
    assert_forbidden(response)


def test_upload_document_page_loads(staff_client):
    response = staff_client.get("/staff/documents/upload")
    assert_ok(response)
    assert b"Upload Document" in response.data


def test_client_cannot_access_upload_page(client_client):
    response = client_client.get("/staff/documents/upload")
    assert_forbidden(response)


# ── Staff document upload ─────────────────────────────────────────────────────


def test_staff_can_upload_document(staff_client, staff_user, db, app):
    org = make_org(db, "Upload Test Co", "upload-test-co")
    from app.models.user import User

    s = db.session.get(User, staff_user.id)
    s.assigned_orgs.append(org)
    db.session.commit()

    response = staff_client.post(
        "/staff/documents/upload",
        data={
            "name": "Test Report",
            "description": "A test upload",
            "org_id": org.id,
            "client_visible": True,
            "file": fake_file("test.pdf"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"uploaded successfully" in response.data

    doc = Document.query.filter_by(name="Test Report").first()
    assert doc is not None
    assert doc.org_id == org.id
    assert doc.version_count == 1

    # cleanup uploaded file
    with app.app_context():
        path = get_upload_path(org.slug, doc.id, "v1_test.pdf")
        if os.path.exists(path):
            os.remove(path)


def test_upload_document_disallowed_file_type(staff_client, staff_user, db):
    org = make_org(db, "Bad File Co", "bad-file-co")
    from app.models.user import User

    s = db.session.get(User, staff_user.id)
    s.assigned_orgs.append(org)
    db.session.commit()

    response = staff_client.post(
        "/staff/documents/upload",
        data={
            "name": "Bad File",
            "org_id": org.id,
            "file": fake_file("malware.exe", b"bad content"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"File type not allowed" in response.data


def test_upload_document_no_org_selected(staff_client, db):
    response = staff_client.post(
        "/staff/documents/upload",
        data={
            "name": "No Org Doc",
            "file": fake_file("test.pdf"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"select an organization" in response.data


def test_upload_document_missing_name(staff_client, staff_user, db):
    org = make_org(db, "Missing Name Co", "missing-name-co")
    from app.models.user import User

    s = db.session.get(User, staff_user.id)
    s.assigned_orgs.append(org)
    db.session.commit()

    response = staff_client.post(
        "/staff/documents/upload",
        data={
            "name": "",
            "org_id": org.id,
            "file": fake_file("test.pdf"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"This field is required" in response.data


# ── Staff document detail ─────────────────────────────────────────────────────


def test_document_detail_loads(staff_client, staff_user, db):
    org = make_org(db, "Detail Doc Co", "detail-doc-co")
    doc = make_document(db, org, staff_user, name="Detail Test")
    make_version(db, doc, staff_user)
    db.session.commit()

    response = staff_client.get(f"/staff/documents/{doc.id}")
    assert_ok(response)
    assert b"Detail Test" in response.data


def test_document_detail_shows_version_history(staff_client, staff_user, db):
    org = make_org(db, "Version History Co", "version-history-co")
    doc = make_document(db, org, staff_user, name="Versioned Doc")
    make_version(db, doc, staff_user, version_number=1)
    make_version(db, doc, staff_user, version_number=2)
    db.session.commit()

    response = staff_client.get(f"/staff/documents/{doc.id}")
    assert_ok(response)
    assert b"v1" in response.data
    assert b"v2" in response.data


def test_document_detail_404_for_unknown(staff_client):
    response = staff_client.get("/staff/documents/99999")
    assert response.status_code == 404


# ── Staff document edit ───────────────────────────────────────────────────────


def test_edit_document_updates_name(staff_client, staff_user, db):
    org = make_org(db, "Edit Co", "edit-co")
    doc = make_document(db, org, staff_user, name="Old Name")
    db.session.commit()

    response = staff_client.post(
        f"/staff/documents/{doc.id}/edit",
        data={
            "name": "New Name",
            "description": "Updated description",
            "client_visible": True,
        },
        follow_redirects=True,
    )
    assert b"Document updated" in response.data
    db.session.refresh(doc)
    assert doc.name == "New Name"


def test_edit_document_toggle_visibility(staff_client, staff_user, db):
    org = make_org(db, "Toggle Co", "toggle-co")
    doc = make_document(db, org, staff_user, client_visible=True)
    db.session.commit()

    staff_client.post(
        f"/staff/documents/{doc.id}/edit",
        data={
            "name": doc.name,
            "description": "",
            # client_visible omitted = unchecked checkbox = False
        },
        follow_redirects=True,
    )
    db.session.refresh(doc)
    assert doc.client_visible is False


# ── Staff document delete ─────────────────────────────────────────────────────


def test_delete_document_soft_deletes(staff_client, staff_user, db):
    org = make_org(db, "Delete Co", "delete-co")
    doc = make_document(db, org, staff_user, name="To Be Deleted")
    db.session.commit()

    response = staff_client.post(
        f"/staff/documents/{doc.id}/delete",
        follow_redirects=True,
    )
    assert b"has been removed" in response.data
    db.session.refresh(doc)
    assert doc.is_active is False


def test_deleted_document_not_in_list(staff_client, staff_user, db):
    org = make_org(db, "Hidden Co", "hidden-co")
    doc = make_document(db, org, staff_user, name="Hidden Doc")
    doc.is_active = False
    db.session.commit()

    response = staff_client.get("/staff/documents")
    assert b"Hidden Doc" not in response.data


# ── Staff upload new version ──────────────────────────────────────────────────


def test_upload_new_version(staff_client, staff_user, db, app):
    org = make_org(db, "New Version Co", "new-version-co")
    doc = make_document(db, org, staff_user, name="Versioned")
    make_version(db, doc, staff_user, version_number=1)
    db.session.commit()

    response = staff_client.post(
        f"/staff/documents/{doc.id}/upload-version",
        data={"file": fake_file("v2_report.pdf")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Version 2 uploaded" in response.data
    db.session.refresh(doc)
    assert doc.version_count == 2

    # cleanup
    with app.app_context():
        for v in doc.versions:
            path = get_upload_path(org.slug, doc.id, v.filename)
            if os.path.exists(path):
                os.remove(path)


# ── Staff document download ───────────────────────────────────────────────────


def test_download_document(staff_client, staff_user, db, app, tmp_path):
    org = make_org(db, "Download Co", "download-co")
    doc = make_document(db, org, staff_user, name="Downloadable")
    version = make_version(db, doc, staff_user)
    db.session.commit()

    # Create a real file at the expected path
    with app.app_context():
        path = get_upload_path(org.slug, doc.id, version.filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"fake pdf content")

    response = staff_client.get(f"/staff/documents/{doc.id}/download")
    assert response.status_code == 200
    assert response.data == b"fake pdf content"

    # cleanup
    if os.path.exists(path):
        os.remove(path)


def test_download_document_404_when_file_missing(staff_client, staff_user, db):
    org = make_org(db, "Missing File Co", "missing-file-co")
    doc = make_document(db, org, staff_user, name="No File")
    make_version(db, doc, staff_user)
    db.session.commit()

    response = staff_client.get(f"/staff/documents/{doc.id}/download")
    assert response.status_code == 404


def test_download_document_404_when_no_versions(staff_client, staff_user, db):
    org = make_org(db, "No Versions Co", "no-versions-co")
    doc = make_document(db, org, staff_user, name="No Versions")
    db.session.commit()

    response = staff_client.get(f"/staff/documents/{doc.id}/download")
    assert response.status_code == 404


# ── Client document access ────────────────────────────────────────────────────


def test_client_sees_visible_documents(client_client, client_user, db, app):
    from app.models.user import User

    u = db.session.get(User, client_user.id)

    org = make_org(db, "Client Docs Co", "client-docs-co")
    from app.models.organization import OrganizationUser

    db.session.add(OrganizationUser(user_id=u.id, org_id=org.id, org_role="owner"))

    admin = make_user(db, "docadmin@test.com", "password123", "Doc", "Admin", "admin")
    doc = make_document(db, org, admin, name="Visible Report", client_visible=True)
    make_version(db, doc, admin)
    db.session.commit()

    response = client_client.get("/client/documents")
    assert_ok(response)
    assert b"Visible Report" in response.data


def test_client_cannot_see_hidden_documents(client_client, client_user, db):
    from app.models.user import User

    u = db.session.get(User, client_user.id)

    org = make_org(db, "Hidden Docs Co", "hidden-docs-co")
    from app.models.organization import OrganizationUser

    db.session.add(OrganizationUser(user_id=u.id, org_id=org.id, org_role="owner"))

    admin = make_user(
        db, "hiddendocadmin@test.com", "password123", "Hidden", "Admin", "admin"
    )
    doc = make_document(db, org, admin, name="Hidden Report", client_visible=False)
    make_version(db, doc, admin)
    db.session.commit()

    response = client_client.get("/client/documents")
    assert_ok(response)
    assert b"Hidden Report" not in response.data


def test_client_download_visible_document(client_client, client_user, db, app):
    from app.models.user import User
    from app.models.organization import OrganizationUser

    u = db.session.get(User, client_user.id)
    org = make_org(db, "Client Download Co", "client-download-co")
    db.session.add(OrganizationUser(user_id=u.id, org_id=org.id, org_role="owner"))

    admin = make_user(
        db, "dlclientadmin@test.com", "password123", "DL", "Admin", "admin"
    )
    doc = make_document(db, org, admin, name="Client Download", client_visible=True)
    version = make_version(db, doc, admin)
    db.session.commit()

    with app.app_context():
        path = get_upload_path(org.slug, doc.id, version.filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"client file content")

    response = client_client.get(f"/client/documents/{doc.id}/download")
    assert response.status_code == 200
    assert response.data == b"client file content"

    if os.path.exists(path):
        os.remove(path)


def test_client_cannot_download_hidden_document(client_client, client_user, db):
    from app.models.user import User
    from app.models.organization import OrganizationUser

    u = db.session.get(User, client_user.id)
    org = make_org(db, "Hidden DL Co", "hidden-dl-co")
    db.session.add(OrganizationUser(user_id=u.id, org_id=org.id, org_role="owner"))

    admin = make_user(
        db, "hiddendladmin@test.com", "password123", "HDL", "Admin", "admin"
    )
    doc = make_document(db, org, admin, name="Hidden DL", client_visible=False)
    make_version(db, doc, admin)
    db.session.commit()

    response = client_client.get(f"/client/documents/{doc.id}/download")
    assert response.status_code == 404


def test_client_cannot_download_other_orgs_document(client_client, client_user, db):
    other_org = make_org(db, "Other Org DL", "other-org-dl")
    admin = make_user(
        db, "otherorgrg@test.com", "password123", "Other", "Admin", "admin"
    )
    doc = make_document(db, other_org, admin, name="Other Org Doc", client_visible=True)
    make_version(db, doc, admin)
    db.session.commit()

    response = client_client.get(f"/client/documents/{doc.id}/download")
    assert response.status_code in (403, 404)


def test_staff_cannot_access_client_download(staff_client, staff_user, db):
    org = make_org(db, "Staff DL Co", "staff-dl-co")
    doc = make_document(db, org, staff_user, name="Staff DL Doc")
    make_version(db, doc, staff_user)
    db.session.commit()

    response = staff_client.get(f"/client/documents/{doc.id}/download")
    assert_forbidden(response)
