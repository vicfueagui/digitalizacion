"""Recuperar exclusivamente código cuando no hubo captura posterior al resguardo."""
import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from .backup import sha256
from .manifests import checked_files, plain_path, sqlite_sidecar
from .release import allowed
from .workspace import Workspace, WorkspaceLock


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name('.' + path.name + '_' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.flush(); os.fsync(out.fileno())
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists(): temporary.unlink()


def database_fingerprint(db):
    """Incluye esquema y filas confirmadas, también si permanecen en WAL."""
    result = hashlib.sha256()
    own_transaction = not db.in_transaction
    if own_transaction: db.execute('BEGIN')
    try:
        for line in db.iterdump():
            result.update(line.encode('utf-8')); result.update(b'\n')
    finally:
        if own_transaction: db.rollback()
    return result.hexdigest()


def data_fingerprint(workspace):
    db = sqlite3.connect(workspace.database.as_uri() + '?mode=ro', uri=True)
    try: database = database_fingerprint(db)
    finally: db.close()
    files = {}
    for folder in ('datos', 'reportes'):
        source = plain_path(workspace.root, folder)
        if not source.exists(): continue
        for path in source.rglob('*'):
            if path == workspace.database or sqlite_sidecar(path.name):
                continue
            name = path.relative_to(workspace.root).as_posix()
            path = plain_path(workspace.root, name)
            if not path.is_file(): continue
            files[name] = sha256(path)
    return {'database': database, 'files': files}


def inspect_recovery(recovery, destination):
    recovery = Path(recovery).resolve(); destination = Path(destination).resolve()
    journal = json.loads(plain_path(recovery, 'actualizacion.json').read_text(encoding='utf-8'))
    if not isinstance(journal, dict) or journal.get('recovery_format') != 1:
        raise ValueError('Resguardo anterior sin huella de datos. Restaura en una carpeta nueva según docs/RESPALDOS.md.')
    if Path(journal.get('destination', '')).resolve() != destination:
        raise ValueError('El resguardo pertenece a otra carpeta. No se cambió código ni datos.')
    files = checked_files(journal.get('new'), allowed)
    previous = journal.get('previous')
    if not isinstance(previous, dict) or not set(previous).issubset(files):
        raise ValueError('La lista de código anterior no es válida.')
    if previous: checked_files(previous, allowed)
    if data_fingerprint(Workspace(destination)) != journal.get('data_before'):
        raise ValueError('Los datos cambiaron después del resguardo. No se puede volver al código anterior; conserva ambos estados para revisión.')
    marker = plain_path(destination, '.actualizacion_pendiente.json')
    if marker.exists():
        data = json.loads(marker.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or Path(data.get('resguardo', '')).resolve() != recovery:
            raise ValueError('Hay otra actualización pendiente. No se modificó el destino.')
    for name, new_hash in files.items():
        target = plain_path(destination, name)
        old_hash = previous.get(name)
        if old_hash:
            saved = plain_path(plain_path(recovery, 'codigo_antes'), name)
            if not saved.is_file() or sha256(saved) != old_hash:
                raise ValueError('El código anterior está incompleto o alterado: ' + name)
        if target.exists():
            if not target.is_file() or sha256(target) not in (old_hash, new_hash):
                raise ValueError('Archivo de código modificado después del resguardo: ' + name)
        elif old_hash:
            raise ValueError('Falta código que existía antes de actualizar: ' + name)
    return journal


def restore_code(recovery, destination, locked=False):
    recovery = Path(recovery).resolve(); destination = Path(destination).resolve()
    if not destination.is_dir(): raise ValueError('No existe la carpeta que se quiere recuperar.')
    lock = None if locked else WorkspaceLock(destination)
    try:
        journal = inspect_recovery(recovery, destination)
        staging = recovery / ('codigo_restituir_' + uuid.uuid4().hex)
        staging.mkdir()
        # Verificar toda la copia de retorno antes de tocar el destino.
        for name, expected in journal['previous'].items():
            out = staging / name; out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(plain_path(plain_path(recovery, 'codigo_antes'), name)), str(out))
            if sha256(out) != expected: raise ValueError('Falló la preparación de ' + name)
        pending = plain_path(destination, '.actualizacion_pendiente.json')
        inspect_recovery(recovery, destination)
        write_json(pending, {'resguardo': str(recovery), 'operacion': 'recuperar código'})
        for name in journal['new']:
            target = plain_path(destination, name)
            if name in journal['previous']:
                os.replace(str(staging / name), str(target))
            elif target.exists():
                # El hash fue comprobado antes: es un archivo añadido por esta actualización.
                target.unlink()
        for name, expected in journal['previous'].items():
            if sha256(plain_path(destination, name)) != expected:
                raise ValueError('Falló la verificación de retorno: ' + name)
        journal['state'] = 'Código anterior restaurado; datos conservados'
        write_json(plain_path(recovery, 'actualizacion.json'), journal)
        pending.unlink()
        return recovery
    finally:
        if lock: lock.close()
