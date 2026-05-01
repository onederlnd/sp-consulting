# Sunceray Patterson Consulting — Platform

Internal web platform for Sunceray Patterson Consulting. Built with Flask, Jinja2, SQLite, and Python. Includes a public-facing website, admin-managed authentication, a client portal, and a staff area.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 / Flask |
| Templating | Jinja2 |
| Database | SQLite + SQLAlchemy + Flask-Migrate |
| Auth | Flask-Login, bcrypt, Flask-WTF (CSRF) |
| Rate Limiting | Flask-Limiter |
| Server | Gunicorn |
| Hosting | Fly.io |
| CI/CD | GitHub Actions |
| Containerization | Docker |

---

## Project Structure

```
sunceray-consulting/
├── app/
│   ├── __init__.py              # App factory (create_app)
│   ├── extensions.py            # db, login_manager, csrf, limiter
│   ├── models/
│   │   └── user.py              # User model with role enum (admin, staff, client)
│   ├── blueprints/
│   │   ├── main/                # Public marketing site
│   │   ├── auth/                # Login, logout, password reset
│   │   ├── client/              # Client portal
│   │   └── staff/               # Staff area
│   ├── templates/
│   │   ├── base.html
│   │   ├── main/
│   │   ├── auth/
│   │   ├── client/
│   │   └── staff/
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
├── migrations/                  # Flask-Migrate / Alembic
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_client.py
│   └── test_staff.py
├── .github/
│   └── workflows/
│       ├── ci.yml               # Lint, test, security scan
│       └── cd.yml               # Deploy to Fly.io
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── docker-compose.yml           # Local development
├── Dockerfile                   # Production image
├── fly.toml                     # Fly.io configuration
├── Makefile                     # Dev shortcuts
├── config.py                    # Dev / Staging / Production configs
├── wsgi.py                      # Gunicorn entrypoint
└── .env.example                 # Required environment variables
```

---

## Roles & Access Control

All accounts are created manually by an administrator — there is no self-registration.

| Role | Access |
|---|---|
| `admin` | Full access to all areas including user management |
| `staff` | Staff portal, assigned client records |
| `client` | Client portal scoped to their own data only |

Route protection is enforced via decorators: `@admin_required`, `@staff_required`, `@client_required`.

---

## Environments

| Environment | Branch | Config Class | Notes |
|---|---|---|---|
| Local dev | any | `DevelopmentConfig` | SQLite file, `.env` secrets |
| Staging | `staging` | `StagingConfig` | Fly.io staging app, Fly secrets |
| Production | `main` | `ProductionConfig` | Fly.io production app, Fly secrets |

---

## Getting Started

### Prerequisites

- Python 3.12+
- [Docker](https://www.docker.com/) (for local dev parity)
- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) (for deployment)

### Local Setup

```bash
# Clone the repo
git clone https://github.com/your-org/sunceray-consulting.git
cd sunceray-consulting

# Copy and fill in environment variables
cp .env.example .env

# Install dependencies
make install

# Run database migrations
make migrate

# Start the dev server
make run
```

The app will be available at `http://localhost:5000`.

### Using Docker

```bash
docker-compose up --build
```

---

## Makefile Commands

| Command | Description |
|---|---|
| `make run` | Start the Flask development server |
| `make test` | Run the pytest test suite |
| `make lint` | Run flake8 linter |
| `make security` | Run bandit + safety checks |
| `make migrate` | Apply pending database migrations |
| `make shell` | Open a Flask shell with app context |
| `make install` | Install all dev dependencies |

---

## CI/CD — GitHub Actions

### CI (`ci.yml`)
Runs on every push and pull request to any branch.

- **Lint** — `flake8` checks code style
- **Test** — `pytest` with coverage reporting
- **Security** — `bandit` scans for common vulnerabilities
- **Dependencies** — `safety` checks for known CVEs in packages

### CD (`cd.yml`)
- Merging to `staging` → deploys to the Fly.io staging app
- Merging to `main` → deploys to the Fly.io production app

Both require `FLY_API_TOKEN` to be set as a GitHub Actions secret.

---

## Deployment — Fly.io

```bash
# Authenticate
fly auth login

# Deploy manually (CI/CD handles this automatically)
fly deploy

# Set a secret
fly secrets set SECRET_KEY=your-secret-key

# View logs
fly logs

# Open a remote shell
fly ssh console
```

The SQLite database is stored on a persistent Fly volume mounted at `/data/app.db`. Volume size and region are configured in `fly.toml`.

---

## Security

- All secrets managed via environment variables — never committed to version control
- CSRF protection on all forms via Flask-WTF
- Passwords hashed with bcrypt
- Login rate-limited via Flask-Limiter
- `bandit` and `safety` run on every CI build
- HTTPS enforced at the Fly.io edge

---

## Environment Variables

See `.env.example` for a full list. Key variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret — must be long and random |
| `FLASK_ENV` | `development`, `staging`, or `production` |
| `DATABASE_URL` | SQLite path or connection string |
| `MAIL_*` | SMTP settings for transactional email |

---

## Contributing

1. Branch from `main` — use the naming convention `feature/`, `fix/`, or `chore/`
2. Open a pull request against `staging` for review
3. CI must pass before merge
4. Merges to `main` are restricted to admins

---

## License

Proprietary — all rights reserved. © Sunceray Patterson Consulting.