#!/usr/bin/env bash
# deploy.sh — manual emergency deploy to Fly.io
# ⚠️  This bypasses CI/CD. Normal deploys happen automatically via cd.yml on merge to main.
# Usage: ./scripts/deploy.sh

set -e

BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "⚠️  MANUAL DEPLOY"
echo "   Branch: $BRANCH"
echo "   This bypasses the normal PR → staging → main workflow."
echo ""
read -rp "Are you sure you want to deploy manually? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Cancelled."
  exit 0
fi

echo "🚀  Deploying to Fly.io..."
fly deploy
echo "✅  Deploy complete."
echo "    Run 'fly logs' to monitor."