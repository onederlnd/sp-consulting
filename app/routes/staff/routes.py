import os
from werkzeug.utils import secure_filename
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    send_file,
    abort,
    request,
)
from flask_login import current_user
from app.routes.staff import staff_bp
from app.utils.decorators import staff_required, admin_required
from app.extensions import db
from app.models.user import User, set_password
from app.models.organization import Organization, OrganizationUser, unique_slug
from app.models.document import Document, DocumentVersion, get_upload_path, allowed_file
from app.forms.auth import make_create_user_form
from app.forms.staff import (
    make_create_organization_form,
    make_upload_document_form,
    make_edit_document_form,
    make_upload_version_form,
)
from app.utils.email import send_invite_email
from app.routes.auth.routes import generate_reset_token


@staff_bp.route("/")
@staff_required
def index():
    return render_template("staff/dashboard.html")


@staff_bp.route("/organizations")
@staff_required
def organizations():
    if current_user.role == "admin":
        all_orgs = Organization.query.order_by(Organization.name).all()
    else:
        all_orgs = current_user.assigned_orgs
    return render_template("staff/organizations.html", organizations=all_orgs)


@staff_bp.route("/organizations/new", methods=["GET", "POST"])
@admin_required
def create_organization():
    form = make_create_organization_form()
    if form.validate_on_submit():
        existing_org = Organization.query.filter_by(name=form.org_name.data).first()
        if existing_org:
            flash("An organization with that name already exists.", "danger")
            return render_template("staff/create_organization.html", form=form)

        existing_user = User.query.filter_by(
            email=form.owner_email.data.lower()
        ).first()
        if existing_user:
            flash("A user with that email already exists.", "danger")
            return render_template("staff/create_organization.html", form=form)

        org = Organization(
            name=form.org_name.data,
            slug=unique_slug(form.org_name.data),
            billing_email=form.billing_email.data.lower(),
            is_active=True,
        )
        db.session.add(org)
        db.session.flush()

        owner = User(
            email=form.owner_email.data.lower(),
            first_name=form.owner_first_name.data,
            last_name=form.owner_last_name.data,
            role="client",
            is_active=True,
        )
        set_password(owner, db.engine.url.database + str(org.id))
        db.session.add(owner)
        db.session.flush()

        membership = OrganizationUser(
            user_id=owner.id,
            org_id=org.id,
            org_role="owner",
        )
        db.session.add(membership)
        db.session.commit()

        token = generate_reset_token(owner.email)
        send_invite_email(owner, org, token)

        flash(
            f"Organization '{org.name}' created. "
            f"An invite has been sent to {owner.email}.",
            "success",
        )
        return redirect(url_for("staff.organizations"))

    return render_template("staff/create_organization.html", form=form)


@staff_bp.route("/organizations/<slug>")
@staff_required
def organization_detail(slug):
    org = Organization.query.filter_by(slug=slug).first_or_404()
    return render_template("staff/organization_detail.html", org=org)


@staff_bp.route("/clients")
@staff_required
def clients():
    if current_user.role == "admin":
        all_clients = User.query.filter_by(role="client").order_by(User.last_name).all()
    else:
        all_clients = [
            m.user
            for org in current_user.assigned_orgs
            for m in org.members
            if m.user.role == "client"
        ]
    return render_template("staff/clients.html", clients=all_clients)


@staff_bp.route("/engagements")
@staff_required
def engagements():
    return render_template("staff/engagements.html")


@staff_bp.route("/settings")
@admin_required
def settings():
    return render_template("staff/settings.html")


# ── Document routes ───────────────────────────────────────────────────────────


@staff_bp.route("/documents")
@staff_required
def documents():
    if current_user.role == "admin":
        all_docs = (
            Document.query.filter_by(is_active=True)
            .order_by(Document.created_at.desc())
            .all()
        )
    else:
        org_ids = [o.id for o in current_user.assigned_orgs]
        all_docs = (
            Document.query.filter(
                Document.org_id.in_(org_ids),
                Document.is_active == True,  # noqa: E712
            )
            .order_by(Document.created_at.desc())
            .all()
        )
    return render_template("staff/documents.html", documents=all_docs)


