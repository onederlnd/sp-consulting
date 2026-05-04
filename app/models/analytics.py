import uuid
from app.extensions import db
from datetime import datetime, timezone


def generate_api_key():
    return str(uuid.uuid4()).replace("-", "")


class OrgDomain(db.Model):
    __tablename__ = "org_domains"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organization = db.relationship("Organization", backref="domains")

    __table_args__ = (db.UniqueConstraint("org_id", "domain", name="uq_org_domain"),)

    def __repr__(self):
        return f"<OrgDomain {self.domain}>"


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    session_id = db.Column(db.String(36), nullable=False, index=True)
    visitor_id = db.Column(db.String(36), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, default="pageview")
    url = db.Column(db.String(2048), nullable=True)
    referrer = db.Column(db.String(2048), nullable=True)
    title = db.Column(db.String(512), nullable=True)
    properties = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    country = db.Column(db.String(2), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    organization = db.relationship("Organization", backref="events")

    def __repr__(self):
        return f"<Event {self.event_type} org={self.org_id}>"


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    session_id = db.Column(db.String(36), nullable=False, unique=True, index=True)
    visitor_id = db.Column(db.String(36), nullable=False, index=True)
    started_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at = db.Column(db.DateTime, nullable=True)
    pageview_count = db.Column(db.Integer, default=1, nullable=False)
    entry_url = db.Column(db.String(2048), nullable=True)
    exit_url = db.Column(db.String(2048), nullable=True)
    referrer = db.Column(db.String(2048), nullable=True)
    utm_source = db.Column(db.String(255), nullable=True)
    utm_medium = db.Column(db.String(255), nullable=True)
    utm_campaign = db.Column(db.String(255), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(2), nullable=True)
    converted = db.Column(db.Boolean, default=False, nullable=False)

    organization = db.relationship("Organization", backref="sessions")

    def __repr__(self):
        return f"<Session {self.session_id}>"


class DailySummary(db.Model):
    __tablename__ = "daily_summaries"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    pageviews = db.Column(db.Integer, default=0, nullable=False)
    unique_visitors = db.Column(db.Integer, default=0, nullable=False)
    sessions = db.Column(db.Integer, default=0, nullable=False)
    bounce_rate = db.Column(db.Float, default=0.0, nullable=False)
    avg_session_duration = db.Column(db.Float, default=0.0, nullable=False)
    top_pages = db.Column(db.JSON, nullable=True)

    organization = db.relationship("Organization", backref="daily_summaries")

    __table_args__ = (db.UniqueConstraint("org_id", "date", name="uq_org_date"),)

    def __repr__(self):
        return f"<DailySummary org={self.org_id} date={self.date}>"
