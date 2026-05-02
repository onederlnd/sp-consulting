from flask import Blueprint

client_bp = Blueprint("client", __name__)

from app.routes.client import routes  # noqa: F401, E402
