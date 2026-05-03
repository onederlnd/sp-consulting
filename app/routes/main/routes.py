from flask import render_template, redirect, url_for, flash
from app.routes.main import main_bp
from app.forms.auth import make_contact_form


@main_bp.route("/")
def index():
    return render_template("main/index.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = make_contact_form()
    if form.validate_on_submit():
        # TODO: send email with contact form data
        flash("Your message has been sent. We'll be in touch shortly.", "success")
        return redirect(url_for("main.contact"))
    return render_template("main/contact.html", form=form)
