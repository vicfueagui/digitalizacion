"""Respaldo privado de negocio y acceso web; compatible con el respaldo legado."""
import json
import platform
import shutil
import sqlite3
from pathlib import Path
from importlib.metadata import version

from app.backup import (create_backup, verify_backup, restore_backup, snapshot,
                        check_database, sha256)
from app.manifests import checked_files, plain_path

PRIVATE = {'config.json', 'acceso.sqlite3', 'solicitudes.sqlite3', 'origen.sqlite3'}


def provenance():
    from app import VERSION
    code = Path(__file__).resolve().parent.parent
    files = [code / 'iniciar_web.py', code / 'requirements-modern.txt']
    for folder in ('app', 'webapp'):
        files.extend(p for p in (code / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix in {'.py', '.sql', '.html', '.css', '.js', '.json', '.txt'})
    return {'app': VERSION, 'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
            'packages': {name: version(name) for name in ('Django', 'Pillow', 'waitress', 'whitenoise')},
            'code': {p.relative_to(code).as_posix(): sha256(p) for p in sorted(files)}}


def create_web_backup(store, destination):
    """Llamar en el hilo serial de negocio, después de confirmar escrituras previas."""
    target = Path(destination).resolve()
    for name in ('datos', 'reportes', '.web'):
        forbidden = store.workspace.root / name
        if target == forbidden or forbidden in target.parents:
            raise ValueError('El respaldo requiere una carpeta nueva fuera de datos, reportes y acceso web.')
    target.mkdir(parents=True, exist_ok=False)
    incomplete = target / 'INCOMPLETO.txt'
    incomplete.write_text('No restaurar: respaldo web sin completar.', encoding='utf-8')
    business = create_backup(store, target / 'expediente')
    private = target / 'privado'
    private.mkdir()
    # Preservar la procedencia exacta antes de normalizar rutas en la copia portable.
    snapshot(store.db, private / 'origen.sqlite3')
    source_config = plain_path(store.workspace.root, '.web/config.json')
    shutil.copy2(str(source_config), str(private / 'config.json'))
    for name in ('acceso.sqlite3', 'solicitudes.sqlite3'):
        source = plain_path(store.workspace.root, '.web/' + name)
        db = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)
        try:
            snapshot(db, private / name)
        finally:
            db.close()
    manifest = {'format': 'digitalizacion-web-1', 'business': 'expediente',
                'created': verify_backup(business)['created'], 'runtime': provenance(),
                'private': {name: sha256(private / name) for name in sorted(PRIVATE)},
                'business_manifest_sha256': sha256(business / 'manifest.json')}
    (target / 'manifest-web.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    # Verificar también antes de retirar la marca de incompleto.
    _verify(target, allow_incomplete=True)
    incomplete.unlink()
    return target


def _verify(source, allow_incomplete=False):
    source = Path(source).resolve()
    if (source / 'INCOMPLETO.txt').exists() and not allow_incomplete:
        raise ValueError('Respaldo web incompleto.')
    manifest = json.loads(plain_path(source, 'manifest-web.json').read_text(encoding='utf-8'))
    if manifest.get('format') != 'digitalizacion-web-1' or manifest.get('business') != 'expediente':
        raise ValueError('Formato web desconocido.')
    files = checked_files(manifest.get('private'), lambda name: name in PRIVATE)
    if set(files) != PRIVATE:
        raise ValueError('Faltan componentes de acceso o procedencia.')
    business = plain_path(source, 'expediente')
    if sha256(plain_path(business, 'manifest.json')) != manifest.get('business_manifest_sha256'):
        raise ValueError('Manifiesto de negocio alterado.')
    base = verify_backup(business)
    for name, digest in files.items():
        path = plain_path(source, 'privado/' + name)
        if sha256(path) != digest:
            raise ValueError('Componente privado alterado: ' + name)
        if name.endswith('.sqlite3'):
            check_database(path)
    config = json.loads(plain_path(source, 'privado/config.json').read_text(encoding='utf-8'))
    if not isinstance(config.get('secret_key'), str) or len(config['secret_key']) < 40 or not isinstance(config.get('demo'), bool):
        raise ValueError('Configuración de acceso incompleta.')
    expected = {'manifest-web.json', 'expediente/manifest.json'}
    expected.update('privado/' + name for name in files)
    expected.update('expediente/' + name for name in base['files'])
    if allow_incomplete: expected.add('INCOMPLETO.txt')
    actual = set()
    for path in source.rglob('*'):
        safe = plain_path(source, path.relative_to(source).as_posix())
        if safe.is_file(): actual.add(path.relative_to(source).as_posix())
    if actual != expected:
        raise ValueError('Respaldo con archivos adicionales o faltantes.')
    return manifest


def verify_web_backup(source):
    return _verify(source)


def restore_web_backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    manifest = verify_web_backup(source)
    # restore_backup exige destino inexistente y verifica cada documento.
    restored = restore_backup(source / 'expediente', destination)
    incomplete = restored / '.restauracion_web_incompleta'
    incomplete.write_text('Acceso web pendiente de restaurar; no iniciar.', encoding='utf-8')
    private = restored / '.web'
    private.mkdir()
    for name, digest in manifest['private'].items():
        out = private / name
        shutil.copy2(str(plain_path(source, 'privado/' + name)), str(out))
        if sha256(out) != digest:
            raise ValueError('Copia privada no coincide: ' + name)
    # Las cuentas y claves se conservan. Las sesiones abiertas deben iniciar otra vez.
    db = sqlite3.connect(str(private / 'acceso.sqlite3'))
    try:
        with db: db.execute('DELETE FROM django_session')
    finally:
        db.close()
    (private / 'restauracion.json').write_text(json.dumps({
        'format': manifest['format'], 'created': manifest['created'],
        'sessions_revoked': True, 'runtime': manifest['runtime']}, ensure_ascii=False, indent=2), encoding='utf-8')
    check_database(private / 'acceso.sqlite3')
    incomplete.unlink()
    return restored
