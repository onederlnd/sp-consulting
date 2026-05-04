import csv
import io
from datetime import datetime, timezone, timedelta
from flask import (
    request,
    jsonify,
    render_template,
    abort,
    make_response,
    current_app,
)
from flask_login import current_user
from sqlalchemy import func
from app.routes.analytics import analytics_bp
from app.extensions import db
from app.models.organization import Organization
from app.models.analytics import OrgDomain, Event, Session
from app.utils.analytics import (
    is_bot,
    parse_device_type,
    parse_browser,
    parse_os,
    get_client_ip,
)
from app.utils.decorators import staff_required, client_required


# ── Ingestion ─────────────────────────────────────────────────────────────────


@analytics_bp.route("/collect", methods=["POST", "OPTIONS"])
def collect():
    """Public ingestion endpoint. Accepts events from tracking script."""

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return _cors_response(jsonify({}), origin=request.headers.get("Origin"))

    origin = request.headers.get("Origin", "")
    domain = origin.replace("https://", "").replace("http://", "").split("/")[0]

    # Validate domain is registered
    org_domain = OrgDomain.query.filter_by(domain=domain).first()
    if not org_domain:
        return jsonify({"error": "Domain not registered"}), 403

    org = org_domain.organization

    # Parse payload
    data = request.get_json(silent=True) or {}

    user_agent = request.headers.get("User-Agent", "")

    # Filter bots
    if is_bot(user_agent):
        return jsonify({"status": "ignored"}), 200

    session_id = data.get("session_id", "")
    visitor_id = data.get("visitor_id", "")
    event_type = data.get("event_type", "pageview")
    url = data.get("url", "")
    referrer = data.get("referrer", "")
    title = data.get("title", "")
    properties = data.get("properties", {})

    if not session_id or not visitor_id:
        return jsonify({"error": "Missing session_id or visitor_id"}), 400

    ip = get_client_ip(request)
    device_type = parse_device_type(user_agent)
    browser = parse_browser(user_agent)
    os_name = parse_os(user_agent)

    # Parse UTM params from URL
    utm_source = data.get("utm_source")
    utm_medium = data.get("utm_medium")
    utm_campaign = data.get("utm_campaign")

    # Create event
    event = Event(
        org_id=org.id,
        session_id=session_id,
        visitor_id=visitor_id,
        event_type=event_type,
        url=url,
        referrer=referrer,
        title=title,
        properties=properties,
        ip_address=ip,
        user_agent=user_agent,
        device_type=device_type,
        browser=browser,
        os=os_name,
    )
    db.session.add(event)

    # Upsert session
    session = Session.query.filter_by(session_id=session_id).first()
    if not session:
        session = Session(
            org_id=org.id,
            session_id=session_id,
            visitor_id=visitor_id,
            entry_url=url,
            referrer=referrer,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            device_type=device_type,
            pageview_count=1,
        )
        db.session.add(session)
    else:
        session.pageview_count += 1
        session.exit_url = url
        session.ended_at = datetime.now(timezone.utc)

    db.session.commit()

    response = jsonify({"status": "ok"})
    return _cors_response(response, origin=origin)


def _cors_response(response, origin=""):
    response.headers["Access-Control-Allow-Origin"] = origin or "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ── Staff analytics overview ──────────────────────────────────────────────────


@analytics_bp.route("/")
@staff_required
def overview():
    if current_user.role == "admin":
        orgs = Organization.query.filter_by(is_active=True).all()
    else:
        orgs = current_user.assigned_orgs

    # Last 30 days summary per org
    since = datetime.now(timezone.utc) - timedelta(days=30)
    org_stats = []
    for org in orgs:
        pageviews = (
            db.session.query(func.count(Event.id))
            .filter(
                Event.org_id == org.id,
                Event.event_type == "pageview",
                Event.created_at >= since,
            )
            .scalar()
            or 0
        )

        visitors = (
            db.session.query(func.count(func.distinct(Event.visitor_id)))
            .filter(
                Event.org_id == org.id,
                Event.created_at >= since,
            )
            .scalar()
            or 0
        )

        org_stats.append(
            {
                "org": org,
                "pageviews": pageviews,
                "visitors": visitors,
            }
        )

    return render_template(
        "analytics/staff_overview.html",
        org_stats=org_stats,
    )


