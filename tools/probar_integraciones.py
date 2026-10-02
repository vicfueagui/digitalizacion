"""Ejecuta solo fixtures nuevos y bloquea accesos Python a datos ajenos al ensayo."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from urllib.parse import unquote,urlsplit

CODE=Path(__file__).resolve().parent.parent
sys.dont_write_bytecode=True
sys.path[:0]=[str(CODE),str(CODE/'tests')]
RUN=CODE.parent/('pruebas-'+uuid.uuid4().hex[:10]);RUN.mkdir()
(RUN/'tmp').mkdir();tempfile.tempdir=str(RUN/'tmp')
os.environ['TEMP']=os.environ['TMP']=str(RUN/'tmp')
os.environ['CONTEXTO_TEST_DIR']=str(RUN/'tmp')
os.environ['DIGITALIZACION_PROBAR_FUENTES_PRIVADAS']='0'
violations=[]

def check(value,write=False):
    if isinstance(value,int) or value is None:return
    value=os.fsdecode(value)
    if str(value)==':memory:':return
    if str(value).startswith('file:'):
        value=unquote(urlsplit(value).path)
        if len(value)>2 and value[0]=='/' and value[2]==':':value=value[1:]
    path=Path(os.path.abspath(os.fsdecode(value))).resolve()
    inside=path==RUN or RUN in path.parents
    project=Path('C:/Digitalizacion')
    forbidden=write and not inside
    if project in path.parents and not inside and CODE not in path.parents and (project/'.venv') not in path.parents:forbidden=True
    if forbidden:violations.append({'evento':'ruta','escritura':write});raise PermissionError('Acceso fuera del ensayo sintético')

def audit(event,args):
    if event=='open':
        mode,flags=args[1:3];check(args[0],bool((mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)))
    elif event=='sqlite3.connect':check(args[0],True)
    elif event in ('os.remove','os.rmdir','os.mkdir','os.chmod','os.utime'):check(args[0],True)
    elif event in ('os.rename','os.link','os.symlink'):check(args[0],True);check(args[1],True)
    elif event in ('subprocess.Popen','os.system','os.startfile'):raise PermissionError('Procesos externos desactivados en pruebas')

sys.addaudithook(audit)
names=sys.argv[1:]
suite=unittest.defaultTestLoader.loadTestsFromNames(names) if names else unittest.defaultTestLoader.discover(str(CODE/'tests'))
with (RUN/'pruebas.txt').open('x',encoding='utf-8') as output:
    result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
data={'ejecutadas':result.testsRun,'aprobadas':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),'fallos':len(result.failures),'errores':len(result.errors),'omitidas':len(result.skipped),'bloqueos':violations,'correcto':result.wasSuccessful(),'python':sys.version}
(RUN/'resultado.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(RUN));print(json.dumps(data,ensure_ascii=True));sys.exit(0 if result.wasSuccessful() else 1)
