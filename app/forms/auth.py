from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length


def make_login_form():
    class LoginForm(FlaskForm):
        email = StringField("Email", validators=[DataRequired(), Email()])
        password = PasswordField("Password", validators=[DataRequired()])
        remember_me = BooleanField("Remember me")
        submit = SubmitField("Log In")

    return LoginForm()


def make_password_reset_request_form():
    class PasswordResetRequestForm(FlaskForm):
        email = StringField("Email", validators=[DataRequired(), Email()])
        submit = SubmitField("Send Reset Link")

    return PasswordResetRequestForm()


def make_password_reset_form():
    class PasswordResetForm(FlaskForm):
        password = PasswordField(
            "New Password", validators=[DataRequired(), Length(min=8)]
        )
        confirm = PasswordField(
            "Confirm Password",
            validators=[
                DataRequired(),
                EqualTo("password", message="Passwords must match"),
            ],
        )
        submit = SubmitField("Reset Password")

    return PasswordResetForm()


def make_create_user_form():
    class CreateUserForm(FlaskForm):
        first_name = StringField(
            "First Name", validators=[DataRequired(), Length(max=100)]
        )
        last_name = StringField(
            "Last Name", validators=[DataRequired(), Length(max=100)]
        )
        email = StringField("Email", validators=[DataRequired(), Email()])
        role = SelectField(
            "Role",
            choices=[("client", "Client"), ("staff", "Staff"), ("admin", "Admin")],
            validators=[DataRequired()],
        )
        password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
        confirm = PasswordField(
            "Confirm Password",
            validators=[
                DataRequired(),
                EqualTo("password", message="Passwords must match"),
            ],
        )
        submit = SubmitField("Create User")

    return CreateUserForm()


def make_contact_form():
    class ContactForm(FlaskForm):
        first_name = StringField(
            "First Name", validators=[DataRequired(), Length(max=100)]
        )
        last_name = StringField(
            "Last Name", validators=[DataRequired(), Length(max=100)]
        )
        email = StringField("Email", validators=[DataRequired(), Email()])
        organization = StringField("Organization", validators=[Length(max=255)])
        service = SelectField(
            "Service",
            choices=[
                ("", "Select a service..."),
                ("strategy", "Business Strategy"),
                ("technology", "Technology Advisory"),
                ("operations", "Operations & Systems"),
                ("executive", "Executive Advisory"),
                ("transformation", "Digital Transformation"),
                ("change", "Change Management"),
                ("other", "Other"),
            ],
        )
        message = TextAreaField("Message", validators=[DataRequired()])
        submit = SubmitField("Send Message →")

    return ContactForm()
