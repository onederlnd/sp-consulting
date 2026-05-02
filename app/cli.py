import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import User, set_password


def _seed_users():
    """Reusable seed function — called by CLI and auto-init."""
    users = [
        {
            "email": "admin@sunceraypatterson.com",
            "password": "changeme123!",
            "first_name": "Sunceray",
            "last_name": "Patterson",
            "role": "admin",
            "is_active": True,
        },
        {
            "email": "rchristenhusz@gmail.com",
            "password": "password123",
            "first_name": "Randy",
            "last_name": "Christenhusz",
            "role": "admin",
            "is_active": True,
        },
        {
            "email": "staff@sunceraypatterson.com",
            "password": "changeme123!",
            "first_name": "Staff",
            "last_name": "User",
            "role": "staff",
            "is_active": True,
        },
        {
            "email": "staff2@sunceraypatterson.com",
            "password": "changeme123!",
            "first_name": "Staff",
            "last_name": "Two",
            "role": "staff",
            "is_active": True,
        },
        {
            "email": "client1@example.com",
            "password": "changeme123!",
            "first_name": "Alice",
            "last_name": "Johnson",
            "role": "client",
            "is_active": True,
        },
        {
            "email": "client2@example.com",
            "password": "changeme123!",
            "first_name": "Marcus",
            "last_name": "Webb",
            "role": "client",
            "is_active": True,
        },
        {
            "email": "client3@example.com",
            "password": "changeme123!",
            "first_name": "Diana",
            "last_name": "Chen",
            "role": "client",
            "is_active": False,
        },
    ]

    created = {}

    for data in users:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing:
            created[data["email"]] = existing
            continue

        user = User(
            email=data["email"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role=data["role"],
            is_active=data["is_active"],
        )
        set_password(user, data["password"])
        db.session.add(user)
        db.session.flush()
        created[data["email"]] = user
    # fmt: off
    assignments = [
        (
            "staff@sunceraypatterson.com",
            ["client1@example.com", "client2@example.com"]
        ),
        (
            "staff2@sunceraypatterson.com",
            ["client2@example.com", "client3@example.com"]
        ),
    ]
    # fmt: on
    for staff_email, client_emails in assignments:
        staff = created.get(staff_email)
        if not staff:
            continue
        for client_email in client_emails:
            client = created.get(client_email)
            if not client:
                continue
            if client not in staff.assigned_clients:
                staff.assigned_clients.append(client)

    db.session.commit()


def register_commands(app):
    app.cli.add_command(seed_db)
    app.cli.add_command(create_user)


@click.command("seed")
@with_appcontext
def seed_db():
    """Seed the database with initial users."""
    _seed_users()
    click.echo("✓ Seed complete.")


@click.command("create-user")
@click.option("--email", prompt=True)
@click.option("--first-name", prompt=True)
@click.option("--last-name", prompt=True)
@click.option("--role", prompt=True, type=click.Choice(["admin", "staff", "client"]))
@click.password_option()
@with_appcontext
def create_user(email, first_name, last_name, role, password):
    """Interactively create a single user from the command line."""
    existing = User.query.filter_by(email=email.lower()).first()
    if existing:
        click.echo(f"Error: {email} already exists.")
        return

    user = User(
        email=email.lower(),
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True,
    )
    set_password(user, password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"✓ Created {role}: {email}")
