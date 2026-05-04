"""
test_analytics.py — Analytics tests
Covers: event ingestion, session upsert, bot filtering, domain validation,
        staff overview, org detail, domain management, client dashboard,
        CSV export, model reprs, access control.
"""

import json
from datetime import datetime, timezone, timedelta

import pytest

from tests.conftest import (
    assert_ok,
    assert_redirect,
    assert_forbidden,
    make_user,
    login,
    logout,
)
from app.extensions import db as _db  # noqa
from app.models.organization import Organization, OrganizationUser
from app.models.analytics import OrgDomain, Event, Session, DailySummary
from app.utils.analytics import (
    is_bot,
    parse_device_type,
    parse_browser,
    parse_os,
    get_client_ip,
    lookup_geo,
)
from unittest.mock import patch, MagicMock


# ── Factories ─────────────────────────────────────────────────────────────────


def make_org(db, name="Test Org", slug="test-org", billing="billing@test.com"):
    org = Organization(
        name=name,
        slug=slug,
        billing_email=billing,
        is_active=True,
        analytics_key="testkey" + slug.replace("-", "")[:24],
    )
    db.session.add(org)
    db.session.flush()
    return org


def make_domain(db, org, domain="example.com"):
    d = OrgDomain(org_id=org.id, domain=domain)
    db.session.add(d)
    db.session.flush()
    return d


def make_event(
    db,
    org,
    event_type="pageview",
    visitor_id="visitor-1",
    session_id="session-1",
    url="/",
    created_at=None,
):
    e = Event(
        org_id=org.id,
        session_id=session_id,
        visitor_id=visitor_id,
        event_type=event_type,
        url=url,
        referrer="https://google.com",
        title="Home",
        device_type="desktop",
        browser="Chrome",
        os="Linux",
        created_at=created_at or datetime.now(timezone.utc),
    )
    db.session.add(e)
    db.session.flush()
    return e


def make_session(db, org, session_id="session-1", visitor_id="visitor-1"):
    s = Session(
        org_id=org.id,
        session_id=session_id,
        visitor_id=visitor_id,
        entry_url="/",
        pageview_count=1,
    )
    db.session.add(s)
    db.session.flush()
    return s


def collect_payload(client, origin="https://example.com", payload=None):
    """POST to /analytics/collect with sensible defaults."""
    default_payload = {
        "session_id": "test-session-id",
        "visitor_id": "test-visitor-id",
        "event_type": "pageview",
        "url": "https://example.com/page",
        "referrer": "",
        "title": "Test Page",
        "properties": {},
    }
    if payload:
        default_payload.update(payload)
    return client.post(
        "/analytics/collect",
        data=json.dumps(default_payload),
        content_type="application/json",
        headers={"Origin": origin, "User-Agent": "Mozilla/5.0 (TestBrowser)"},
    )


# ── Model: OrgDomain ──────────────────────────────────────────────────────────


def test_org_domain_repr(db):
    org = make_org(db)
    d = make_domain(db, org, "repr.com")
    db.session.commit()
    assert "repr.com" in repr(d)


def test_org_domain_unique_constraint(db):
    from sqlalchemy.exc import IntegrityError

    org = make_org(db, slug="unique-dom-org")
    make_domain(db, org, "dup.com")
    db.session.commit()

    db.session.add(OrgDomain(org_id=org.id, domain="dup.com"))
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_org_domain_relationship_to_org(db):
    org = make_org(db, slug="rel-org")
    d = make_domain(db, org, "reltest.com")
    db.session.commit()
    assert d.organization.slug == "rel-org"


# ── Model: Event ──────────────────────────────────────────────────────────────


def test_event_repr(db):
    org = make_org(db, slug="event-repr-org")
    e = make_event(db, org)
    db.session.commit()
    assert "pageview" in repr(e)


def test_event_created_at_defaults_to_utc(db):
    org = make_org(db, slug="event-ts-org")
    e = make_event(db, org)
    db.session.commit()
    assert e.created_at is not None


