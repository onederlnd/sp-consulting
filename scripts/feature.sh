#!/usr/bin/env bash
# feature.sh — create a new branch from latest main
# Usage: ./scripts/feature.sh [branch-name]
# If no branch name is provided, you will be prompted.

set -e

# ── Get branch name ──────────────────────────────────────────────────────────
if [ -n "$1" ]; then
  BRANCH="$1"
else
  read -rp "Branch name (e.g. feature/my-feature, fix/bug-name): " BRANCH
fi

if [ -z "$BRANCH" ]; then
  echo "❌  Branch name required."
  exit 1
fi

# ── Sync main ────────────────────────────────────────────────────────────────
echo "⬇️  Syncing main..."
git checkout main
git pull origin main

# ── Create branch ────────────────────────────────────────────────────────────
git checkout -b "$BRANCH"
echo "✅  Branch '$BRANCH' created from latest main."
echo "    Start working, then run ./scripts/ship.sh when ready."