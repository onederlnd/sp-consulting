from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from app.models.document import ALLOWED_EXTENSIONS


from wtforms.validators import Email


def make_create_organization_form():
    class CreateOrganizationForm(FlaskForm):
        org_name = StringField(
            "Organization Name",
            validators=[DataRequired(), Length(max=255)],
        )
        billing_email = StringField(
            "Billing Email",
            validators=[DataRequired(), Email(), Length(max=255)],
        )
        owner_first_name = StringField(
            "Contact First Name",
            validators=[DataRequired(), Length(max=100)],
        )
        owner_last_name = StringField(
            "Contact Last Name",
            validators=[DataRequired(), Length(max=100)],
        )
        owner_email = StringField(
            "Contact Email",
            validators=[DataRequired(), Email(), Length(max=255)],
        )
        submit = SubmitField("Create Organization & Send Invite →")

    return CreateOrganizationForm()


def make_upload_document_form():
    class UploadDocumentForm(FlaskForm):
        name = StringField(
            "Document Name",
            validators=[DataRequired(), Length(max=255)],
        )
        description = TextAreaField(
            "Description",
            validators=[Length(max=1000)],
        )
        file = FileField(
            "File",
            validators=[
                FileRequired(),
                FileAllowed(
                    list(ALLOWED_EXTENSIONS),
                    "File type not allowed.",
                ),
            ],
        )
        client_visible = BooleanField(
            "Visible to client",
            default=True,
        )
        submit = SubmitField("Upload Document →")

    return UploadDocumentForm()


def make_edit_document_form():
    class EditDocumentForm(FlaskForm):
        name = StringField(
            "Document Name",
            validators=[DataRequired(), Length(max=255)],
        )
        description = TextAreaField(
            "Description",
            validators=[Length(max=1000)],
        )
        client_visible = BooleanField("Visible to client")
        submit = SubmitField("Save Changes →")

    return EditDocumentForm()


def make_upload_version_form():
    class UploadVersionForm(FlaskForm):
        file = FileField(
            "New Version",
            validators=[
                FileRequired(),
                FileAllowed(
                    list(ALLOWED_EXTENSIONS),
                    "File type not allowed.",
                ),
            ],
        )
        submit = SubmitField("Upload New Version →")

    return UploadVersionForm()
