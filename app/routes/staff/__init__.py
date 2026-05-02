from flask import Blueprint

staff_bp = Blueprint("staff", __name__)

from app.routes.staff import routes  # noqa: F401, E402
