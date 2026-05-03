from flask import render_template, redirect, url_for, flash
from flask_login import current_user
from app.routes.staff import staff_bp
from app.utils.decorators import staff_required, admin_required
from app.extensions import db
from app.models.user import User, set_password
from app.models.organization import Organization, OrganizationUser, unique_slug
from app.forms.auth import make_create_user_form
from app.forms.staff import make_create_organization_form
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
        # Check for duplicate org name
        existing_org = Organization.query.filter_by(name=form.org_name.data).first()
        if existing_org:
            flash("An organization with that name already exists.", "danger")
            return render_template("staff/create_organization.html", form=form)

        # Check for duplicate user email
        existing_user = User.query.filter_by(
            email=form.owner_email.data.lower()
        ).first()
        if existing_user:
            flash("A user with that email already exists.", "danger")
            return render_template("staff/create_organization.html", form=form)

        # Create org
        org = Organization(
            name=form.org_name.data,
            slug=unique_slug(form.org_name.data),
            billing_email=form.billing_email.data.lower(),
            is_active=True,
        )
        db.session.add(org)
        db.session.flush()

        # Create owner user with unusable placeholder password
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

        # Link owner to org
        membership = OrganizationUser(
            user_id=owner.id,
            org_id=org.id,
            org_role="owner",
        )
        db.session.add(membership)
        db.session.commit()

        # Send password reset email so owner sets their own password
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
            user
            for org in current_user.assigned_orgs
            for m in org.members
            for user in [m.user]
            if user.role == "client"
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


@staff_bp.route("/documents")
@staff_required
def documents():
    return render_template("staff/documents.html")


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
