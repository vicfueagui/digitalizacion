"""Lista cerrada de código distribuible: nunca incluye datos de trabajo."""
from pathlib import PurePosixPath

ROOT_FILES = {
    'iniciar_web.py', 'transicion_web.py', 'requirements-modern.txt',
    'main.py', 'actualizar.py', 'asistente_actualizacion.py', 'instalar_visor.py', 'README.md', 'ACTUALIZACION.html',
    'requirements.txt', 'requirements-legacy.txt', 'requirements-laptop.txt',
    'INICIAR.bat', 'DIAGNOSTICO.bat', 'PROBAR.bat', 'INSTALAR_VISOR.bat', 'ACTUALIZAR.bat',
    'iniciar.sh', '.gitignore', '.dockerignore', 'AGENTS.md',
}


def allowed(name):
    path = PurePosixPath(name)
    if '\\' in name or path.is_absolute() or '..' in path.parts or ':' in name:
        return False
    if name in ROOT_FILES:
        return True
    # Distribución web explícita: ningún workspace ni configuración de acceso.
    if len(path.parts) == 2 and path.parts[0] == 'webapp' and path.suffix == '.py':
        return True
    if len(path.parts) == 3 and path.parts[:2] == ('webapp','migrations') and path.suffix == '.py':
        return True
    if len(path.parts) == 3 and path.parts[:2] == ('webapp', 'templates') and path.suffix == '.html':
        return True
    if name in {'webapp/static/app.css', 'webapp/static/app.js', 'webapp/static/charts.js',
                'webapp/static/ux.css', 'webapp/static/ux.js', 'webapp/static/desk.js'}:
        return True
    if len(path.parts) == 4 and path.parts[:3] == ('webapp', 'static', 'vendor') and path.name in {
            'bootstrap.min.css', 'htmx.min.js', 'chart.umd.min.js', 'manifest.json',
            'BOOTSTRAP-LICENSE.txt', 'HTMX-LICENSE.txt', 'CHARTJS-LICENSE.txt'}:
        return True
    if len(path.parts) != 2:
        return False
    folder = path.parts[0]
    return ((folder == 'app' and path.suffix in ('.py', '.sql')) or
            (folder in ('tests', 'tools') and path.suffix == '.py') or
            (folder == 'docs' and (path.suffix == '.md' or path.name == 'MANUAL_USUARIO.html')) or
            (folder == 'instaladores' and path.name in (
                'Pillow-9.5.0-cp38-cp38-win_amd64.whl', 'SHA256.txt', 'LICENCIA_PILLOW.txt')))
