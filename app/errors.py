from flask import render_template
from werkzeug.exceptions import HTTPException
from app import db  # adjust import to match your app factory


def register_error_handlers(app):
    """Register HTTP error handlers. Call this in your app factory."""

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()  # roll back any broken transactions
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return render_template(
                "errors/generic.html", code=e.code, description=e.description
            ), e.code
        db.session.rollback()
        return render_template("errors/500.html"), 500
