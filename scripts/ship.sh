#!/usr/bin/env bash
# ship.sh — lint, test, push branch, and open a PR
# Usage: ./scripts/ship.sh [pr-title]
# If no PR title is provided, you will be prompted.

set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)

# ── Guard: don't ship directly from main ─────────────────────────────────────
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "staging" ]; then
  echo "❌  You're on '$BRANCH'. Create a feature branch first."
  echo "    Run: ./scripts/feature.sh"
  exit 1
fi

# ── Lint ─────────────────────────────────────────────────────────────────────
echo "🔍  Running linter..."
make lint

# ── Tests ────────────────────────────────────────────────────────────────────
echo "🧪  Running tests..."
make test

# ── Push branch ──────────────────────────────────────────────────────────────
echo "⬆️  Pushing branch '$BRANCH'..."
git push -u origin "$BRANCH"

# ── Open PR (requires GitHub CLI) ────────────────────────────────────────────
if command -v gh &> /dev/null; then
  if [ -n "$1" ]; then
    PR_TITLE="$1"
  else
    read -rp "PR title: " PR_TITLE
  fi

  if [ -z "$PR_TITLE" ]; then
    PR_TITLE="$BRANCH"
  fi

  gh pr create --base staging --title "$PR_TITLE" --fill
  echo "✅  PR opened against staging."
else
  echo "⚠️  GitHub CLI not found. Install it to auto-open PRs:"
  echo "    https://cli.github.com"
  echo ""
  echo "✅  Branch pushed. Open a PR manually:"
  echo "    https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//' | sed 's/\.git$//')/compare/$BRANCH"
fi