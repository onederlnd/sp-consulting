"""
test_email.py — Email utility tests
Covers: password reset email, invite email, mail.send() calls.
"""

from unittest.mock import patch, MagicMock
import pytest
from app.utils.email import send_password_reset_email, send_invite_email
from app.models.organization import Organization


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_user():
    user = MagicMock()
    user.email = "test@test.com"
    user.first_name = "Test"
    user.last_name = "User"
    return user


@pytest.fixture()
def mock_org():
    org = MagicMock(spec=Organization)
    org.name = "Test Organization"
    org.slug = "test-organization"
    return org


# ── Password Reset Email ──────────────────────────────────────────────────────


def test_send_password_reset_email_calls_mail_send(app, mock_user):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_password_reset_email(mock_user, "test-token-123")
            assert mock_mail.send.called


def test_send_password_reset_email_sends_to_correct_recipient(app, mock_user):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_password_reset_email(mock_user, "test-token-123")
            msg = mock_mail.send.call_args[0][0]
            assert "test@test.com" in msg.recipients


def test_send_password_reset_email_subject(app, mock_user):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_password_reset_email(mock_user, "test-token-123")
            msg = mock_mail.send.call_args[0][0]
            assert "Reset" in msg.subject
            assert "Sunceray Patterson" in msg.subject


def test_send_password_reset_email_contains_token_url(app, mock_user):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_password_reset_email(mock_user, "test-token-abc")
            msg = mock_mail.send.call_args[0][0]
            assert "test-token-abc" in msg.body
            assert "test-token-abc" in msg.html


def test_send_password_reset_email_uses_base_url(app, mock_user):
    with app.app_context():
        app.config["BASE_URL"] = "https://app.test.com"
        with patch("app.utils.email.mail") as mock_mail:
            send_password_reset_email(mock_user, "mytoken")
            msg = mock_mail.send.call_args[0][0]
            assert "https://app.test.com" in msg.body


# ── Invite Email ──────────────────────────────────────────────────────────────


def test_send_invite_email_calls_mail_send(app, mock_user, mock_org):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_invite_email(mock_user, mock_org, "invite-token-123")
            assert mock_mail.send.called


def test_send_invite_email_sends_to_correct_recipient(app, mock_user, mock_org):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_invite_email(mock_user, mock_org, "invite-token-123")
            msg = mock_mail.send.call_args[0][0]
            assert "test@test.com" in msg.recipients


def test_send_invite_email_subject_contains_org_name(app, mock_user, mock_org):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_invite_email(mock_user, mock_org, "invite-token-123")
            msg = mock_mail.send.call_args[0][0]
            assert "Test Organization" in msg.subject


def test_send_invite_email_contains_invite_url(app, mock_user, mock_org):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_invite_email(mock_user, mock_org, "invite-token-xyz")
            msg = mock_mail.send.call_args[0][0]
            assert "invite-token-xyz" in msg.body
            assert "invite-token-xyz" in msg.html


def test_send_invite_email_contains_org_name_in_body(app, mock_user, mock_org):
    with app.app_context():
        with patch("app.utils.email.mail") as mock_mail:
            send_invite_email(mock_user, mock_org, "invite-token-xyz")
            msg = mock_mail.send.call_args[0][0]
            assert "Test Organization" in msg.body
            assert "Test Organization" in msg.html


def test_send_invite_email_uses_base_url(app, mock_user, mock_org):
    with app.app_context():
        app.config["BASE_URL"] = "https://app.test.com"
        with patch("app.utils.email.mail") as mock_mail:
            send_invite_email(mock_user, mock_org, "myinvitetoken")
            msg = mock_mail.send.call_args[0][0]
            assert "https://app.test.com" in msg.body


# ── Mail suppressed in testing ────────────────────────────────────────────────


def test_mail_suppressed_in_test_config(app):
    """Confirm MAIL_SUPPRESS_SEND is True in testing so no real emails go out."""
    assert app.config.get("MAIL_SUPPRESS_SEND") is True


def test_reset_email_does_not_raise_when_suppressed(app, mock_user):
    """End-to-end: send goes through Flask-Mail with suppression, no mock needed."""
    with app.app_context():
        try:
            send_password_reset_email(mock_user, "suppress-test-token")
        except Exception as e:
            pytest.fail(f"send_password_reset_email raised unexpectedly: {e}")


def test_invite_email_does_not_raise_when_suppressed(app, mock_user, mock_org):
    """End-to-end: send goes through Flask-Mail with suppression, no mock needed."""
    with app.app_context():
        try:
            send_invite_email(mock_user, mock_org, "suppress-invite-token")
        except Exception as e:
            pytest.fail(f"send_invite_email raised unexpectedly: {e}")