# ── Staff org detail ──────────────────────────────────────────────────────────


@analytics_bp.route("/<org_slug>")
@staff_required
def org_detail(org_slug):
    org = Organization.query.filter_by(slug=org_slug).first_or_404()

    since = datetime.now(timezone.utc) - timedelta(days=30)

    # Today's stats
    today = datetime.now(timezone.utc).date()
    today_pageviews = (
        db.session.query(func.count(Event.id))
        .filter(
            Event.org_id == org.id,
            Event.event_type == "pageview",
            func.date(Event.created_at) == today,
        )
        .scalar()
        or 0
    )

    today_visitors = (
        db.session.query(func.count(func.distinct(Event.visitor_id)))
        .filter(
            Event.org_id == org.id,
            func.date(Event.created_at) == today,
        )
        .scalar()
        or 0
    )

    # 30-day trend
    trend = (
        db.session.query(
            func.date(Event.created_at).label("date"),
            func.count(Event.id).label("pageviews"),
            func.count(func.distinct(Event.visitor_id)).label("visitors"),
        )
        .filter(
            Event.org_id == org.id,
            Event.created_at >= since,
        )
        .group_by(func.date(Event.created_at))
        .order_by(func.date(Event.created_at))
        .all()
    )

    # Top pages
    top_pages = (
        db.session.query(
            Event.url,
            Event.title,
            func.count(Event.id).label("views"),
        )
        .filter(
            Event.org_id == org.id,
            Event.event_type == "pageview",
            Event.created_at >= since,
        )
        .group_by(Event.url, Event.title)
        .order_by(func.count(Event.id).desc())
        .limit(10)
        .all()
    )

    # Referrers
    referrers = (
        db.session.query(
            Event.referrer,
            func.count(Event.id).label("count"),
        )
        .filter(
            Event.org_id == org.id,
            Event.referrer != "",
            Event.referrer.isnot(None),
            Event.created_at >= since,
        )
        .group_by(Event.referrer)
        .order_by(func.count(Event.id).desc())
        .limit(10)
        .all()
    )

    # Device breakdown
    devices = (
        db.session.query(
            Event.device_type,
            func.count(Event.id).label("count"),
        )
        .filter(
            Event.org_id == org.id,
            Event.created_at >= since,
        )
        .group_by(Event.device_type)
        .all()
    )

    # Registered domains
    domains = OrgDomain.query.filter_by(org_id=org.id).all()

    return render_template(
        "analytics/org_detail.html",
        org=org,
        today_pageviews=today_pageviews,
        today_visitors=today_visitors,
        trend=trend,
        top_pages=top_pages,
        referrers=referrers,
        devices=devices,
        domains=domains,
    )


# ── Domain management ─────────────────────────────────────────────────────────


@analytics_bp.route("/<org_slug>/domains/add", methods=["POST"])
@staff_required
def add_domain(org_slug):
    org = Organization.query.filter_by(slug=org_slug).first_or_404()
    domain = request.form.get("domain", "").strip().lower()

    if not domain:
        from flask import flash

        flash("Domain cannot be empty.", "danger")
        return _redirect_to_detail(org_slug)

    # Strip protocol if pasted with it
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]

    existing = OrgDomain.query.filter_by(org_id=org.id, domain=domain).first()
    if existing:
        from flask import flash

        flash("Domain already registered.", "danger")
        return _redirect_to_detail(org_slug)

    db.session.add(OrgDomain(org_id=org.id, domain=domain))
    db.session.commit()

    from flask import flash

    flash(f"{domain} added.", "success")
    return _redirect_to_detail(org_slug)


@analytics_bp.route("/<org_slug>/domains/<int:domain_id>/delete", methods=["POST"])
@staff_required
def delete_domain(org_slug, domain_id):
    domain = OrgDomain.query.get_or_404(domain_id)
    db.session.delete(domain)
    db.session.commit()
    from flask import flash

    flash("Domain removed.", "success")
    return _redirect_to_detail(org_slug)


