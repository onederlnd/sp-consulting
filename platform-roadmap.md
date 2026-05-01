# Sunceray Patterson Consulting — Platform Roadmap

**Target:** v1.0 Production Launch  
**Stack:** Flask · SQLite · SQLAlchemy · Docker · Fly.io

---

## Phase 0 — Foundation ✅ In Progress

- [x] GitHub repo initialized
- [ ] Project structure scaffolded (`app/`, `blueprints/`, `templates/`, `static/`)
- [ ] `config.py` with Dev / Staging / Production configs
- [ ] `extensions.py` — db, login_manager, csrf, limiter wired up
- [ ] Docker + `docker-compose.yml` for local dev
- [ ] `.env.example` documented
- [ ] `Makefile` commands (`run`, `test`, `lint`, `migrate`, `shell`, `install`)
- [ ] `requirements/` split — `base.txt`, `dev.txt`, `prod.txt`

---

## Phase 1 — Auth & User Management

- [ ] `User` model with role enum (`admin`, `staff`, `client`)
- [ ] Flask-Migrate baseline migration
- [ ] Login / logout routes (`auth` blueprint)
- [ ] Password hashing with bcrypt
- [ ] CSRF protection on all forms (Flask-WTF)
- [ ] Login rate limiting (Flask-Limiter)
- [ ] Role-based decorators: `@admin_required`, `@staff_required`, `@client_required`
- [ ] Admin-only user creation (no self-registration)
- [ ] Password reset flow (email token)
- [ ] `base.html` template with nav and flash messages

---

## Phase 2 — Admin Area

- [ ] Admin dashboard (user list, role management)
- [ ] Create / edit / deactivate user accounts
- [ ] Assign staff to client records
- [ ] Basic audit log (user creation, role changes)

---

## Phase 3 — Public Marketing Site

- [ ] `main` blueprint with public routes
- [ ] Homepage, About, Services, Contact pages
- [ ] Contact form with email delivery (SMTP / `MAIL_*` config)
- [ ] Static assets wired — CSS, JS, images
- [ ] SEO basics (meta tags, page titles)

---

## Phase 4 — Client Portal

- [ ] `client` blueprint scaffolded
- [ ] Dashboard scoped to authenticated client only
- [ ] View assigned documents / deliverables
- [ ] Messaging or notes thread (client ↔ staff)
- [ ] Data access gated — no cross-client leakage

---

## Phase 5 — Staff Area

- [ ] `staff` blueprint scaffolded
- [ ] Staff dashboard — assigned client list
- [ ] View and update client records
- [ ] Upload / manage client deliverables
- [ ] Internal notes (not visible to clients)

---

## Phase 6 — CI/CD & Infrastructure

- [ ] GitHub Actions `ci.yml` — lint (flake8), test (pytest), security (bandit + safety)
- [ ] GitHub Actions `cd.yml` — deploy to Fly.io on merge to `staging` and `main`
- [ ] `FLY_API_TOKEN` secret set in GitHub Actions
- [ ] Fly.io apps provisioned (staging + production)
- [ ] Persistent SQLite volume mounted at `/data/app.db`
- [ ] `fly.toml` configured (region, volume, health checks)
- [ ] HTTPS enforced at Fly.io edge
- [ ] Secrets managed via `fly secrets set` (never in version control)

---

## Phase 7 — Testing & Hardening

- [ ] `conftest.py` with test client and fixtures
- [ ] `test_auth.py` — login, logout, rate limit, CSRF
- [ ] `test_client.py` — portal access, data scoping
- [ ] `test_staff.py` — staff access, client record updates
- [ ] Coverage report in CI
- [ ] Manual QA pass on staging

---

## Phase 8 — v1.0 Launch

- [ ] Final security review (bandit clean, safety clean)
- [ ] Staging smoke test sign-off
- [ ] Merge `staging` → `main` → production deploy
- [ ] DNS pointed to Fly.io production app
- [ ] Post-launch monitoring (Fly logs, error alerts)

---

## Backlog / Post-v1

- Email notifications (new message, document upload)
- Client-facing invoice or payment status view
- Staff reporting / activity summary
- Admin analytics dashboard
- Two-factor authentication
- API layer for future mobile or third-party integrations

---

*Last updated: May 2026*