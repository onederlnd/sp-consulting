from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, Length


def make_create_organization_form():
    class CreateOrganizationForm(FlaskForm):
        org_name = StringField(
            "Organization Name",
            validators=[DataRequired(), Length(max=255)],
        )
        billing_email = EmailField(
            "Billing Email",
            validators=[DataRequired(), Email()],
        )
        owner_first_name = StringField(
            "Contact First Name",
            validators=[DataRequired(), Length(max=100)],
        )
        owner_last_name = StringField(
            "Contact Last Name",
            validators=[DataRequired(), Length(max=100)],
        )
        owner_email = EmailField(
            "Contact Email",
            validators=[DataRequired(), Email()],
        )
        submit = SubmitField("Create Organization & Send Invite →")

    return CreateOrganizationForm()
