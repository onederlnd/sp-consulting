from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail


def send_password_reset_email(user, token):
    reset_url = f"{current_app.config.get('BASE_URL', '')}/auth/reset-password/{token}"
    msg = Message(
        subject="Reset Your Password — Sunceray Patterson Consulting",
        recipients=[user.email],
        body=render_template(
            "email/reset_password.txt",
            user=user,
            reset_url=reset_url,
        ),
        html=render_template(
            "email/reset_password.html",
            user=user,
            reset_url=reset_url,
        ),
    )
    mail.send(msg)


# flake8 off
def send_contact_email(form_data):
    msg = Message(
        subject=(
            f"New Contact: {form_data['service']} — "
            f"{form_data['first_name']} {form_data['last_name']}"
        ),
        recipients=[current_app.config.get("MAIL_DEFAULT_SENDER")],
        reply_to=form_data["email"],
        body=render_template(
            "email/contact.txt",
            data=form_data,
        ),
        html=render_template(
            "email/contact.html",
            data=form_data,
        ),
    )
    mail.send(msg)


def send_invite_email(user, org, token):
    invite_url = f"{current_app.config.get('BASE_URL', '')}/auth/reset-password/{token}"
    msg = Message(
        subject=f"You've been invited to {org.name} — Sunceray Patterson Consulting",
        recipients=[user.email],
        body=render_template(
            "email/invite.txt",
            user=user,
            org=org,
            invite_url=invite_url,
        ),
        html=render_template(
            "email/invite.html",
            user=user,
            org=org,
            invite_url=invite_url,
        ),
    )
    mail.send(msg)
