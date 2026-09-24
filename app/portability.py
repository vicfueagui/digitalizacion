"""Rutas activas estrictas e historia portable; nunca sustituye texto global."""
import json
import os
from pathlib import Path, PureWindowsPath
from .manifests import checked_files, plain_path

PATH_FIELDS = ('antes','despues','original','copia','respaldo','source','target','destino','ruta')


def active_relative(workspace, value):
    """Rechaza traversal, escapes y enlaces incluso internos antes de leer."""
    text=str(value).replace('\\','/')
    if '..' in text.split('/'):raise ValueError('La ruta contiene una salida del espacio de trabajo.')
    if PureWindowsPath(text).drive and os.name!='nt':
        raise ValueError('Ruta activa absoluta de Windows fuera del workspace local.')
    path=Path(text)
    if path.is_absolute():
        try:relative=path.relative_to(workspace.root).as_posix()
        except ValueError:raise ValueError('Ruta activa fuera del workspace.')
    else:relative=text
    checked_files({relative:'0'*64}, lambda name:name.startswith(('datos/','reportes/')))
    plain_path(workspace.root, relative)
    return relative


def history_relative(value, roots):
    """No exige que un nombre histórico aún exista. No remapea raíces desconocidas."""
    if not isinstance(value,str):return value
    text=value.replace('\\','/')
    if '..' in text.split('/'):
        raise ValueError('Traversal en una ruta de operación TIFF; requiere revisión.')
    absolute = text.startswith('/') or bool(PureWindowsPath(value).drive)
    if not absolute:
        if text.startswith(('datos/','reportes/')):
            checked_files({text:'0'*64},lambda name:True)
            return text
        return value
    for root in roots:
        prefix=str(root).replace('\\','/').rstrip('/')+'/'
        windows=bool(PureWindowsPath(str(root)).drive)
        match=text.casefold().startswith(prefix.casefold()) if windows else text.startswith(prefix)
        if match:
            relative=text[len(prefix):]
            if not relative.startswith(('datos/','reportes/')):return value
            checked_files({relative:'0'*64},lambda name:name.startswith(('datos/','reportes/')))
            return relative
    return value  # Evidencia externa/histórica; nunca se resuelve ni se copia.


def evidenced_history_roots(db, workspace, candidates):
    """Un prefijo declarado solo se acepta si una referencia y su hash lo corroboran."""
    from .backup import sha256
    roots=[str(workspace.root)]
    if not candidates:return roots
    references={}
    for table, fields in (('archivos_tiff',(('ruta','hash_actual'),('original','hash_original'))),
                          ('revisiones_tiff',(('ruta','hash'),)),('versiones_archivo',(('ruta','sha256'),))):
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():continue
        for field,digest in fields:
            for path,expected in db.execute('SELECT '+field+','+digest+' FROM '+table):
                relative=active_relative(workspace,path)
                references[relative]=expected
    details=[]
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='operaciones_tiff'").fetchone():
        for row in db.execute('SELECT detalle FROM operaciones_tiff'):
            obj=json.loads(row[0]);details.extend(obj.get(key) for key in PATH_FIELDS if isinstance(obj.get(key),str))
    for candidate in candidates:
        text=str(candidate).replace('\\','/').rstrip('/')
        if not text or '..' in text.split('/') or not (text.startswith('/') or PureWindowsPath(text).is_absolute()):
            raise ValueError('Raíz histórica inválida; se requiere una ruta absoluta completa.')
        matched=False
        for value in details:
            relative=history_relative(value,[text])
            if relative!=value and relative in references:
                if sha256(plain_path(workspace.root,relative))==references[relative]:matched=True;break
        if not matched:raise ValueError('La raíz histórica indicada no tiene correspondencia inequívoca con una referencia verificada.')
        roots.append(text)
    return roots


def normalize_operations(db, workspace, historical_roots=(), changes=None):
    """Solo sobre un snapshot writable. Diario pendiente exige rutas actuales válidas."""
    roots=evidenced_history_roots(db,workspace,historical_roots)
    for ident,state,detail in db.execute('SELECT id,estado,detalle FROM operaciones_tiff').fetchall():
        obj=json.loads(detail)
        if not isinstance(obj,dict):raise ValueError('Detalle de operación TIFF inválido.')
        before=detail
        for key in PATH_FIELDS:
            if key in obj and isinstance(obj[key],str):
                obj[key]=(active_relative(workspace,obj[key]) if state=='Preparada'
                          else history_relative(obj[key],roots))
        after=json.dumps(obj,ensure_ascii=False)
        if obj!=json.loads(before):
            db.execute('UPDATE operaciones_tiff SET detalle=? WHERE id=?',(after,ident))
            if changes is not None:changes.append({'tabla':'operaciones_tiff','id':ident,'campo':'detalle','antes':before,'despues':after})
