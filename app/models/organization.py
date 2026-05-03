from app.extensions import db
from datetime import timezone, datetime
import re


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def unique_slug(name):
    base = slugify(name)
    slug = base
    counter = 1
    while Organization.query.filter_by(slug=slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    billing_email = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    analytics_key = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    members = db.relationship(
        "OrganizationUser",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    assigned_staff = db.relationship(
        "User",
        secondary="org_staff",
        back_populates="assigned_orgs",
        lazy="joined",
    )
    # Add this column to the Organization model
    analytics_key = db.Column(
        db.String(32),
        unique=True,
        nullable=True,
        default=None,
    )

    @property
    def owner(self):
        membership = OrganizationUser.query.filter_by(
            org_id=self.id, org_role="owner"
        ).first()
        return membership.user if membership else None

    @property
    def member_count(self):
        return OrganizationUser.query.filter_by(org_id=self.id).count()

    def __repr__(self):
        return f"<Organization {self.slug}>"


class OrganizationUser(db.Model):
    __tablename__ = "organization_users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    org_role = db.Column(db.String(20), nullable=False, default="member")
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", back_populates="org_memberships")
    organization = db.relationship("Organization", back_populates="members")

    __table_args__ = (db.UniqueConstraint("user_id", "org_id", name="uq_org_user"),)

    def __repr__(self):
        return f"<OrganizationUser user={self.user_id} org={self.org_id}>"


# Staff ↔ Organization association table
org_staff = db.Table(
    "org_staff",
    db.Column("staff_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "org_id", db.Integer, db.ForeignKey("organizations.id"), primary_key=True
    ),
)
