from flask import Flask
from config import config_map
from flask_migrate import Migrate
from datetime import datetime, timezone
from app.extensions import db, login_manager, csrf, limiter, mail
from app.cli import register_commands


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

    # Import models so Flask-Migrate can detect them
    from app.models import user  # noqa: F401

    # Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.client import client_bp
    from app.routes.staff import staff_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(client_bp, url_prefix="/client")
    app.register_blueprint(staff_bp, url_prefix="/staff")

    register_commands(app)

    @app.context_processor
    def inject_now():
        return {"now": datetime.now(timezone.utc)}

    with app.app_context():
        _auto_init(app)

    return app


def _auto_init(app):
    """Create DB file, tables, and seed if first run."""
    import os
    from app.extensions import db
    from app.models.user import User

    # Create the database file and directory if needed
    db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            app.logger.info(f"Created database directory: {db_dir}")

    db.create_all()

    if User.query.first() is None:
        from app.cli import _seed_users
        _seed_users()
        app.logger.info("Database seeded with initial data.")
