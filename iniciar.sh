#!/bin/sh
set -eu
DIG_PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$DIG_PROJECT_DIR/.venv/bin/python" ]; then
    echo "Falta .venv. Sigue docs/LAPTOP.md."
    exit 1
fi
exec "$DIG_PROJECT_DIR/.venv/bin/python" "$DIG_PROJECT_DIR/main.py" "$@"
