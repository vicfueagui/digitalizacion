"""Ensayo reproducible de oficina: solo datos ficticios, sin abrir producción."""
import argparse
import json
import os
import platform
import sqlite3
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import VERSION
from app.workspace import absolute
from app.backup import sha256


def main():
    parser = argparse.ArgumentParser(description='Ensayo local con datos ficticios y resultados para revisión')
    parser.add_argument('--destino', required=True, help='Carpeta NUEVA para la demo, respaldo, restauración e informe')
    parser.add_argument('--ventanas', action='store_true', help='También abrir la aplicación y el visor de prueba')
    args = parser.parse_args()
    destination = absolute(args.destino)
    destination.mkdir(parents=True, exist_ok=False)
    info = {'version_aplicacion': VERSION, 'sistema': platform.system(), 'sistema_version': platform.release(),
            'service_pack': platform.win32_ver()[2] if sys.platform == 'win32' else None,
            'python_implementacion': platform.python_implementation(),
            'arquitectura': platform.machine(), 'python': platform.python_version(), 'python_bits': struct.calcsize('P')*8,
            'sqlite': sqlite3.sqlite_version, 'pillow': None, 'libtiff': False}
    try:
        import PIL
        from PIL import features
        info.update(pillow=PIL.__version__, libtiff=features.check('libtiff'))
    except ImportError:
        pass
    results = {'entorno': info, 'etapas': [], 'pruebas': None,
               'perfil_windows7_coincide': sys.platform == 'win32' and platform.release() == '7' and info['service_pack'] == 'SP1' and info['python_implementacion'] == 'CPython' and sys.version_info[:3] == (3,8,10) and info['python_bits'] == 64 and info['pillow'] == '9.5.0' and info['libtiff'],
               'perfil_windows10_conservador': sys.platform == 'win32' and platform.release() == '10' and sys.getwindowsversion().build < 22000 and info['python_implementacion'] == 'CPython' and sys.version_info[:3] == (3,8,10) and info['python_bits'] == 64 and info['pillow'] == '9.5.0' and info['libtiff'],
               'revision_manual_pendiente': ['Teclado español y teclado numérico físicos', 'Nitidez, rueda/trackpad y disposición de paneles', 'Rendimiento con tamaños representativos en el equipo de oficina', 'Comparación de una copia autorizada antes de abrir producción'],
               'produccion_validada': False, 'comprobaciones_automaticas_correctas': False}
    report = destination / 'resultado.json'
    # Aunque la carpeta del código contenga fuentes privadas, este ensayo no las habilita.
    child_env = dict(os.environ)
    child_env['DIGITALIZACION_PROBAR_FUENTES_PRIVADAS'] = '0'
    child_env['PYTHONIOENCODING'] = 'utf-8'
    def run(name, arguments, timeout=600):
        print('Comprobando: ' + name, flush=True)
        logfile = destination / (name + '.log')
        try:
            with logfile.open('x', encoding='utf-8') as out:
                process = subprocess.run([sys.executable]+[str(a) for a in arguments], cwd=str(ROOT), env=child_env,
                                         stdout=out, stderr=subprocess.STDOUT, timeout=timeout)
            status = process.returncode == 0
            result = {'etapa': name, 'correcto': status, 'codigo_salida': process.returncode, 'registro': logfile.name}
        except (OSError, subprocess.TimeoutExpired) as error:
            status = False
            result = {'etapa': name, 'correcto': False, 'error': str(error), 'registro': logfile.name}
        results['etapas'].append(result)
        return status
    try:
        demo = destination / 'demo'
        suite_ok = run('pruebas', [ROOT/'tools/run_tests.py', '--resultado', destination/'pruebas.json'])
        if (destination/'pruebas.json').exists():
            results['pruebas'] = json.loads((destination/'pruebas.json').read_text(encoding='utf-8'))
        if run('crear_demo', [ROOT/'main.py', '--crear-demo', demo]):
            run('diagnostico', [ROOT/'main.py', '--workspace', demo, '--diagnostico'])
            before = sha256(demo/'datos/digitalizacion.sqlite3')
            backup = destination/'respaldo'
            if run('respaldar', [ROOT/'main.py','--workspace',demo,'--respaldar',backup]):
                run('verificar', [ROOT/'main.py','--verificar-respaldo',backup])
                if run('restaurar', [ROOT/'main.py','--restaurar',backup,'--destino',destination/'restaurado']):
                    run('diagnostico_restaurado', [ROOT/'main.py','--workspace',destination/'restaurado','--diagnostico'])
            results['etapas'].append({'etapa':'base_de_demo_intacta_al_respaldar', 'correcto':sha256(demo/'datos/digitalizacion.sqlite3') == before})
            if args.ventanas:
                run('ventanas', [ROOT/'tools/smoke_ui.py'], timeout=120)
                run('asistente', [ROOT/'tools/smoke_update_assistant.py'], timeout=120)
        results['comprobaciones_automaticas_correctas'] = suite_ok and all(item['correcto'] for item in results['etapas'])
    finally:
        with report.open('x', encoding='utf-8') as out: json.dump(results, out, ensure_ascii=False, indent=2)
    print('Informe local: ' + str(report))
    print('No se abrió producción. Las comprobaciones físicas continúan pendientes.')
    return 0 if results['comprobaciones_automaticas_correctas'] else 1


if __name__ == '__main__':
    try: sys.exit(main())
    except (ValueError, OSError) as error:
        print('Ensayo detenido:', error, file=sys.stderr); sys.exit(1)
