import os
from flask import render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import current_user
from app.routes.client import client_bp
from app.utils.decorators import client_required
from app.models.document import Document, get_upload_path


@client_bp.route("/")
@client_required
def index():
    return render_template("client/dashboard.html")


@client_bp.route("/documents")
@client_required
def documents():
    org = current_user.organization
    if org:
        docs = (
            Document.query.filter_by(
                org_id=org.id,
                is_active=True,
                client_visible=True,
            )
            .order_by(Document.created_at.desc())
            .all()
        )
    else:
        docs = []
    return render_template("client/documents.html", documents=docs)


@client_bp.route("/documents/<int:doc_id>/download")
@client_required
def download_document(doc_id):
    org = current_user.organization
    if not org:
        abort(403)
    doc = Document.query.filter_by(
        id=doc_id,
        org_id=org.id,
        is_active=True,
        client_visible=True,
    ).first_or_404()
    version = doc.latest_version
    if not version:
        abort(404)
    path = get_upload_path(org.slug, doc.id, version.filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(
        path,
        as_attachment=True,
        download_name=version.original_filename,
    )


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
    flash("Message sent.", "success")
    return redirect(url_for("client.messages"))


@client_bp.route("/reports")
@client_required
def reports():
    return render_template("client/reports.html")
