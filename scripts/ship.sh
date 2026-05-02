#!/usr/bin/env bash
# ship.sh — lint, test, commit any fixes, push branch, and open a PR
# Usage: ./scripts/ship.sh [pr-title]

set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE_BRANCH="main"

# ── Guard: don't ship directly from protected branches ───────────────────────
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "staging" ]; then
  echo "❌  You're on '$BRANCH'. Create a feature branch first."
  echo "    Run: ./scripts/feature.sh"
  exit 1
fi

# ── Auto-fix trailing newlines before linting ────────────────────────────────
echo "🔧  Fixing trailing newlines..."
while IFS= read -r file; do
  if [ -n "$(tail -c1 "$file")" ]; then
    echo "" >> "$file"
    echo "    fixed: $file"
  fi
done < <(git diff --name-only HEAD; git ls-files --others --exclude-standard)

# ── Lint ─────────────────────────────────────────────────────────────────────
echo "🔍  Running linter..."
make lint

# ── Tests ────────────────────────────────────────────────────────────────────
echo "🧪  Running tests..."
make test

# ── Stage any auto-fixes ─────────────────────────────────────────────────────
if ! git diff --quiet; then
  echo "📎  Staging auto-fixes..."
  git add -u
  git commit -m "chore: auto-fix linting issues"
fi

# ── Push branch ──────────────────────────────────────────────────────────────
echo "⬆️   Pushing branch '$BRANCH'..."
git push -u origin "$BRANCH"

# ── Open PR ──────────────────────────────────────────────────────────────────
if command -v gh &> /dev/null; then
  if [ -n "$1" ]; then
    PR_TITLE="$1"
  else
    read -rp "PR title: " PR_TITLE
  fi

  if [ -z "$PR_TITLE" ]; then
    PR_TITLE="$BRANCH"
  fi

  gh pr create --base "$BASE_BRANCH" --title "$PR_TITLE" --fill
  echo "✅  PR opened against $BASE_BRANCH."
else
  echo "⚠️  GitHub CLI not found. Install it to auto-open PRs:"
  echo "    https://cli.github.com"
  echo ""
  echo "✅  Branch pushed. Open a PR manually:"
  echo "    https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//' | sed 's/\.git$//')/compare/$BRANCH"
fi
