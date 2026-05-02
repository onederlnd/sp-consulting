from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, limiter
from app.models.user import User, check_password, set_password
from app.forms.auth import (
    make_login_form,
    make_password_reset_request_form,
    make_password_reset_form,
)
from app.routes.auth import auth_bp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
import bcrypt  # noqa: F401

# ── Login ────────────────────────────────────────────────────────────────────


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        if current_user.role in ("admin", "staff"):
            return redirect(url_for("staff.index"))
        return redirect(url_for("client.index"))

    form = make_login_form()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.is_active and check_password(user, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            if user.role in ("admin", "staff"):
                return redirect(url_for("staff.index"))
            return redirect(next_page or url_for("main.index"))
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


# ── Logout ───────────────────────────────────────────────────────────────────


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ── Password Reset Request ───────────────────────────────────────────────────


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password_request():
    form = make_password_reset_request_form()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            pass
            # token = generate_reset_token(user.email)

            # TODO: send email with token
            # send_password_reset_email(user, token)
            flash("If that email exists, a reset link has been sent.", "info")
        else:
            flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password_request.html", form=form)


# ── Password Reset ───────────────────────────────────────────────────────────


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.reset_password_request"))

    form = make_password_reset_form()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            set_password(user, form.password.data)
            db.session.commit()
            flash("Your password has been updated.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


# ── Token helpers ────────────────────────────────────────────────────────────


def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="password-reset")


def verify_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, salt="password-reset", max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    return email