@staff_bp.route("/documents/upload", methods=["GET", "POST"])
@staff_required
def upload_document():
    form = make_upload_document_form()

    if current_user.role == "admin":
        orgs = Organization.query.order_by(Organization.name).all()
    else:
        orgs = current_user.assigned_orgs

    if form.validate_on_submit():
        file = form.file.data
        if not allowed_file(file.filename):
            flash("File type not allowed.", "danger")
            return render_template("staff/upload_document.html", form=form, orgs=orgs)

        org_id = request.form.get("org_id", type=int)
        org = Organization.query.get(org_id)
        if not org:
            flash("Please select an organization.", "danger")
            return render_template("staff/upload_document.html", form=form, orgs=orgs)

        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit(".", 1)[1].lower()

        doc = Document(
            org_id=org.id,
            uploaded_by_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            file_type=file_ext,
            client_visible=form.client_visible.data,
            is_active=True,
        )
        db.session.add(doc)
        db.session.flush()

        stored_filename = f"v1_{original_filename}"
        upload_path = get_upload_path(org.slug, doc.id, stored_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)

        version = DocumentVersion(
            document_id=doc.id,
            uploaded_by_id=current_user.id,
            filename=stored_filename,
            original_filename=original_filename,
            file_size=os.path.getsize(upload_path),
            version_number=1,
        )
        db.session.add(version)
        db.session.commit()

        flash(f"'{doc.name}' uploaded successfully.", "success")
        return redirect(url_for("staff.documents"))

    return render_template("staff/upload_document.html", form=form, orgs=orgs)


@staff_bp.route("/documents/<int:doc_id>")
@staff_required
def document_detail(doc_id):
    doc = Document.query.get_or_404(doc_id)
    upload_form = make_upload_version_form()
    edit_form = make_edit_document_form()
    edit_form.name.data = doc.name
    edit_form.description.data = doc.description
    edit_form.client_visible.data = doc.client_visible
    return render_template(
        "staff/document_detail.html",
        doc=doc,
        upload_form=upload_form,
        edit_form=edit_form,
    )


@staff_bp.route("/documents/<int:doc_id>/edit", methods=["POST"])
@staff_required
def edit_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    form = make_edit_document_form()
    if form.validate_on_submit():
        doc.name = form.name.data
        doc.description = form.description.data
        doc.client_visible = form.client_visible.data
        db.session.commit()
        flash("Document updated.", "success")
    return redirect(url_for("staff.document_detail", doc_id=doc.id))


@staff_bp.route("/documents/<int:doc_id>/upload-version", methods=["POST"])
@staff_required
def upload_version(doc_id):
    doc = Document.query.get_or_404(doc_id)
    form = make_upload_version_form()
    if form.validate_on_submit():
        file = form.file.data
        if not allowed_file(file.filename):
            flash("File type not allowed.", "danger")
            return redirect(url_for("staff.document_detail", doc_id=doc.id))

        original_filename = secure_filename(file.filename)
        next_version = (doc.version_count or 0) + 1
        stored_filename = f"v{next_version}_{original_filename}"

        org = doc.organization
        upload_path = get_upload_path(org.slug, doc.id, stored_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)

        version = DocumentVersion(
            document_id=doc.id,
            uploaded_by_id=current_user.id,
            filename=stored_filename,
            original_filename=original_filename,
            file_size=os.path.getsize(upload_path),
            version_number=next_version,
        )
        db.session.add(version)
        db.session.commit()

        flash(f"Version {next_version} uploaded.", "success")
    return redirect(url_for("staff.document_detail", doc_id=doc.id))


@staff_bp.route("/documents/<int:doc_id>/download")
@staff_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    version = doc.latest_version
    if not version:
        abort(404)
    org = doc.organization
    path = get_upload_path(org.slug, doc.id, version.filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(
        path,
        as_attachment=True,
        download_name=version.original_filename,
    )


@staff_bp.route("/documents/<int:doc_id>/delete", methods=["POST"])
@staff_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    doc.is_active = False
    db.session.commit()
    flash(f"'{doc.name}' has been removed.", "success")
    return redirect(url_for("staff.documents"))


# ── User management ───────────────────────────────────────────────────────────


@staff_bp.route("/users")
@admin_required
def users():
    all_users = User.query.order_by(User.last_name).all()
    return render_template("staff/users.html", users=all_users)


@staff_bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def create_user():
    form = make_create_user_form()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash("A user with that email already exists.", "danger")
            return render_template("staff/create_user.html", form=form)
        user = User(
            email=form.email.data.lower(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
            is_active=True,
        )
        set_password(user, form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"User {user.email} created successfully.", "success")
        return redirect(url_for("staff.users"))
    return render_template("staff/create_user.html", form=form)
