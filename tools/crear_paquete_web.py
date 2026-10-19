"""Paquete de código con lista permitida. Nunca incluye el workspace de demo."""
import argparse
import json
from pathlib import Path
import shutil
import sys

CODE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE))
from app import VERSION
from app.backup import sha256
from app.release import allowed
from app.manifests import plain_path

LAUNCHER = '''@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0python_web_ruta.txt" (
    echo Falta completar la activacion web. No se abrira una base distinta.
    pause
    exit /b 1
)
set "DIG_WEB_PYTHON="
set /p "DIG_WEB_PYTHON="<"%~dp0python_web_ruta.txt"
if not exist "%DIG_WEB_PYTHON%" (
    echo No se encuentra el entorno Python verificado. Conserva la carpeta de runtime.
    pause
    exit /b 1
)
"%DIG_WEB_PYTHON%" -B "%~dp0iniciar_web.py" --workspace "%~dp0." --operacion
set "DIG_WEB_RESULT=%ERRORLEVEL%"
if not "%DIG_WEB_RESULT%"=="0" pause
exit /b %DIG_WEB_RESULT%
'''


def build(destination):
    destination = Path(destination).resolve()
    if destination == CODE or CODE in destination.parents or destination in CODE.parents:
        raise ValueError('El paquete debe vivir separado del código de preparación.')
    names = ['main.py', 'actualizar.py', 'iniciar_web.py', 'transicion_web.py', 'requirements-modern.txt']
    for directory in ('app', 'webapp'):
        names.extend(p.relative_to(CODE).as_posix() for p in (CODE / directory).rglob('*')
                     if p.is_file() and allowed(p.relative_to(CODE).as_posix()))
    names.extend('docs/' + n for n in ('GUIA_WEB_V080.md', 'GUIA_WEB_V081.md', 'GUIA_ESTACION_TIFF_V082.md', 'OPERACION_V05.md', 'INTEGRACIONES_V070.md', 'RECEPCION_INDICADORES_V061.md'))
    destination.mkdir(parents=True, exist_ok=False)
    files = {}
    for name in sorted(names):
        if not allowed(name): raise ValueError('Ruta de código fuera de la lista permitida.')
        source = plain_path(CODE, name)
        out = plain_path(destination, name)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(out))
        files[name] = sha256(out)
        if files[name] != sha256(source): raise ValueError('Copia de código incompleta: ' + name)
    launcher = destination / 'INICIAR.bat'
    launcher.write_bytes(LAUNCHER.replace('\n', '\r\n').encode('ascii'))
    files['INICIAR.bat'] = sha256(launcher)
    manifest = {'format': 1, 'version': VERSION, 'files': files}
    (destination / 'release-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destino', required=True)
    result = build(parser.parse_args().destino)
    print('Paquete de código creado:', len(result['files']), 'archivos; sin datos ni cuentas.')
