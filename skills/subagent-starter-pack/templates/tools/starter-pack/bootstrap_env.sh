#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
REQUIREMENTS_FILE="$REPO_ROOT/tools/starter-pack/requirements.txt"

if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  echo "Missing requirements file: $REQUIREMENTS_FILE" >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  if command -v uv >/dev/null 2>&1; then
    if ! uv venv "$VENV_DIR"; then
      echo "uv venv failed; falling back to python3 -m venv" >&2
      rm -rf "$VENV_DIR"
      python3 -m venv "$VENV_DIR"
    fi
  else
    python3 -m venv "$VENV_DIR"
  fi
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$REQUIREMENTS_FILE"

echo "Starter-pack validation environment ready at $VENV_DIR"
echo "Run: $VENV_DIR/bin/python tools/starter-pack/validate.py"
