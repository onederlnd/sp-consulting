#!/bin/bash
# done.sh — Clean up a merged feature branch locally and remotely
# Usage: ./done.sh feature/my-branch [base-branch]
# Base branch defaults to main if not specified.

set -e

FEATURE_BRANCH="${1}"
BASE_BRANCH="${2:-main}"

if [ -z "$FEATURE_BRANCH" ]; then
  echo "Usage: ./cleanup.sh <feature-branch> [base-branch]"
  exit 1
fi

echo "→ Switching to $BASE_BRANCH..."
git checkout "$BASE_BRANCH"

echo "→ Pulling latest $BASE_BRANCH..."
git pull origin "$BASE_BRANCH"

echo "→ Deleting remote branch $FEATURE_BRANCH..."
git push origin --delete "$FEATURE_BRANCH" || echo "  Remote branch not found, skipping."

echo "→ Deleting local branch $FEATURE_BRANCH..."
git branch -d "$FEATURE_BRANCH" || echo "  Local branch not found or not fully merged, skipping."

echo "→ Pruning stale remote refs..."
git fetch --prune

echo "→ Cleaning up other stale local branches..."
git branch -vv | grep 'gone]' | awk '{print $1}' | xargs -r git branch -d

echo "✓ Done. Current branch: $(git branch --show-current)"
