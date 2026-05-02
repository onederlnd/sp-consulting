from flask import render_template, redirect, url_for, flash, request
from app.routes.client import client_bp
from app.utils.decorators import client_required


@client_bp.route("/")
@client_required
def index():
    return render_template("client/dashboard.html")


@client_bp.route("/documents")
@client_required
def documents():
    return render_template("client/documents.html")


@client_bp.route("/messages")
@client_required
def messages():
    return render_template("client/messages.html")


@client_bp.route("/messages/send", methods=["POST"])
@client_required
def send_message():
    body = request.form.get("body", "").strip()
    if not body:
        flash("Message cannot be empty.", "danger")
        return redirect(url_for("client.messages"))

    # TODO: save message to DB once Message model exists
    flash("Message sent.", "success")
    return redirect(url_for("client.messages"))


@client_bp.route("/reports")
@client_required
def reports():
    return render_template("client/reports.html")
