"""Resolución comprobada del intérprete. Existir no significa poder ejecutarse."""
import json
import os
from pathlib import Path
import subprocess
import sys

PROBE = r'''import json,platform,struct,sqlite3,sys
value=dict(python=platform.python_version(),implementacion=platform.python_implementation(),python_bits=struct.calcsize('P')*8,
 sistema=platform.system(),sistema_version=platform.release(),ejecutable=sys.executable,sqlite=sqlite3.sqlite_version,
 tk=None,tcl=None,pillow=None,libtiff=False,libtiff_version=None)
try:
 import tkinter
 value['tk']=str(tkinter.TkVersion);value['tcl']=tkinter.Tcl().eval('info patchlevel')
except Exception as error:value['error_tk']=type(error).__name__
try:
 import PIL
 from PIL import Image,ImageTk,features
 value.update(pillow=PIL.__version__,libtiff=bool(features.check('libtiff')),libtiff_version=features.version('libtiff'))
except Exception as error:value['error_pillow']=type(error).__name__
print(json.dumps(value))
'''


def environment():
    env=dict(os.environ)
    for key in ('PYTHONHOME','PYTHONPATH'):env.pop(key,None)
    env['PYTHONIOENCODING']='utf-8';env['PYTHONDONTWRITEBYTECODE']='1'
    env['DIGITALIZACION_PROBAR_FUENTES_PRIVADAS']='0'
    return env


def validate(info,profile='legado'):
    if info.get('implementacion')!='CPython' or info.get('python_bits')!=64:
        raise ValueError('Se requiere CPython de 64 bits.')
    if not info.get('tk') or not info.get('tcl'):raise ValueError('Tk/Tcl no funciona en este intérprete.')
    if profile in ('legado','instalar') and info.get('python')!='3.8.10':
        raise ValueError('La primera migración requiere exactamente Python 3.8.10.')
    if profile in ('legado','instalar') and info.get('tk')!='8.6':
        raise ValueError('La primera migración requiere Tk 8.6.')
    if profile=='legado' and info.get('pillow')!='9.5.0':raise ValueError('La primera migración requiere Pillow 9.5.0.')
    if profile!='instalar' and (not info.get('pillow') or not info.get('libtiff')):
        raise ValueError('Pillow con soporte libtiff no está disponible.')
    if profile not in ('legado','instalar','laboratorio'):raise ValueError('Perfil desconocido.')


def probe(executable,profile='legado'):
    executable=Path(executable)
    if not executable.is_absolute():raise ValueError('La ruta del intérprete debe ser absoluta.')
    if not executable.is_file() or executable.stat().st_size==0:raise ValueError('Intérprete ausente o de 0 bytes.')
    # En Windows no resolve(): un .venv mantiene su identidad y pyvenv.cfg.
    process=subprocess.run([str(executable),'-I','-c',PROBE],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           encoding='utf-8',env=environment(),timeout=30)
    if process.returncode:raise ValueError('El intérprete no se ejecuta correctamente (código '+str(process.returncode)+').')
    try:info=json.loads(process.stdout)
    except (ValueError,TypeError):raise ValueError('El intérprete no produjo un diagnóstico válido.')
    validate(info,profile)
    return info


def registered_python():
    if os.name!='nt':return []
    import winreg
    paths=[]
    for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY):
            for tag in ('3.8','3.8-64'):
                try:
                    with winreg.OpenKey(hive,'SOFTWARE\\Python\\PythonCore\\'+tag+'\\InstallPath',0,winreg.KEY_READ|view) as key:
                        try:path=winreg.QueryValueEx(key,'ExecutablePath')[0]
                        except OSError:path=str(Path(winreg.QueryValueEx(key,'')[0])/'python.exe')
                        paths.append(path)
                except OSError:continue
    return paths


def candidates(root,configured=None,extra=()):
    root=Path(root).absolute()
    result=[root/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')]
    if configured:result.append(Path(configured).expanduser())
    config=root/'python_ruta.txt'
    if config.is_file():
        value=config.read_text(encoding='utf-8-sig').strip()
        if value and '\n' not in value and '\r' not in value:
            result.append(Path(value.strip('"')).expanduser())
    if os.environ.get('DIGITALIZACION_PYTHON'):result.append(Path(os.environ['DIGITALIZACION_PYTHON']))
    result.extend(Path(p) for p in registered_python())
    result.extend(Path(p) for p in extra)
    result.append(Path(sys.executable))
    unique=[];seen=set()
    for path in result:
        name=str(path).casefold() if os.name=='nt' else str(path)
        if name not in seen:seen.add(name);unique.append(path)
    return unique


def resolve(root,configured=None,profile='legado',extra=()):
    rejected=[]
    for path in candidates(root,configured,extra):
        try:
            info=probe(path,profile)
            return path,info,rejected
        except (ValueError,OSError,subprocess.TimeoutExpired) as error:
            rejected.append({'candidato':str(path),'motivo':str(error)})
    raise ValueError('No se encontró un intérprete válido para '+profile+'.\n'+
                     '\n'.join(r['candidato']+': '+r['motivo'] for r in rejected))
