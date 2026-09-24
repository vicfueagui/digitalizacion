"""Diagnóstico de lectura y huellas de todas las tablas; no abre Store ni migra."""
import ast
import datetime
import hashlib
import json
import platform
import shutil
import sqlite3
import struct
import sys
import tempfile
from pathlib import Path

from .backup import snapshot,sha256,inventory_files
from .manifests import plain_path
from .portability import active_relative
from .update_recovery import database_fingerprint,write_json
from .workspace import WorkspaceLock

REFERENCES=(('archivos_tiff','ruta','hash_actual','actual'),
            ('archivos_tiff','original','hash_original','original'),
            ('revisiones_tiff','ruta','hash','revision'),
            ('versiones_archivo','ruta','sha256','version'))


def runtime_info():
    data={'python':platform.python_version(),'implementacion':platform.python_implementation(),
          'python_bits':struct.calcsize('P')*8,'ejecutable':sys.executable,
          'sistema':platform.system(),'sistema_version':platform.release(),
          'sistema_detalle':platform.version(),'arquitectura_so':platform.machine(),
          'sqlite':sqlite3.sqlite_version,'tk':None,'tcl':None,'pillow':None,'libtiff':False,'libtiff_version':None}
    try:
        import tkinter
        data['tk']=str(tkinter.TkVersion)
        data['tcl']=tkinter.Tcl().eval('info patchlevel')
    except Exception as error:data['error_tk']=type(error).__name__
    try:
        import PIL
        from PIL import features
        data.update(pillow=PIL.__version__,libtiff=bool(features.check('libtiff')),
                    libtiff_version=features.version('libtiff'))
    except ImportError:pass
    return data