def _redirect_to_detail(org_slug):
    from flask import redirect, url_for

    return redirect(url_for("analytics.org_detail", org_slug=org_slug))


# ── Client analytics ──────────────────────────────────────────────────────────


@analytics_bp.route("/client")
@client_required
def client_dashboard():
    org = current_user.organization
    if not org:
        abort(403)

    since = datetime.now(timezone.utc) - timedelta(days=30)
    today = datetime.now(timezone.utc).date()

    today_pageviews = (
        db.session.query(func.count(Event.id))
        .filter(
            Event.org_id == org.id,
            Event.event_type == "pageview",
            func.date(Event.created_at) == today,
        )
        .scalar()
        or 0
    )

    today_visitors = (
        db.session.query(func.count(func.distinct(Event.visitor_id)))
        .filter(
            Event.org_id == org.id,
            func.date(Event.created_at) == today,
        )
        .scalar()
        or 0
    )

    month_pageviews = (
        db.session.query(func.count(Event.id))
        .filter(
            Event.org_id == org.id,
            Event.event_type == "pageview",
            Event.created_at >= since,
        )
        .scalar()
        or 0
    )

    month_visitors = (
        db.session.query(func.count(func.distinct(Event.visitor_id)))
        .filter(
            Event.org_id == org.id,
            Event.created_at >= since,
        )
        .scalar()
        or 0
    )

    trend = (
        db.session.query(
            func.date(Event.created_at).label("date"),
            func.count(Event.id).label("pageviews"),
            func.count(func.distinct(Event.visitor_id)).label("visitors"),
        )
        .filter(
            Event.org_id == org.id,
            Event.created_at >= since,
        )
        .group_by(func.date(Event.created_at))
        .order_by(func.date(Event.created_at))
        .all()
    )

    top_pages = (
        db.session.query(
            Event.url,
            Event.title,
            func.count(Event.id).label("views"),
        )
        .filter(
            Event.org_id == org.id,
            Event.event_type == "pageview",
            Event.created_at >= since,
        )
        .group_by(Event.url, Event.title)
        .order_by(func.count(Event.id).desc())
        .limit(10)
        .all()
    )

    referrers = (
        db.session.query(
            Event.referrer,
            func.count(Event.id).label("count"),
        )
        .filter(
            Event.org_id == org.id,
            Event.referrer != "",
            Event.referrer.isnot(None),
            Event.created_at >= since,
        )
        .group_by(Event.referrer)
        .order_by(func.count(Event.id).desc())
        .limit(10)
        .all()
    )

    devices = (
        db.session.query(
            Event.device_type,
            func.count(Event.id).label("count"),
        )
        .filter(
            Event.org_id == org.id,
            Event.created_at >= since,
        )
        .group_by(Event.device_type)
        .all()
    )

    return render_template(
        "client/analytics.html",
        org=org,
        today_pageviews=today_pageviews,
        today_visitors=today_visitors,
        month_pageviews=month_pageviews,
        month_visitors=month_visitors,
        trend=trend,
        top_pages=top_pages,
        referrers=referrers,
        devices=devices,
    )


# ── CSV Export ────────────────────────────────────────────────────────────────


@analytics_bp.route("/export/<org_slug>")
@staff_required
def export_csv(org_slug):
    org = Organization.query.filter_by(slug=org_slug).first_or_404()

    since = datetime.now(timezone.utc) - timedelta(
        days=current_app.config.get("ANALYTICS_RETENTION_DAYS", 90)
    )

    events = (
        Event.query.filter(
            Event.org_id == org.id,
            Event.created_at >= since,
        )
        .order_by(Event.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "timestamp",
            "event_type",
            "url",
            "title",
            "referrer",
            "visitor_id",
            "session_id",
            "device_type",
            "browser",
            "os",
            "country",
            "city",
        ]
    )

    for event in events:
        writer.writerow(
            [
                event.created_at.isoformat(),
                event.event_type,
                event.url,
                event.title,
                event.referrer,
                event.visitor_id,
                event.session_id,
                event.device_type,
                event.browser,
                event.os,
                event.country or "",
                event.city or "",
            ]
        )

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = (
        f"attachment; filename={org.slug}-analytics.csv"
    )
    return response
