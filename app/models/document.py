import os
from app.extensions import db
from datetime import datetime, timezone

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx",
    "doc",
    "txt",
    "md",
    "xlsx",
    "xls",
    "csv",
    "pptx",
    "ppt",
    "png",
    "jpg",
    "jpeg",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_path(org_slug, document_id, filename):
    from flask import current_app

    base = current_app.config.get("UPLOAD_PATH", "/data/uploads")
    return os.path.join(base, org_slug, str(document_id), filename)


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_type = db.Column(db.String(20), nullable=False)
    client_visible = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organization = db.relationship("Organization", backref="documents")
    uploaded_by = db.relationship("User", backref="uploaded_documents")
    versions = db.relationship(
        "DocumentVersion",
        back_populates="document",
        order_by="DocumentVersion.version_number.desc()",
        cascade="all, delete-orphan",
    )

    @property
    def latest_version(self):
        return self.versions[0] if self.versions else None

    @property
    def version_count(self):
        return len(self.versions)

    def __repr__(self):
        return f"<Document {self.name}>"


class DocumentVersion(db.Model):
    __tablename__ = "document_versions"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document = db.relationship("Document", back_populates="versions")
    uploaded_by = db.relationship("User", backref="document_versions")

    @property
    def file_size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def __repr__(self):
        return f"<DocumentVersion doc={self.document_id} v{self.version_number}>"
