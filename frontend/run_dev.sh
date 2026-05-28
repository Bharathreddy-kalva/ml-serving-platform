#!/usr/bin/env bash
# Start the React frontend dev server on port 3000.
# Run from the repo root: bash frontend/run_dev.sh

set -euo pipefail

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v node &>/dev/null; then
  echo "ERROR: node not found on PATH" >&2
  exit 1
fi

echo "Node  $(node --version)"
echo "npm   $(npm --version)"
echo ""

cd "$FRONTEND_DIR"

echo "Installing dependencies..."
npm install --prefer-offline 2>&1 | tail -5

echo ""
echo "  Dashboard : http://localhost:3000"
echo "  API proxy : /api  →  http://localhost:8000"
echo ""

exec npm run dev
