"""Prepara una copia validada y reutiliza el actualizador existente para promover."""
import json
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

from app.backup import create_backup, restore_backup, snapshot, sha256, check_database
from app.manifests import plain_path
from app.update_recovery import data_fingerprint, database_fingerprint, write_json
from app.workspace import Workspace, WorkspaceLock
from actualizar import inspect_release, apply_update


def validate_copy(root):
    from app.core import Store
    from app.migrations import CORE_VERSION, CODING_VERSION
    from app.coding import page_info
    from app.dashboard import Dashboard
    ws = Workspace(root)
    before = data_fingerprint(ws)
    # La primera transición no es un instalador de nuevas migraciones. Comprobar
    # en modo lectura antes de que Store pueda actualizar una copia antigua.
    connection = sqlite3.connect(ws.database.as_uri() + '?mode=ro', uri=True)
    try:
        versions = {k: connection.execute('SELECT value FROM meta WHERE key=?', (k,)).fetchone()[0]
                    for k in ('schema_version', 'coding_schema_version')}
    finally:
        connection.close()
    expected = {'schema_version': str(CORE_VERSION), 'coding_schema_version': str(CODING_VERSION)}
    if versions != expected:
        raise ValueError('La copia requiere una migración específica antes de la transición; no fue modificada.')
    store = Store(workspace=root, operador='Validación técnica de copia')
    try:
        Dashboard(store).snapshot(store.works())
        files = pages = 0
        for folder in ('datos', 'reportes'):
            for path in (ws.root / folder).rglob('*'):
                if path.suffix.lower() not in ('.tif', '.tiff'): continue
                safe = plain_path(ws.root, path.relative_to(ws.root).as_posix())
                pages += len(page_info(safe, True)); files += 1
    finally:
        store.db.close()
    check_database(ws.database)
    after = data_fingerprint(ws)
    if before != after:
        raise ValueError('La apertura con el nuevo motor cambió la copia. Se conserva para revisión; no activar.')
    return {'schema': versions, 'tiff_decoded': files, 'pages_decoded': pages, 'unchanged': True, 'fingerprint': after}


def prepare(source, destination, recovery):
    source, destination, recovery = (Path(p).resolve() for p in (source, destination, recovery))
    if destination == recovery or destination in recovery.parents or recovery in destination.parents:
        raise ValueError('El resguardo debe estar fuera de la instalación.')
    release = inspect_release(source, destination)
    ws = Workspace(destination)
    lock = WorkspaceLock(destination)
    try:
        recovery.mkdir(parents=True, exist_ok=False)
        before = data_fingerprint(ws)
        db = sqlite3.connect(ws.database.as_uri() + '?mode=ro', uri=True)
        try:
            snapshot(db, recovery / 'origen-exacto.sqlite3')
            create_backup(SimpleNamespace(db=db, path=ws.database, workspace=ws), recovery / 'respaldo')
        finally: db.close()
        original = sqlite3.connect((recovery / 'origen-exacto.sqlite3').as_uri() + '?mode=ro', uri=True)
        try:
            if database_fingerprint(original) != before['database']:
                raise ValueError('La instantánea original no conserva el estado lógico completo.')
        finally: original.close()
        restored = restore_backup(recovery / 'respaldo', recovery / 'copia-validada')
        result = validate_copy(restored)
        if data_fingerprint(ws) != before:
            raise ValueError('La fuente cambió durante el ensayo. Detén todas las escrituras y prepara otro resguardo.')
        plan = {'format': 'transicion-web-1', 'state': 'Copia validada', 'destination': str(destination),
                'source': str(source), 'release_sha256': sha256(source / 'release-manifest.json'),
                'version': release['version'], 'data_before': before, 'copy_validation': result,
                'original_sha256': sha256(recovery / 'origen-exacto.sqlite3'), 'python': sys.executable}
        write_json(recovery / 'transicion.json', plan)
        return plan
    finally: lock.close()


def activate(recovery):
    recovery = Path(recovery).resolve()
    plan = json.loads(plain_path(recovery, 'transicion.json').read_text(encoding='utf-8'))
    if plan.get('format') != 'transicion-web-1' or plan.get('state') != 'Copia validada':
        raise ValueError('No hay una copia validada pendiente de activar.')
    source, destination = Path(plan['source']).resolve(), Path(plan['destination']).resolve()
    if sha256(source / 'release-manifest.json') != plan['release_sha256']:
        raise ValueError('El paquete cambió después de validar la copia.')
    inspect_release(source, destination)
    if data_fingerprint(Workspace(recovery / 'copia-validada')) != plan['copy_validation']['fingerprint']:
        raise ValueError('La copia validada fue modificada. Repite la preparación en otro resguardo.')
    if sha256(recovery / 'origen-exacto.sqlite3') != plan['original_sha256']:
        raise ValueError('La base original de resguardo fue alterada.')
    if (destination / '.web').exists() or (destination / 'python_web_ruta.txt').exists():
        raise ValueError('Ya existe configuración web. Requiere actualización específica, no primera transición.')
    # El actualizador coteja expected_data DESPUÉS de adquirir su propio bloqueo.
    saved = apply_update(source, destination, expected_data=plan['data_before'])
    private = destination / '.web'
    private.mkdir()
    (destination / 'python_web_ruta.txt').write_text(plan['python'] + '\n', encoding='utf-8')
    release = json.loads((source / 'release-manifest.json').read_text(encoding='utf-8'))
    write_json(private / 'activacion.json', {'format': 'web-local-1', 'workspace': str(destination),
        'version': release['version'], 'files': release['files'], 'resguardo': str(recovery)})
    plan.update(state='Activada; cuenta inicial pendiente', updater_recovery=str(saved))
    write_json(recovery / 'transicion.json', plan)
    return plan
