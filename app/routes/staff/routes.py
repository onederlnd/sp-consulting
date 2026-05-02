from flask import render_template
from app.routes.staff import staff_bp
from app.utils.decorators import staff_required


@staff_bp.route("/")
@staff_required
def index():
    return render_template("staff/dashboard.html")


@staff_bp.route("/clients")
@staff_required
def clients():
    return render_template("staff/clients.html")


@staff_bp.route("/engagements")
@staff_required
def engagements():
    return render_template("staff/enagement.html")


@staff_bp.route("/documents")
@staff_required
def documents():
    return render_template("staff/documents.html")
