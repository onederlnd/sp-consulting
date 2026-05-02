import bcrypt
from app.extensions import db, login_manager
from flask_login import UserMixin

staff_clients = db.Table(
    'staff_clients',
    db.Column('staff_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('client_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
)


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

    # Staff → their assigned clients
    assigned_clients = db.relationship(
        'User',
        secondary=staff_clients,
        primaryjoin=id == staff_clients.c.staff_id,
        secondaryjoin=id == staff_clients.c.client_id,
        backref='assigned_staff',
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


def set_password(user, password):
    user.password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


def check_password(user, password):
    return bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
