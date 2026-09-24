"""Lista cerrada de código distribuible: nunca incluye datos de trabajo."""
from pathlib import PurePosixPath

ROOT_FILES = {
    'migrar.py', 'diagnosticar_integridad.py', 'auditar_integridad_tiff.py',
    'python_runtime.py', 'preparar_entorno.py', 'lanzar.py', 'ejecutar_python.ps1',
    'EJECUTAR.bat', 'MIGRAR.bat', 'AUDITAR_INTEGRIDAD.bat',
    'MIGRACION_WINDOWS10.md', 'MIGRACION_WINDOWS10.html', 'requirements-modern-lab.txt',
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
    if len(path.parts) != 2:
        return False
    folder = path.parts[0]
    return ((folder == 'app' and path.suffix in ('.py', '.sql')) or
            (folder in ('tests', 'tools') and path.suffix == '.py') or
            (folder == 'docs' and (path.suffix == '.md' or path.name == 'MANUAL_USUARIO.html')) or
            (folder == 'instaladores' and path.name in (
                'Pillow-9.5.0-cp38-cp38-win_amd64.whl', 'SHA256.txt', 'LICENCIA_PILLOW.txt')))