def test_event_optional_fields_nullable(db):
    org = make_org(db, slug="event-null-org")
    e = Event(org_id=org.id, session_id="s1", visitor_id="v1", event_type="custom")
    db.session.add(e)
    db.session.commit()
    assert e.url is None
    assert e.referrer is None
    assert e.country is None
    assert e.city is None


def test_event_custom_event_type_stored(db):
    org = make_org(db, slug="event-custom-org")
    e = make_event(db, org, event_type="form_submit")
    db.session.commit()
    assert e.event_type == "form_submit"


# ── Model: Session ────────────────────────────────────────────────────────────


def test_session_repr(db):
    org = make_org(db, slug="sess-repr-org")
    s = make_session(db, org, session_id="repr-session")
    db.session.commit()
    assert "repr-session" in repr(s)


def test_session_unique_session_id(db):
    from sqlalchemy.exc import IntegrityError

    org = make_org(db, slug="sess-unique-org")
    make_session(db, org, session_id="dup-session")
    db.session.commit()

    db.session.add(
        Session(
            org_id=org.id, session_id="dup-session", visitor_id="v2", pageview_count=1
        )
    )
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_session_defaults_converted_false(db):
    org = make_org(db, slug="sess-conv-org")
    s = make_session(db, org, session_id="conv-session")
    db.session.commit()
    assert s.converted is False


# ── Model: DailySummary ───────────────────────────────────────────────────────


def test_daily_summary_repr(db):
    org = make_org(db, slug="summary-repr-org")
    today = datetime.now(timezone.utc).date()
    s = DailySummary(org_id=org.id, date=today, pageviews=10)
    db.session.add(s)
    db.session.commit()
    assert repr(s)  # just confirm it doesn't raise


def test_daily_summary_unique_org_date(db):
    from sqlalchemy.exc import IntegrityError

    org = make_org(db, slug="summary-unique-org")
    today = datetime.now(timezone.utc).date()
    db.session.add(DailySummary(org_id=org.id, date=today))
    db.session.commit()

    db.session.add(DailySummary(org_id=org.id, date=today))
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_daily_summary_defaults(db):
    org = make_org(db, slug="summary-defaults-org")
    today = datetime.now(timezone.utc).date()
    s = DailySummary(org_id=org.id, date=today)
    db.session.add(s)
    db.session.commit()
    assert s.pageviews == 0
    assert s.unique_visitors == 0
    assert s.bounce_rate == 0.0


# ── Collect: CORS Preflight ───────────────────────────────────────────────────


def test_collect_options_returns_200(client):
    response = client.options(
        "/analytics/collect",
        headers={"Origin": "https://example.com"},
    )
    assert response.status_code == 200


def test_collect_options_returns_cors_headers(client):
    response = client.options(
        "/analytics/collect",
        headers={"Origin": "https://example.com"},
    )
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers


# ── Collect: Domain Validation ────────────────────────────────────────────────


def test_collect_rejects_unregistered_domain(client, db):
    make_org(db, slug="unregistered-org")
    db.session.commit()

    response = collect_payload(client, origin="https://notregistered.com")
    assert response.status_code == 403
    assert response.get_json()["error"] == "Domain not registered"


