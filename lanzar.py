"""Despacho compartido: ruta del código fija y workspace configurable explícito."""
from pathlib import Path
import subprocess
import sys
from app.runtime import environment

ROOT=Path(__file__).resolve().parent


def command(action,arguments):
    entries={'iniciar':['main.py'],'diagnostico':['main.py','--diagnostico'],
             'probar':['-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],
             'actualizar':['asistente_actualizacion.py'],'instalar':['preparar_entorno.py'],
             'migracion':['migrar.py'],'integridad':['migrar.py','--auditar']}
    if action not in entries:raise ValueError('Acción desconocida.')
    args=list(entries[action])
    if args[0].endswith('.py'):args[0]=str(ROOT/args[0])
    config=ROOT/'workspace_ruta.txt'
    if action in ('iniciar','diagnostico') and not any(a in ('--workspace','--db') or a.startswith(('--workspace=','--db=')) for a in arguments) and config.is_file():
        root=config.read_text(encoding='utf-8-sig').strip().strip('"')
        if not Path(root).is_absolute() or '\n' in root:raise ValueError('workspace_ruta.txt requiere una ruta absoluta, sin argumentos.')
        args+=['--workspace',root]
    return [sys.executable]+args+list(arguments)


def main():
    if len(sys.argv)<2:raise ValueError('Falta la acción del lanzador.')
    return subprocess.call(command(sys.argv[1],sys.argv[2:]),cwd=str(ROOT),env=environment())


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as error:print('No se pudo iniciar:',error,file=sys.stderr);sys.exit(1)
