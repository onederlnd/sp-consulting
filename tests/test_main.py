"""
test_main.py — Public marketing site route tests
"""

from tests.conftest import assert_ok


def test_homepage_loads(client):
    response = client.get("/")
    assert_ok(response)


def test_about_page_loads(client):
    response = client.get("/about")
    assert_ok(response)


def test_contact_page_loads(client):
    response = client.get("/contact")
    assert_ok(response)
    assert b"Send a Message" in response.data


def test_contact_form_submission(client):
    response = client.post(
        "/contact",
        data={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@test.com",
            "organization": "Test Co",
            "service": "strategy",
            "message": "I need help with my business strategy.",
        },
        follow_redirects=True,
    )
    assert b"message has been sent" in response.data


def test_contact_form_missing_required_fields(client):
    response = client.post(
        "/contact",
        data={
            "first_name": "",
            "last_name": "",
            "email": "",
            "message": "",
        },
        follow_redirects=True,
    )
    assert b"This field is required" in response.data


def test_contact_form_invalid_email(client):
    response = client.post(
        "/contact",
        data={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "not-an-email",
            "message": "Hello",
        },
        follow_redirects=True,
    )
    assert b"Invalid email" in response.data


def test_contact_form_sends_email(client):
    from unittest.mock import patch

    with patch("app.routes.main.routes.send_contact_email") as mock_send:
        response = client.post(
            "/contact",
            data={
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@test.com",
                "organization": "Test Co",
                "service": "strategy",
                "message": "I need help.",
            },
            follow_redirects=True,
        )
        assert mock_send.called
        assert b"message has been sent" in response.data
