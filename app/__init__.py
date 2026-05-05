import sys
from flask import Flask
from config import config_map
from flask_migrate import Migrate
from datetime import datetime, timezone
from app.extensions import db, login_manager, csrf, limiter, mail
from app.cli import register_commands
from app.errors import register_error_handlers

# Import models so Flask-Migrate can detect them
from app.models import user  # noqa: F401
from app.models import organization  # noqa: F401
from app.models import document  # noqa: F401
from app.models import analytics  # noqa: F401


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    # Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.client import client_bp
    from app.routes.staff import staff_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(client_bp, url_prefix="/client")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")

    register_commands(app)

    @app.context_processor
    def inject_now():
        return {"now": datetime.now(timezone.utc)}

    if "db" not in sys.argv:
        with app.app_context():
            _auto_init(app)

    register_error_handlers(app)

    return app


def _auto_init(app):
    """Seed if first run. Schema managed by Flask-Migrate."""
    from app.extensions import db
    from app.models.user import User
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    if not inspector.has_table("users"):
        return  # tables not created yet -- skipp seeding1
    org_columns = (
        {col["name"] for col in inspector.get_columns("organizations")}
        if inspector.has_table("organizations")
        else set()
    )
    if "analytics_key" not in org_columns:
        app.longer.info("Schema not fully migrated yet -- skipping auto-init.")
        return

    if User.query.first() is None:
        from app.cli import _seed_users

        _seed_users()
        app.logger.info("Database seeded with initial data.")
