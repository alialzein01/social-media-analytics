#!/usr/bin/env bash
# Helper to run commands inside the project's virtualenv named 'venv'.
# Usage: ./scripts/run_in_venv.sh pytest -q

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$DIR/venv"

if [ ! -d "$VENV" ]; then
  echo "Virtualenv not found at $VENV"
  echo "Create one with: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# Activate venv
# shellcheck disable=SC1090
source "$VENV/bin/activate"

# Run the provided command
if [ $# -eq 0 ]; then
  echo "No command provided. Example: ./scripts/run_in_venv.sh pytest -q"
  exec "$SHELL"
else
  exec "$@"
fi
