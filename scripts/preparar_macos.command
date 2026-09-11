#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

cd "$PROJECT_DIR"

select_python() {
    if command -v python3.12 >/dev/null 2>&1; then
        command -v python3.12
        return
    fi

    if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
        command -v python3
        return
    fi

    echo "ERROR: No se encontró Python 3.12 o posterior." >&2
    echo "Instale Python 3.12 para macOS y vuelva a ejecutar este archivo." >&2
    exit 1
}

if [[ ! -x "$VENV_PYTHON" ]]; then
    if [[ -e "$VENV_DIR" ]]; then
        echo "ERROR: .venv existe, pero no contiene un entorno Python utilizable." >&2
        echo "Renombre esa carpeta y vuelva a ejecutar la preparación." >&2
        exit 1
    fi

    SYSTEM_PYTHON="$(select_python)"
    echo "Creando entorno virtual con $SYSTEM_PYTHON..."
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
fi

echo "Instalando dependencias del proyecto..."
"$VENV_PYTHON" -m pip install -r requirements.txt

echo "Preparando configuración local privada..."
"$VENV_PYTHON" scripts/prepare_local_env.py

echo "Aplicando migraciones..."
"$VENV_PYTHON" manage.py migrate --noinput

echo "Cargando catálogos y permisos iniciales..."
"$VENV_PYTHON" manage.py initialize_system

echo "Verificando la instalación..."
"$VENV_PYTHON" manage.py check

echo
echo "Preparación terminada correctamente."
echo "Para crear una cuenta administradora ejecute:"
echo "  $VENV_PYTHON manage.py createsuperuser"
echo
echo "Después abra scripts/iniciar_macos.command."
