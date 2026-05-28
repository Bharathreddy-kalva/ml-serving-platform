#!/usr/bin/env bash
# Create and populate the Python virtual environment for the ML pipeline.
# Run from the repo root:  bash ml/setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
REQUIREMENTS="$REPO_ROOT/ml/requirements.txt"

# ── Python version check ──────────────────────────────────────────────────────
PYTHON=$(command -v python3.11 2>/dev/null || command -v python3 2>/dev/null || true)
if [[ -z "$PYTHON" ]]; then
  echo "ERROR: python3 not found on PATH" >&2
  exit 1
fi

PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [[ "$PYTHON_MAJOR" -lt 3 || ("$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 10) ]]; then
  echo "ERROR: Python 3.10+ required, found $PYTHON_VERSION" >&2
  exit 1
fi
echo "Using Python $PYTHON_VERSION ($PYTHON)"

# ── Create venv ───────────────────────────────────────────────────────────────
if [[ -d "$VENV_DIR" ]]; then
  echo "Virtual environment already exists at $VENV_DIR"
  echo "To recreate it: rm -rf $VENV_DIR && bash ml/setup.sh"
else
  echo "Creating virtual environment at $VENV_DIR ..."
  "$PYTHON" -m venv "$VENV_DIR"
fi

# ── Install dependencies ──────────────────────────────────────────────────────
echo "Installing dependencies from $REQUIREMENTS ..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS"

echo ""
echo "Setup complete."
echo ""
echo "  Activate with:  source .venv/bin/activate"
echo "  Or run directly: .venv/bin/python ml/scripts/train.py"
