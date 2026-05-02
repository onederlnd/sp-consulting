from flask import render_template, redirect, url_for, flash
from flask_login import current_user
from app.routes.staff import staff_bp
from app.utils.decorators import staff_required, admin_required
from app.extensions import db
from app.models.user import User, set_password
from app.forms.auth import make_create_user_form


@staff_bp.route("/")
@staff_required
def index():
    return render_template("staff/dashboard.html")


@staff_bp.route("/clients")
@staff_required
def clients():
    if current_user.role == "admin":
        all_clients = User.query.filter_by(role="client").order_by(User.last_name).all()
    else:
        all_clients = current_user.assigned_clients
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
