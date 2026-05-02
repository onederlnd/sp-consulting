from flask import render_template
from flask_login import login_required
from app.routes.client import client_bp
from app.utils.decorators import client_required


@client_bp.route("/")
@login_required
@client_required
def index():
    return render_template("client/dashboard.html")