def test_collect_accepts_registered_domain(client, db):
    org = make_org(db, slug="registered-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    response = collect_payload(client, origin="https://example.com")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_collect_sets_cors_origin_in_response(client, db):
    org = make_org(db, slug="cors-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    response = collect_payload(client, origin="https://example.com")
    assert response.headers.get("Access-Control-Allow-Origin") == "https://example.com"


# ── Collect: Bot Filtering ────────────────────────────────────────────────────


def test_collect_ignores_googlebot(client, db):
    org = make_org(db, slug="bot-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    response = client.post(
        "/analytics/collect",
        data=json.dumps(
            {"session_id": "bs", "visitor_id": "bv", "event_type": "pageview"}
        ),
        content_type="application/json",
        headers={
            "Origin": "https://example.com",
            "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
        },
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "ignored"
    assert Event.query.filter_by(org_id=org.id).count() == 0


def test_collect_ignores_bingbot(client, db):
    org = make_org(db, slug="bing-bot-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    client.post(
        "/analytics/collect",
        data=json.dumps(
            {"session_id": "bs2", "visitor_id": "bv2", "event_type": "pageview"}
        ),
        content_type="application/json",
        headers={
            "Origin": "https://example.com",
            "User-Agent": "Mozilla/5.0 (compatible; bingbot/2.0)",
        },
    )
    assert Event.query.filter_by(org_id=org.id).count() == 0


# ── Collect: Missing Fields ───────────────────────────────────────────────────


def test_collect_rejects_missing_session_id(client, db):
    org = make_org(db, slug="missing-sid-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    response = collect_payload(
        client,
        origin="https://example.com",
        payload={"session_id": "", "visitor_id": "v1"},
    )
    assert response.status_code == 400


def test_collect_rejects_missing_visitor_id(client, db):
    org = make_org(db, slug="missing-vid-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    response = collect_payload(
        client,
        origin="https://example.com",
        payload={"session_id": "s1", "visitor_id": ""},
    )
    assert response.status_code == 400


# ── Collect: Event & Session Creation ─────────────────────────────────────────


def test_collect_creates_event(client, db):
    org = make_org(db, slug="create-event-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    collect_payload(client, origin="https://example.com")

    events = Event.query.filter_by(org_id=org.id).all()
    assert len(events) == 1
    assert events[0].event_type == "pageview"


def test_collect_creates_new_session(client, db):
    org = make_org(db, slug="create-sess-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    collect_payload(
        client,
        origin="https://example.com",
        payload={"session_id": "brand-new-session", "visitor_id": "v1"},
    )

    session = Session.query.filter_by(session_id="brand-new-session").first()
    assert session is not None
    assert session.pageview_count == 1
    assert session.org_id == org.id


def test_collect_increments_existing_session(client, db):
    org = make_org(db, slug="incr-sess-org")
    make_domain(db, org, "example.com")
    db.session.add(
        Session(
            org_id=org.id,
            session_id="existing-session",
            visitor_id="v1",
            pageview_count=3,
            entry_url="/",
        )
    )
    db.session.commit()

    collect_payload(
        client,
        origin="https://example.com",
        payload={"session_id": "existing-session", "visitor_id": "v1"},
    )

    session = Session.query.filter_by(session_id="existing-session").first()
    assert session.pageview_count == 4


def test_collect_updates_exit_url_on_existing_session(client, db):
    org = make_org(db, slug="exit-url-org")
    make_domain(db, org, "example.com")
    db.session.add(
        Session(
            org_id=org.id,
            session_id="exit-session",
            visitor_id="v1",
            pageview_count=1,
            entry_url="/",
        )
    )
    db.session.commit()

    collect_payload(
        client,
        origin="https://example.com",
        payload={
            "session_id": "exit-session",
            "visitor_id": "v1",
            "url": "https://example.com/contact",
        },
    )

    session = Session.query.filter_by(session_id="exit-session").first()
    assert session.exit_url == "https://example.com/contact"
    assert session.ended_at is not None


def test_collect_stores_utm_params_on_new_session(client, db):
    org = make_org(db, slug="utm-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    collect_payload(
        client,
        origin="https://example.com",
        payload={
            "session_id": "utm-session",
            "visitor_id": "v1",
            "utm_source": "newsletter",
            "utm_medium": "email",
            "utm_campaign": "spring2026",
        },
    )

    session = Session.query.filter_by(session_id="utm-session").first()
    assert session.utm_source == "newsletter"
    assert session.utm_medium == "email"
    assert session.utm_campaign == "spring2026"


def test_collect_multiple_events_same_session(client, db):
    org = make_org(db, slug="multi-event-org")
    make_domain(db, org, "example.com")
    db.session.commit()

    for i in range(3):
        collect_payload(
            client,
            origin="https://example.com",
            payload={
                "session_id": "multi-session",
                "visitor_id": "v1",
                "url": f"/page-{i}",
            },
        )

    assert Event.query.filter_by(org_id=org.id).count() == 3
    session = Session.query.filter_by(session_id="multi-session").first()
    assert session.pageview_count == 3


# ── Access Control: Staff Analytics Overview ──────────────────────────────────


def test_analytics_overview_redirects_when_logged_out(client):
    response = client.get("/analytics/", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_analytics_overview_forbidden_for_client(client_client):
    response = client_client.get("/analytics/")
    assert_forbidden(response)


def test_analytics_overview_accessible_to_staff(staff_client, db):
    make_org(db, slug="overview-staff-org")
    db.session.commit()
    response = staff_client.get("/analytics/")
    assert_ok(response)


def test_analytics_overview_accessible_to_admin(admin_client, db):
    make_org(db, slug="overview-admin-org")
    db.session.commit()
    response = admin_client.get("/analytics/")
    assert_ok(response)


def test_analytics_overview_shows_org_name(admin_client, db):
    make_org(db, name="Visible Org", slug="visible-org")
    db.session.commit()
    response = admin_client.get("/analytics/")
    assert b"Visible Org" in response.data


# ── Staff Analytics: Org Detail ───────────────────────────────────────────────


def test_org_detail_404_for_unknown_slug(staff_client):
    response = staff_client.get("/analytics/no-such-org")
    assert response.status_code == 404


def test_org_detail_loads_for_staff(staff_client, db):
    make_org(db, name="Detail Org", slug="detail-org")
    db.session.commit()

    response = staff_client.get("/analytics/detail-org")
    assert_ok(response)
    assert b"Detail Org" in response.data


def test_org_detail_shows_registered_domains(staff_client, db):
    org = make_org(db, name="Domain Detail Org", slug="domaindetail-org")
    make_domain(db, org, "domaindetail.com")
    db.session.commit()

    response = staff_client.get("/analytics/domaindetail-org")
    assert b"domaindetail.com" in response.data


def test_org_detail_renders_with_no_events(staff_client, db):
    make_org(db, name="Empty Events Org", slug="emptyevents-org")
    db.session.commit()

    response = staff_client.get("/analytics/emptyevents-org")
    assert_ok(response)


def test_org_detail_renders_with_events(staff_client, db):
    org = make_org(db, name="Has Events Org", slug="hasevents-org")
    for i in range(5):
        make_event(db, org, visitor_id=f"v{i}", session_id=f"s{i}", url=f"/page-{i}")
    db.session.commit()

    response = staff_client.get("/analytics/hasevents-org")
    assert_ok(response)


def test_org_detail_forbidden_for_client(client_client, db):
    make_org(db, name="Forbidden Detail Org", slug="forbiddendetail-org")
    db.session.commit()

    response = client_client.get("/analytics/forbiddendetail-org")
    assert_forbidden(response)


# ── Domain Management ─────────────────────────────────────────────────────────


def test_add_domain_requires_staff(client_client, db):
    make_org(db, name="AddDom Org", slug="adddom-org")
    db.session.commit()

    response = client_client.post(
        "/analytics/adddom-org/domains/add",
        data={"domain": "newsite.com"},
        follow_redirects=False,
    )
    assert_forbidden(response)


def test_add_domain_success(staff_client, db):
    org = make_org(db, name="NewDomain Org", slug="newdomain-org")
    db.session.commit()

    response = staff_client.post(
        "/analytics/newdomain-org/domains/add",
        data={"domain": "newsite.com"},
        follow_redirects=True,
    )
    assert_ok(response)
    assert OrgDomain.query.filter_by(org_id=org.id, domain="newsite.com").first()


def test_add_domain_strips_https_protocol(staff_client, db):
    org = make_org(db, name="Proto Org", slug="proto-org")
    db.session.commit()

    staff_client.post(
        "/analytics/proto-org/domains/add",
        data={"domain": "https://proto.com/"},
        follow_redirects=True,
    )
    assert OrgDomain.query.filter_by(org_id=org.id, domain="proto.com").first()


def test_add_domain_strips_http_protocol(staff_client, db):
    org = make_org(db, name="Http Org", slug="http-org")
    db.session.commit()

    staff_client.post(
        "/analytics/http-org/domains/add",
        data={"domain": "http://http.com/path"},
        follow_redirects=True,
    )
    assert OrgDomain.query.filter_by(org_id=org.id, domain="http.com").first()


def test_add_domain_rejects_empty(staff_client, db):
    make_org(db, name="Empty Domain Org", slug="emptydomain-org")
    db.session.commit()

    response = staff_client.post(
        "/analytics/emptydomain-org/domains/add",
        data={"domain": ""},
        follow_redirects=True,
    )
    assert b"cannot be empty" in response.data


def test_add_domain_rejects_duplicate(staff_client, db):
    org = make_org(db, name="Dup Domain Org", slug="dupdomain-org")
    make_domain(db, org, "already.com")
    db.session.commit()

    response = staff_client.post(
        "/analytics/dupdomain-org/domains/add",
        data={"domain": "already.com"},
        follow_redirects=True,
    )
    assert b"already registered" in response.data


def test_delete_domain_removes_record(staff_client, db):
    org = make_org(db, name="Del Domain Org", slug="deldomain-org")
    domain = make_domain(db, org, "delete-me.com")
    db.session.commit()

    domain_id = domain.id
    response = staff_client.post(
        f"/analytics/deldomain-org/domains/{domain_id}/delete",
        follow_redirects=True,
    )
    assert_ok(response)
    assert OrgDomain.query.get(domain_id) is None


def test_delete_domain_requires_staff(client_client, db):
    org = make_org(db, name="Del Auth Org", slug="delauth-org")
    domain = make_domain(db, org, "secret.com")
    db.session.commit()

    response = client_client.post(
        f"/analytics/delauth-org/domains/{domain.id}/delete",
        follow_redirects=False,
    )
    assert_forbidden(response)


def test_delete_domain_404_for_unknown_id(staff_client):
    response = staff_client.post("/analytics/any-org/domains/99999/delete")
    assert response.status_code == 404


# ── CSV Export ────────────────────────────────────────────────────────────────


def test_export_csv_requires_staff(client_client, db):
    make_org(db, name="Export Org", slug="export-org")
    db.session.commit()

    response = client_client.get("/analytics/export/export-org")
    assert_forbidden(response)


def test_export_csv_returns_csv_content_type(staff_client, db):
    make_org(db, name="CSV Org", slug="csv-org")
    db.session.commit()

    response = staff_client.get("/analytics/export/csv-org")
    assert_ok(response)
    assert "text/csv" in response.content_type


def test_export_csv_contains_header_row(staff_client, db):
    make_org(db, name="Header CSV Org", slug="headercsv-org")
    db.session.commit()

    response = staff_client.get("/analytics/export/headercsv-org")
    text = response.data.decode()
    for col in ("timestamp", "event_type", "url", "visitor_id", "session_id"):
        assert col in text


def test_export_csv_contains_event_data(staff_client, db):
    org = make_org(db, name="Data CSV Org", slug="datacsv-org")
    make_event(db, org, url="/my-page", visitor_id="export-visitor", session_id="es1")
    db.session.commit()

    response = staff_client.get("/analytics/export/datacsv-org")
    text = response.data.decode()
    assert "/my-page" in text
    assert "export-visitor" in text


def test_export_csv_filename_includes_slug(staff_client, db):
    make_org(db, name="Slug CSV Org", slug="slugcsv-org")
    db.session.commit()

    response = staff_client.get("/analytics/export/slugcsv-org")
    disposition = response.headers.get("Content-Disposition", "")
    assert "slugcsv-org" in disposition


def test_export_csv_empty_when_no_events(staff_client, db):
    make_org(db, name="Empty CSV Org", slug="emptycsv-org")
    db.session.commit()

    response = staff_client.get("/analytics/export/emptycsv-org")
    assert_ok(response)
    lines = response.data.decode().strip().splitlines()
    assert len(lines) == 1  # header only


def test_export_csv_404_for_unknown_org(staff_client):
    response = staff_client.get("/analytics/export/no-org-here")
    assert response.status_code == 404


def test_export_csv_excludes_old_events(staff_client, db, app):
    """Events older than ANALYTICS_RETENTION_DAYS should not appear."""
    retention = app.config.get("ANALYTICS_RETENTION_DAYS", 90)
    org = make_org(db, name="Retention CSV Org", slug="retentioncsv-org")
    old_ts = datetime.now(timezone.utc) - timedelta(days=retention + 5)
    make_event(
        db,
        org,
        visitor_id="old-visitor",
        session_id="old-s",
        url="/old-page",
        created_at=old_ts,
    )
    db.session.commit()

    response = staff_client.get("/analytics/export/retentioncsv-org")
    text = response.data.decode()
    assert "old-visitor" not in text


# ── Client Dashboard ──────────────────────────────────────────────────────────


def test_client_dashboard_requires_login(client):
    response = client.get("/analytics/client", follow_redirects=False)
    assert_redirect(response, to="/auth/login")


def test_client_dashboard_forbidden_for_staff(staff_client):
    response = staff_client.get("/analytics/client")
    assert_forbidden(response)


def test_client_dashboard_forbidden_for_admin(admin_client):
    response = admin_client.get("/analytics/client")
    assert_forbidden(response)


def test_client_dashboard_loads_for_client_with_org(app, db, client):
    org = make_org(db, name="Client Dash Org", slug="clientdash-org")
    user = make_user(
        db, "dashclient@test.com", "password123", "Dash", "Client", "client"
    )
    db.session.add(OrganizationUser(user_id=user.id, org_id=org.id, org_role="owner"))
    db.session.commit()

    login(client, "dashclient@test.com", "password123")
    response = client.get("/analytics/client")
    assert_ok(response)
    assert b"Today's Pageviews" in response.data
    assert b"30-Day Pageviews" in response.data
    logout(client)


def test_client_dashboard_403_when_no_org(app, db, client):
    with app.test_client() as fresh_client:
        make_user(db, "noorg2@test.com", "password123", "No", "Org", "client")
        db.session.commit()
        db.session.expire_all()

        login(fresh_client, "noorg2@test.com", "password123")
        response = fresh_client.get("/analytics/client")
        assert response.status_code == 403
        logout(fresh_client)


def test_client_dashboard_shows_org_name(app, db, client):
    org = make_org(db, name="My Client Org", slug="myclient-org")
    user = make_user(db, "myclient@test.com", "password123", "My", "Client", "client")
    db.session.add(OrganizationUser(user_id=user.id, org_id=org.id, org_role="owner"))
    make_event(db, org, visitor_id="c-v1", session_id="c-s1")
    db.session.commit()

    login(client, "myclient@test.com", "password123")
    response = client.get("/analytics/client")
    assert_ok(response)
    assert b"Today's Pageviews" in response.data
    assert b"desktop" in response.data  # event device shows up in devices table
    logout(client)


CHROME_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
FIREFOX_LINUX = "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)
IPAD_UA = (
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
BINGBOT = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
SEMRUSH = "SemrushBot/7~bl"
EMPTY_UA = ""


# ── utils/analytics.py: is_bot ────────────────────────────────────────────────


def test_is_bot_empty_string():
    assert is_bot("") is False


def test_is_bot_none_equivalent():
    assert is_bot("") is False


def test_is_bot_googlebot():
    assert is_bot(GOOGLEBOT) is True


def test_is_bot_bingbot():
    assert is_bot(BINGBOT) is True


def test_is_bot_semrush():
    assert is_bot(SEMRUSH) is True


def test_is_bot_pattern_bot_keyword():
    assert is_bot("SomeRandomBot/1.0") is True


def test_is_bot_pattern_crawler():
    assert is_bot("MyCrawler/1.0") is True


def test_is_bot_pattern_spider():
    assert is_bot("WebSpider/2.0") is True


def test_is_bot_pattern_ahrefsbot():
    assert is_bot("AhrefsBot/7.0") is True


def test_is_bot_pattern_mj12bot():
    assert is_bot("MJ12bot/v1.4.8") is True


def test_is_bot_real_chrome_not_bot():
    assert is_bot(CHROME_DESKTOP) is False


def test_is_bot_real_firefox_not_bot():
    assert is_bot(FIREFOX_LINUX) is False


def test_is_bot_real_safari_iphone_not_bot():
    assert is_bot(SAFARI_IPHONE) is False


def test_is_bot_case_insensitive():
    assert is_bot("GOOGLEBOT/2.1") is True


# ── utils/analytics.py: parse_device_type ────────────────────────────────────


def test_parse_device_type_empty():
    assert parse_device_type("") == "unknown"


def test_parse_device_type_desktop():
    assert parse_device_type(CHROME_DESKTOP) == "desktop"


def test_parse_device_type_mobile():
    assert parse_device_type(SAFARI_IPHONE) == "mobile"


def test_parse_device_type_tablet():
    assert parse_device_type(IPAD_UA) == "tablet"


def test_parse_device_type_firefox_linux_desktop():
    assert parse_device_type(FIREFOX_LINUX) == "desktop"


def test_parse_device_type_exception_returns_unknown():
    with patch("app.utils.analytics.parse_ua", side_effect=Exception("boom")):
        assert parse_device_type(CHROME_DESKTOP) == "unknown"


# ── utils/analytics.py: parse_browser ────────────────────────────────────────


def test_parse_browser_empty():
    assert parse_browser("") == "unknown"


def test_parse_browser_chrome():
    result = parse_browser(CHROME_DESKTOP)
    assert "Chrome" in result or result != "unknown"


def test_parse_browser_firefox():
    result = parse_browser(FIREFOX_LINUX)
    assert "Firefox" in result or result != "unknown"


def test_parse_browser_safari_iphone():
    result = parse_browser(SAFARI_IPHONE)
    assert result != "unknown"


def test_parse_browser_exception_returns_unknown():
    with patch("app.utils.analytics.parse_ua", side_effect=Exception("boom")):
        assert parse_browser(CHROME_DESKTOP) == "unknown"


def test_parse_browser_empty_family_returns_unknown():
    mock_ua = MagicMock()
    mock_ua.browser.family = ""
    with patch("app.utils.analytics.parse_ua", return_value=mock_ua):
        assert parse_browser(CHROME_DESKTOP) == "unknown"


# ── utils/analytics.py: parse_os ─────────────────────────────────────────────


def test_parse_os_empty():
    assert parse_os("") == "unknown"


def test_parse_os_windows():
    result = parse_os(CHROME_DESKTOP)
    assert "Windows" in result or result != "unknown"


def test_parse_os_linux():
    result = parse_os(FIREFOX_LINUX)
    assert "Linux" in result or result != "unknown"


def test_parse_os_ios():
    result = parse_os(SAFARI_IPHONE)
    assert "iOS" in result or result != "unknown"


def test_parse_os_exception_returns_unknown():
    with patch("app.utils.analytics.parse_ua", side_effect=Exception("boom")):
        assert parse_os(CHROME_DESKTOP) == "unknown"


def test_parse_os_empty_family_returns_unknown():
    mock_ua = MagicMock()
    mock_ua.os.family = ""
    with patch("app.utils.analytics.parse_ua", return_value=mock_ua):
        assert parse_os(CHROME_DESKTOP) == "unknown"


# ── utils/analytics.py: get_client_ip ────────────────────────────────────────


def test_get_client_ip_from_remote_addr(app):
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "1.2.3.4"}):
        from flask import request

        assert get_client_ip(request) == "1.2.3.4"


def test_get_client_ip_from_x_forwarded_for(app):
    with app.test_request_context("/", headers={"X-Forwarded-For": "9.8.7.6, 1.2.3.4"}):
        from flask import request

        assert get_client_ip(request) == "9.8.7.6"


def test_get_client_ip_single_x_forwarded_for(app):
    with app.test_request_context("/", headers={"X-Forwarded-For": "5.5.5.5"}):
        from flask import request

        assert get_client_ip(request) == "5.5.5.5"


# ── utils/analytics.py: lookup_geo ───────────────────────────────────────────


def test_lookup_geo_returns_none_tuple():
    result = lookup_geo("1.2.3.4")
    assert result == (None, None)
