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
