import bcrypt
from app.extensions import db, login_manager
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Org memberships (client side)
    org_memberships = db.relationship(
        "OrganizationUser",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Orgs assigned to this staff member
    assigned_orgs = db.relationship(
        "Organization",
        secondary="org_staff",
        back_populates="assigned_staff",
        lazy="joined",
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def organization(self):
        """Primary organization for client users."""
        membership = next(
            (m for m in self.org_memberships if m.org_role == "owner"),
            self.org_memberships[0] if self.org_memberships else None,
        )
        return membership.organization if membership else None


def set_password(user, password):
    user.password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def check_password(user, password):
    return bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
