
# GitHub Branch Protection Setup

After pushing this repo to GitHub, apply these branch protection rules manually.
GitHub does not support configuring branch protection via files in the repository —
it must be done through the UI or GitHub CLI.

---

## Option A — GitHub UI

Go to: **Settings → Branches → Add branch ruleset**

### For `main`

| Setting | Value |
|---|---|
| Branch name pattern | `main` |
| Restrict pushes | ✅ Enabled |
| Require pull request before merging | ✅ Enabled |
| Required approvals | `1` |
| Dismiss stale reviews on new commits | ✅ Enabled |
| Require status checks to pass | ✅ Enabled |
| Required status checks | `Lint`, `Test`, `Security Scan` |
| Require branches to be up to date | ✅ Enabled |
| Do not allow bypassing settings | ✅ Enabled |

### For `staging`

Same as `main` except required approvals can be set to `0` if you want
to allow solo deploys to staging without a review.

### For `develop`

No protection needed — leave it open for flexibility.

---

## Option B — GitHub CLI

Install the CLI: https://cli.github.com

```bash
# Protect main
gh api \
  --method PUT \
  repos/{owner}/sunceray-consulting/branches/main/protection \
  --field required_status_checks='{"strict":true,"contexts":["Lint","Test","Security Scan"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null

# Protect staging
gh api \
  --method PUT \
  repos/{owner}/sunceray-consulting/branches/staging/protection \
  --field required_status_checks='{"strict":true,"contexts":["Lint","Test","Security Scan"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":0}' \
  --field restrictions=null
```

Replace `{owner}` with your GitHub username or organization name.

---

## Required GitHub Secrets

Go to: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|---|---|
| `FLY_API_TOKEN` | Get this by running `fly auth token` after logging into Fly.io |

---

## GitHub Environments

Go to: **Settings → Environments**

Create two environments:

1. **staging** — no required reviewers
2. **production** — add yourself as a required reviewer for an extra manual gate before prod deploys

---

## After Setup

Your pipeline is live. Every push will:
- Trigger CI automatically
- Block merges to `main` and `staging` if CI fails
- Auto-deploy on merge via the CD workflow