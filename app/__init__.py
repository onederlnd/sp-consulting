from flask import Flask
from config import config_map
from app.extensions import db, login_manager, csrf, limiter
from flask_migrate import Migrate
from datetime import datetime, timezone


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
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

    @app.context_processor
    def inject_now():
        return {"now": datetime.now(timezone.utc)}

    return app
