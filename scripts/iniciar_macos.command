#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SETUP_SCRIPT="$SCRIPT_DIR/preparar_macos.command"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SERVER_HOST="127.0.0.1"
SERVER_PORT="${DIGITALIZACION_PORT:-8000}"

cd "$PROJECT_DIR"

case "$SERVER_PORT" in
    ''|*[!0-9]*)
        echo "ERROR: DIGITALIZACION_PORT debe ser un número de puerto válido." >&2
        exit 1
        ;;
esac

if (( SERVER_PORT < 1 || SERVER_PORT > 65535 )); then
    echo "ERROR: El puerto debe estar entre 1 y 65535." >&2
    exit 1
fi

if [[ ! -x "$VENV_PYTHON" || ! -f "$PROJECT_DIR/.env" ]]; then
    echo "La instalación local todavía no está preparada. Iniciando preparación..."
    "$SETUP_SCRIPT"
fi

"$VENV_PYTHON" manage.py check
"$VENV_PYTHON" manage.py migrate --noinput

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$SERVER_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERROR: El puerto $SERVER_PORT ya está ocupado." >&2
    echo "Cierre el proceso que lo usa o ejecute, por ejemplo:" >&2
    echo "  DIGITALIZACION_PORT=8001 $0" >&2
    exit 1
fi

APP_URL="http://$SERVER_HOST:$SERVER_PORT/"

if [[ "${DIGITALIZACION_OPEN_BROWSER:-1}" != "0" ]]; then
    (
        attempt=0
        while (( attempt < 80 )); do
            if /usr/bin/curl --silent --fail "$APP_URL" >/dev/null 2>&1; then
                /usr/bin/open "$APP_URL" >/dev/null 2>&1 || true
                exit 0
            fi
            attempt=$((attempt + 1))
            sleep 0.25
        done
        echo "AVISO: El servidor no respondió a tiempo; abra manualmente $APP_URL" >&2
    ) &
fi

echo
echo "Sistema disponible en $APP_URL"
echo "La aplicación solo escucha en esta computadora."
echo "Para detenerla presione Control+C en esta ventana."
echo

exec "$VENV_PYTHON" manage.py runserver "$SERVER_HOST:$SERVER_PORT" --noreload
