"""Respaldo verificable de SQLite + documentos. Restaurar siempre a una raíz nueva."""
import hashlib
import json
import shutil
import sqlite3
import uuid
from pathlib import Path
from .workspace import Workspace
from .manifests import checked_files, plain_path, sqlite_sidecar
from .portability import active_relative, normalize_operations


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            result.update(part)
    return result.hexdigest()


def check_database(path):
    db = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    try:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('La base no supera integrity_check.')
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('La base tiene relaciones inconsistentes.')
    finally:
        db.close()


def snapshot(connection, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Reservar sin sobrescribir un respaldo anterior.
    with target.open('xb'):
        pass
    out = sqlite3.connect(str(target))
    try:
        connection.backup(out)
        # La copia no depende de archivos WAL/SHM efímeros del equipo de origen.
        out.execute('PRAGMA journal_mode=DELETE')
    finally:
        out.close()
    check_database(target)


def inventory_files(database, workspace, normalize=False, historical_roots=(), changes=None):
    """Validar cada referencia; normalizar SOLO rutas de la copia exportada."""
    uri = Path(database).resolve().as_uri() + ('?mode=rw' if normalize else '?mode=ro')
    db = sqlite3.connect(uri, uri=True)
    references = set()
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, fields in (
            ('archivos_tiff', (('ruta','hash_actual'), ('original','hash_original'))),
            ('revisiones_tiff', (('ruta','hash'),)),
            ('versiones_archivo', (('ruta','sha256'),))):
            if table not in tables: continue
            for field, hashfield in fields:
                for ident, name, expected in db.execute('SELECT id,'+field+','+hashfield+' FROM '+table).fetchall():
                    relative = active_relative(workspace,name)
                    path = plain_path(workspace.root,relative)
                    references.add(relative)
                    if not path.is_file() or sha256(path) != expected:
                        raise ValueError('Referencia TIFF faltante o alterada: '+table+' ID '+str(ident)+' / '+field)
                    if normalize:
                        if name!=relative:
                            db.execute('UPDATE '+table+' SET '+field+'=? WHERE id=?', (relative, ident))
                            if changes is not None:changes.append({'tabla':table,'id':ident,'campo':field,'antes':name,'despues':relative})
        if normalize and 'operaciones_tiff' in tables:
            normalize_operations(db,workspace,historical_roots,changes)
        if 'entregas' in tables:
            from .delivery import content_hash
            for ident,name,state,expected,stored in db.execute('SELECT id,ruta,estado,manifest_hash,manifest FROM entregas').fetchall():
                relative=active_relative(workspace,name);folder=plain_path(workspace.root,relative)
                if normalize and name!=relative:
                    db.execute('UPDATE entregas SET ruta=? WHERE id=?',(relative,ident))
                    if changes is not None:changes.append({'tabla':'entregas','id':ident,'campo':'ruta','antes':name,'despues':relative})
                if state in ('Preparando','Incompleta'):continue
                if (folder/'INCOMPLETA.txt').exists():raise ValueError('Entrega publicada con marca incompleta: '+ident)
                manifest=json.loads(plain_path(folder,'manifest.json').read_text(encoding='utf-8'))
                if content_hash(manifest)!=expected or manifest!=json.loads(stored):raise ValueError('Manifest de entrega alterado: '+ident)
                references.add(workspace.relative(folder/'manifest.json'))
                entries=checked_files({i['ruta']:i['sha256'] for i in manifest['items']},lambda n:n.startswith(('PERSONALES/','FEDERAL/')))
                if {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} != set(entries)|{'manifest.json'}:
                    raise ValueError('Residuos o archivos faltantes en entrega: '+ident)
                for name,expected in entries.items():
                    path=plain_path(folder,name);references.add(workspace.relative(path))
                    if not path.is_file() or sha256(path)!=expected:raise ValueError('Archivo de entrega faltante/alterado: '+name)
        db.commit()
    finally:
        db.close()
    return references


def create_backup(store, destination=None, historical_roots=(), changes=None, exclude=None):
    from .core import now
    target = Path(destination) if destination else store.workspace.backups / ('completo_' + uuid.uuid4().hex)
    target = target.resolve()
    # No permitir copiar el respaldo dentro del árbol que se está copiando.
    for name in ('datos', 'reportes'):
        source = store.workspace.path(name)
        if target == source or source in target.parents:
            raise ValueError('El respaldo no puede quedar dentro de datos ni reportes.')
    target.mkdir(parents=True, exist_ok=False)
    try:
        database = target / 'datos' / 'digitalizacion.sqlite3'
        snapshot(store.db, database)
        inventory_files(database, store.workspace, normalize=True,historical_roots=historical_roots,changes=changes)
        marker = store.workspace.path('DEMO.json')
        if marker.is_file():
            shutil.copy2(str(marker), str(target / 'DEMO.json'))
        for name in ('datos', 'reportes'):
            source = plain_path(store.workspace.root, name)
            if not source.exists():
                continue
            for path in source.rglob('*'):
                if exclude and exclude(path.relative_to(store.workspace.root).as_posix()):continue
                # Exclusión léxica ANTES de resolver/stat: Windows puede bloquear
                # -shm/-wal abiertos. La base consistente ya procede de backup().
                if path == store.path or path.suffix in ('.sqlite3', '.sqlite', '.db') or sqlite_sidecar(path.name):
                    continue
                # Mantener las validaciones de enlaces/junctions para lo incluido.
                path = plain_path(store.workspace.root, path.relative_to(store.workspace.root).as_posix())
                if not path.is_file():
                    continue
                rel = path.relative_to(store.workspace.root)
                out = target / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(path), str(out))
                if sha256(path) != sha256(out):
                    raise ValueError('Un archivo cambió durante el respaldo: ' + str(rel))
        files = {p.relative_to(target).as_posix(): sha256(p) for p in target.rglob('*') if p.is_file()}
        manifest = {'format': 1, 'created': now(), 'database': 'datos/digitalizacion.sqlite3', 'files': files}
        (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        verify_backup(target)
        return target
    except BaseException:
        # Conservar evidencia; ausencia de manifest válido impide restaurar como respaldo completo.
        (target / 'INCOMPLETO.txt').write_text('El respaldo falló. No usar para restaurar. Repetir en otra carpeta.', encoding='utf-8')
        raise


def verify_backup(source):
    source = Path(source).resolve()
    if (source / 'INCOMPLETO.txt').exists():
        raise ValueError('Respaldo incompleto.')
    manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
    if not isinstance(manifest,dict) or manifest.get('format') != 1 or manifest.get('database') != 'datos/digitalizacion.sqlite3':
        raise ValueError('Formato de respaldo desconocido.')
    ws = Workspace(source)
    files = checked_files(manifest.get('files'), lambda name: name == 'DEMO.json' or name.startswith(('datos/', 'reportes/')))
    for name, expected in files.items():
        path = plain_path(source, name)
        if not path.is_file() or sha256(path) != expected:
            raise ValueError('Archivo faltante o alterado en el respaldo: ' + name)
    if manifest['database'] not in manifest['files']:
        raise ValueError('Falta la base de datos en el manifiesto.')
    check_database(ws.database)
    if not inventory_files(ws.database, ws).issubset(files):
        raise ValueError('El manifiesto omite documentos referenciados por la base.')
    return manifest


def restore_backup(source, destination):
    source = Path(source).resolve()
    manifest = verify_backup(source)
    ws = Workspace(destination)
    # mkdir exclusivo: nunca restaurar sobre una operación activa o sobre otra copia.
    ws.root.mkdir(parents=True, exist_ok=False)
    incomplete = ws.root / '.restauracion_incompleta'
    incomplete.write_text('No abrir: restauración sin completar. Repetir en una carpeta nueva.', encoding='utf-8')
    for name in manifest['files']:
        out = plain_path(ws.root, name)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(plain_path(source, name)), str(out))
        if sha256(out) != manifest['files'][name]:
            raise ValueError('Falló la verificación al restaurar: ' + name)
    check_database(ws.database)
    inventory_files(ws.database, ws)
    incomplete.unlink()
    return ws.root


def backup_existing(workspace, destination):
    """Abrir solo para leer: respaldar ANTES de migrar una instalación antigua."""
    from types import SimpleNamespace
    from .workspace import WorkspaceLock
    if not workspace.database.is_file():
        raise ValueError('No existe la base que se quiere respaldar.')
    lock = WorkspaceLock(workspace.root)
    try:
        db = sqlite3.connect(workspace.database.as_uri() + '?mode=ro', uri=True)
        try:
            return create_backup(SimpleNamespace(db=db, workspace=workspace, path=workspace.database), destination)
        finally:
            db.close()
    finally:
        lock.close()
