# Sunceray Patterson Consulting — Platform Roadmap

**Target:** v1.0 Production Launch  
**Stack:** Flask · SQLite → PostgreSQL · SQLAlchemy · Docker · Fly.io

---

## Phase 0 — Foundation ✅ Complete

- [x] GitHub repo initialized
- [x] Project structure scaffolded (`app/`, `routes/`, `templates/`, `static/`)
- [x] `config.py` with Dev / Staging / Production / Testing configs
- [x] `extensions.py` — db, login_manager, csrf, limiter, mail wired up
- [x] `.env.example` documented
- [x] `Makefile` commands (`run`, `test`, `lint`, `migrate`, `shell`, `install`, `seed`)
- [x] `requirements/` split — `base.txt`, `dev.txt`, `prod.txt`
- [x] `ship.sh` — lint, test, commit, push, open PR
- [x] `done.sh` — branch cleanup after merge
- [x] `scripts/feature.sh` — feature branch creation

---

## Phase 1 — Auth & User Management ✅ Complete

- [x] `User` model with role (`admin`, `staff`, `client`)
- [x] Flask-Migrate baseline migration
- [x] Login / logout routes
- [x] Password hashing with bcrypt
- [x] CSRF protection on all forms (Flask-WTF)
- [x] Login rate limiting (Flask-Limiter)
- [x] Role-based decorators: `@admin_required`, `@staff_required`, `@client_required`
- [x] Unauthenticated users redirected to login, wrong-role users get 403
- [x] Admin-only user creation (no self-registration)
- [x] Password reset flow (email token via Flask-Mail)
- [x] `base.html` with nav, flash messages, portal_base.html override
- [x] `next=` parameter preserved on redirect

---

## Phase 2 — Organization & Client Management ✅ Complete

- [x] `Organization` model — name, slug (auto-generated), billing email, plan, is_active
- [x] `OrganizationUser` model — user ↔ org with org_role (owner, member, viewer)
- [x] `org_staff` association — staff assigned at org level (replaces staff_clients)
- [x] One-step org creation — creates org + owner user + sends invite email
- [x] Admin org list, org detail view (members + assigned staff)
- [x] Up to 3 users per organization (enforced at app layer)
- [x] All client data scoped to org_id — portable by design
- [x] Staff sees assigned orgs only; admin sees all
- [x] Migration from `staff_clients` to `org_staff`

---

## Phase 3 — Staff Portal ✅ Complete

- [x] `staff` blueprint scaffolded
- [x] Staff dashboard
- [x] Organizations list and detail
- [x] Engagements (placeholder)
- [x] Documents (placeholder)
- [x] Settings (placeholder — pending design)
- [x] User management (admin only) — list, create
- [x] Sidebar extracted to `_sidebar.html` include
- [x] `portal_base.html` — suppresses public nav/footer

---

## Phase 4 — Client Portal ✅ Complete

- [x] `client` blueprint scaffolded
- [x] Dashboard scoped to authenticated client only
- [x] Documents page (placeholder — scoped to client org)
- [x] Messages page with compose form (placeholder backend)
- [x] Reports page (placeholder)
- [x] Sidebar extracted to `_sidebar.html` include
- [x] No cross-client data leakage

---

## Phase 5 — Public Marketing Site ✅ Complete

- [x] `main` blueprint with public routes
- [x] Homepage, About, Services, Contact pages
- [x] Static assets wired — CSS, JS
- [x] SEO basics (meta tags, page titles)
- [x] Contact form with email delivery

---

## Phase 6 — Test Suite ✅ Complete

- [x] `conftest.py` with fixtures, factories, auth helpers, assertion helpers
- [x] `test_auth.py` — login, logout, rate limiting, CSRF, password reset, route protection
- [x] `test_dashboards.py` — all portal routes, role access, empty states, validation
- [x] `test_dashboards_extended.py` — token flow, next param, cross-role access, session security
- [x] 66 tests passing
- [x] Coverage ~80%
- [x] `test_organizations.py` — org creation, invite flow, member limits
- [x] Coverage to 90%+

---

## Phase 7 — CI/CD & Infrastructure 🔲 Up Next

- [x] GitHub Actions `ci.yml` — lint (flake8), test (pytest), security (bandit + safety)
- [x] GitHub Actions `cd.yml` — deploy to Fly.io on merge to `staging` and `main`

vvvvv ON HOLD until ready to go live vvvvv
- [h] `FLY_API_TOKEN` secret set in GitHub Actions
- [h] Fly.io apps provisioned (staging + production)
- [h] Persistent volume mounted at `/data/app.db`
- [h] `fly.toml` configured (region, volume, health checks)
- [h] HTTPS enforced at Fly.io edge
- [h] Secrets managed via `fly secrets set`
- [h] Migrate from SQLite to PostgreSQL for production

---

## Phase 8 — Analytics Platform 🔲 Planned

- [ ] Analytics data model (events, sessions, pageviews scoped to org)
- [ ] Ingestion endpoint (pixel or API)
- [ ] Client-facing analytics dashboard
- [ ] Staff-facing analytics overview per org
- [ ] Data export (CSV) — client owns their data

---

## Phase 9 — Content & Integrations 🔲 Planned

- [ ] CMS content ingestion (pages, posts) scoped to org
- [ ] E-commerce data ingestion (orders, revenue)
- [ ] Social data ingestion
- [ ] Connected platforms UI (OAuth flows per integration)
- [ ] Unified data dashboard per org

---

## Phase 10 — Messaging & Documents 🔲 Planned

- [ ] `Message` model — threaded, two-way, client ↔ staff
- [ ] Email notifications on new message
- [ ] `Document` model — file storage, scoped to org
- [ ] Staff upload, client download
- [ ] Document versioning

---

## Phase 11 — Engagements & Reporting 🔲 Planned

- [ ] `Engagement` model — scoped to org, status, dates
- [ ] `Report` model — linked to engagement, published to client
- [ ] Staff reporting tools
- [ ] Client-facing report viewer

---

## Phase 12 — Settings & Administration 🔲 Planned

- [ ] Personal settings — name, email, password change
- [ ] System settings — firm config, editable at runtime (DB-backed)
- [ ] Role expansion — analytics, sales, viewer roles
- [ ] Basic audit log (user creation, role changes, login events)

---

## Phase 13 — v1.0 Launch 🔲 Planned

- [ ] Final security review (bandit clean, safety clean)
- [ ] Staging smoke test sign-off
- [ ] Merge `staging` → `main` → production deploy
- [ ] DNS pointed to Fly.io production app
- [ ] Post-launch monitoring

---

## Backlog / Post-v1

- Two-factor authentication
- API layer for mobile or third-party integrations
- Client-facing invoice or payment status view
- White-label portal per org (custom domain, branding)

---

*Last updated: May 2026*