def code_version(root):
    """Leer una constante, sin ejecutar código de una carpeta transferida."""
    tree=ast.parse(plain_path(root,'app/__init__.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id=='VERSION' for n in node.targets):
            value=ast.literal_eval(node.value)
            if isinstance(value,str):return value
    raise ValueError('El código no declara una versión reconocible.')


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def content_digest(value):return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def quote(name):return '"'+name.replace('"','""')+'"'


def row_value(value):
    if isinstance(value,bytes):return ['blob',value.hex()]
    if isinstance(value,float):return ['float',value.hex()]
    return [type(value).__name__,value]


def database_summary(db):
    """SHA por tabla incluye todas sus columnas/filas, duplicados y tipos SQLite.

    Ordenar hashes evita depender de rowid/orden físico o de la letra de unidad.
    Conserva esquema, índices y triggers; nunca expone los valores de las filas.
    """
    schema=[list(r) for r in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name")]
    tables={}
    for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        columns=[r[1] for r in db.execute('PRAGMA table_info('+quote(name)+')')]
        hashes=[]
        for row in db.execute('SELECT * FROM '+quote(name)):
            hashes.append(bytes.fromhex(content_digest([row_value(v) for v in row])))
        digest=hashlib.sha256()
        for value in sorted(hashes):digest.update(value)
        tables[name]={'filas':len(hashes),'columnas':columns,'sha256_filas':digest.hexdigest()}
    result={'esquema_sha256':content_digest(schema),'tablas':tables}
    result['sha256_logico']=content_digest(result)
    return result


def read_summary(database):
    db=sqlite3.connect(Path(database).as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN');return database_summary(db)
    finally:db.close()


def audit_database(database,workspace,decode=True):
    db=sqlite3.connect(Path(database).as_uri()+'?mode=ro',uri=True)
    issues=[];counts={'referencias':0,'correctas':0,'faltantes':0,'hash_incorrecto':0,'rutas_invalidas':0,
                     'actual':0,'original':0,'revision':0,'version':0,'tiff_activos':0,'paginas_activas':0}
    checked={};valid=set();tables=set()
    def problem(kind,table=None,ident=None,field=None):
        issues.append({'tipo':kind,'tabla':table,'id':ident,'campo':field})
    try:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':problem('sqlite_integridad')
        foreign=db.execute('PRAGMA foreign_key_check').fetchall()
        for table,rowid,parent,key in foreign:problem('relacion_invalida',table,rowid,str(key))
        summary=database_summary(db);tables=set(summary['tablas'])
        for table,field,hashfield,kind in REFERENCES:
            if table not in tables:continue
            for ident,value,expected in db.execute('SELECT id,'+field+','+hashfield+' FROM '+table):
                counts['referencias']+=1;counts[kind]+=1
                try:relative=active_relative(workspace,value);path=plain_path(workspace.root,relative)
                except (ValueError,OSError):
                    counts['rutas_invalidas']+=1;problem('ruta_invalida',table,ident,field);continue
                try:
                    if not path.is_file():
                        counts['faltantes']+=1;problem('faltante',table,ident,field);continue
                    if relative not in checked:
                        info={'sha256':sha256(path),'paginas':None}
                        if decode:
                            from .coding import page_info
                            info['paginas']=len(page_info(path,True))
                        checked[relative]=info
                    info=checked[relative]
                    if info['sha256']!=expected:
                        counts['hash_incorrecto']+=1;problem('hash_incorrecto',table,ident,field);continue
                    if decode and table=='archivos_tiff' and field=='ruta':
                        registered=db.execute('SELECT paginas FROM archivos_tiff WHERE id=?',(ident,)).fetchone()[0]
                        if registered!=info['paginas']:problem('paginas_diferentes',table,ident,field);continue
                    if table=='versiones_archivo':
                        expected_bytes,expected_pages=db.execute('SELECT bytes,paginas FROM versiones_archivo WHERE id=?',(ident,)).fetchone()
                        if path.stat().st_size!=expected_bytes or (decode and info['paginas']!=expected_pages):
                            problem('version_metadata_diferente',table,ident,field);continue
                    counts['correctas']+=1;valid.add(relative)
                except (OSError,ValueError,EOFError,RuntimeError):problem('ilegible_o_inaccesible',table,ident,field)
        if 'archivos_tiff' in tables:
            counts['tiff_activos'],counts['paginas_activas']=db.execute('SELECT COUNT(*),COALESCE(SUM(paginas),0) FROM archivos_tiff WHERE activo=1').fetchone()
        for table,condition in (('operaciones_tiff',"estado='Preparada'"),
                                ('sustituciones_tiff',"fase!='Completada'"),
                                ('entregas',"estado IN ('Preparando','Incompleta')")):
            if table in tables and db.execute('SELECT COUNT(*) FROM '+table+' WHERE '+condition).fetchone()[0]:
                problem('operacion_incompleta',table)
        try:inventory_files(database,workspace)
        except (ValueError,OSError,sqlite3.Error,KeyError,TypeError):
            if not issues:problem('referencias_o_entregas_invalidas')
        return {'correcto':not issues,'resumen_base':summary,'tiff':counts,'problemas':issues,
                'archivos_tiff_unicos_verificados':len(valid),'paginas_decodificadas':decode}
    finally:db.close()


def diagnose(workspace,code_root=None,locked=False):
    if not workspace.database.is_file():raise ValueError('No existe la base. El diagnóstico no crea workspaces.')
    lock=None if locked else WorkspaceLock(workspace.root)
    try:
        report={'formato':1,'fecha':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
                'entorno':runtime_info(),'workspace':str(workspace.root),'base':str(workspace.database),
                'base_bytes':workspace.database.stat().st_size,'espacio_libre_bytes':shutil.disk_usage(workspace.root).free,
                'version_aplicacion':code_version(code_root) if code_root else None}
        for marker in ('.actualizacion_pendiente.json','.restauracion_incompleta'):
            if (workspace.root/marker).exists():raise ValueError('La instalación tiene una operación incompleta: '+marker)
        try:
            with tempfile.TemporaryDirectory(prefix='digitalizacion-diagnostico-') as temp:
                copied=Path(temp)/'snapshot.sqlite3'
                db=sqlite3.connect(workspace.database.as_uri()+'?mode=ro',uri=True)
                try:
                    db.execute('BEGIN')
                    report['huella_logica_origen']=database_fingerprint(db)
                    snapshot(db,copied)
                finally:db.close()
                report.update(audit_database(copied,workspace))
        except (sqlite3.Error,ValueError) as error:
            report.update(correcto=False,resumen_base={'tablas':{},'sha256_logico':None},
                          tiff={'correctas':0,'referencias':0},
                          problemas=[{'tipo':'sqlite_o_estructura_invalida','detalle':type(error).__name__}])
        return report
    finally:
        if lock:lock.close()


def save_report(report,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    write_json(destination/'diagnostico.json',report)
    lines=['DIAGNOSTICO '+('CORRECTO' if report['correcto'] else 'CON PROBLEMAS'),
           'No se modificó la base ni ningún TIFF. Informe local; no se envía información.',
           'Python: '+report['entorno']['python']+' / '+str(report['entorno']['python_bits'])+' bits',
           'Pillow: '+str(report['entorno']['pillow'])+' / libtiff: '+str(report['entorno']['libtiff']),
           'SQLite: '+report['entorno']['sqlite'],
           'SHA-256 lógico: '+str(report['resumen_base']['sha256_logico'])]
    lines.extend(name+': '+str(row['filas'])+' filas' for name,row in report['resumen_base']['tablas'].items())
    lines.extend(name+': '+str(value) for name,value in report['tiff'].items())
    lines.extend(canonical(issue) for issue in report['problemas'])
    (destination/'LEER_DIAGNOSTICO.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return destination
