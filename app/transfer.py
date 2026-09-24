"""Formato de traslado 1: código de origen intacto + copia portable + evidencia.

No abre Store, no migra esquema y no aplica actualizaciones de código al origen.
"""
import datetime
import json
import os
import re
from pathlib import Path,PurePosixPath
import shutil
import sqlite3
import tempfile
from types import SimpleNamespace
import uuid

from .backup import create_backup,verify_backup,restore_backup,sha256,snapshot,check_database
from .integrity import diagnose,read_summary,audit_database,code_version,content_digest
from .manifests import checked_files,plain_path,walk_plain,sqlite_sidecar
from .portability import active_relative
from .release import allowed
from .runtime import validate as validate_runtime
from .update_recovery import database_fingerprint,write_json
from .workspace import Workspace,WorkspaceLock,CODE_ROOT

MANIFEST='migracion-manifest.json'
CHECKSUM='migracion-manifest.sha256'
FORMAT=1


def publish_folder(staging,destination):
    """Reserva exclusiva; la retirada de INCOMPLETO publica el conjunto verificado.

    No usar rename(carpeta,destino): POSIX reemplaza un destino vacío ajeno.
    Una interrupción conserva una marca que todos los lectores rechazan.
    """
    destination.mkdir(exist_ok=False)
    marker=destination/'INCOMPLETO.txt'
    marker.write_text('Publicación en curso. No utilizar.',encoding='utf-8')
    for item in staging.iterdir():
        if item.name=='INCOMPLETO.txt':continue
        os.rename(str(item),str(destination/item.name))
    marker.unlink()
    shutil.rmtree(str(staging))


def ignored(name):
    path=PurePosixPath(name)
    return ('__pycache__' in path.parts or path.name in ('.DS_Store','Thumbs.db','desktop.ini') or
            path.suffix in ('.pyc','.pyo') or
            (path.name.startswith(('.edit_','.recover_','.restore_')) and path.suffix=='.tmp'))


def disjoint(destination,*roots):
    destination=Path(destination).resolve()
    for root in roots:
        root=Path(root).resolve()
        if destination==root or destination in root.parents or root in destination.parents:
            raise ValueError('Elige un destino nuevo e independiente del origen, paquete y herramientas.')
    return destination


def code_allowed(name):
    path=PurePosixPath(name)
    # Capturar también pequeños resolutores/correcciones locales del origen.
    return allowed(name) or (len(path.parts)==1 and not path.name.startswith('.') and path.suffix in ('.py','.bat','.ps1'))


def code_files(root):
    root=Path(root).resolve();files={}
    for p in root.iterdir():
        if code_allowed(p.name) and p.is_file():files[p.name]=sha256(plain_path(root,p.name))
    for folder in ('app','tests','tools','docs','instaladores'):
        base=root/folder
        if not base.exists():continue
        plain_path(root,folder)
        for p in base.iterdir():
            name=p.relative_to(root).as_posix()
            if code_allowed(name) and p.is_file():files[name]=sha256(plain_path(root,name))
    checked_files(files,code_allowed)
    required={'main.py','app/core.py','app/__init__.py','app/workspace.py','app/migrations.py','app/schema.sql',
              'tools/run_tests.py','tools/ensayo_oficina.py','tools/smoke_ui.py'}
    if not required<=set(files):raise ValueError('El programa de origen está incompleto: faltan código o pruebas de aceptación.')
    return files


def copy_files(source,target,files):
    for name,expected in files.items():
        src=plain_path(source,name);out=plain_path(target,name)
        out.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as inp,out.open('xb') as stream:shutil.copyfileobj(inp,stream,1024*1024)
        if sha256(out)!=expected or sha256(src)!=expected:raise ValueError('Un archivo cambió durante la copia verificada.')


def payload_files(workspace):
    result={}
    for folder in ('datos','reportes'):
        source=plain_path(workspace.root,folder)
        if not source.exists():continue
        for path in source.rglob('*'):
            name=path.relative_to(workspace.root).as_posix()
            if path==workspace.database or sqlite_sidecar(path.name) or ignored(name):continue
            path=plain_path(workspace.root,name)
            if not path.is_file():continue
            if path.suffix.lower() in ('.sqlite3','.sqlite','.db'):
                raise ValueError('Hay otra base dentro de datos/reportes. Debe clasificarse antes de trasladar; no se omite ni se copia abierta.')
            result[name]=sha256(path)
    checked_files(result,lambda name:name.startswith(('datos/','reportes/'))) if result else None
    return result


def source_state(workspace):
    db=sqlite3.connect(workspace.database.as_uri()+'?mode=ro',uri=True)
    try:fingerprint=database_fingerprint(db)
    finally:db.close()
    return {'base_logica':fingerprint,'archivos':payload_files(workspace)}


def normalization_proof(portable,changes,original_summary):
    """Invertir exclusivamente las sustituciones declaradas en otra copia temporal.

    Toda tabla/columna/fila restante debe resultar idéntica a origen, no solo contar igual.
    """
    permitted={'archivos_tiff':{'ruta','original'},'revisiones_tiff':{'ruta'},
               'versiones_archivo':{'ruta'},'entregas':{'ruta'},'operaciones_tiff':{'detalle'}}
    with tempfile.TemporaryDirectory(prefix='digitalizacion-equivalencia-') as temp:
        target=Path(temp)/'prueba.sqlite3'
        source=sqlite3.connect(Path(portable).as_uri()+'?mode=ro',uri=True)
        try:snapshot(source,target)
        finally:source.close()
        db=sqlite3.connect(str(target))
        try:
            with db:
                for change in reversed(changes):
                    table=change['tabla'];field=change['campo']
                    if table not in permitted or field not in permitted[table]:raise ValueError('Normalización no permitida.')
                    current=db.execute('SELECT '+field+' FROM '+table+' WHERE id=?',(change['id'],)).fetchone()
                    if current is None or current[0]!=change['despues']:raise ValueError('La evidencia de normalización no coincide con la copia.')
                    db.execute('UPDATE '+table+' SET '+field+'=? WHERE id=?',(change['antes'],change['id']))
        finally:db.close()
        if read_summary(target)!=original_summary:raise ValueError('La copia portable no conserva todas las filas, tablas y relaciones del origen.')


def package_allowed(name):
    if name in ('informes/origen.json','informes/normalizacion.json','informes/portable.json','LEEME.txt'):return True
    for prefix in ('programa/','herramientas/'):
        if name.startswith(prefix):return code_allowed(name[len(prefix):])
    if name.startswith('respaldo/'):
        return name=='respaldo/manifest.json' or name=='respaldo/DEMO.json' or name.startswith(('respaldo/datos/','respaldo/reportes/'))
    return False


def tree_files(root):
    files={}
    for path in walk_plain(root):
        relative=path.relative_to(root).as_posix()
        path=plain_path(root,relative)  # Estricto: ni siquiera enlaces internos.
        if path.is_file():files[relative]=sha256(path)
    return files


def export_migration(workspace,code_root,destination,tool_root=CODE_ROOT,historical_roots=(),laboratory=False):
    code_root=Path(code_root).resolve();tool_root=Path(tool_root).resolve()
    destination=disjoint(destination,workspace.root,code_root,tool_root)
    if destination.exists():raise FileExistsError('Ese paquete ya existe. Verifícalo o elige otro nombre.')
    if not workspace.database.is_file():raise ValueError('No existe el workspace de origen.')
    if laboratory and not (workspace.root/'DEMO.json').is_file():raise ValueError('El modo laboratorio exige una demo explícita, nunca datos reales.')
    lock=WorkspaceLock(workspace.root);staging=None
    try:
        report=diagnose(workspace,code_root,locked=True)
        if not report['correcto']:raise ValueError('La integridad de origen tiene problemas. Ejecuta Auditar y conserva el informe; no se exportó producción.')
        validate_runtime(report['entorno'],'laboratorio' if laboratory else 'legado')
        if not laboratory and report['entorno']['sistema']!='Windows':raise ValueError('La exportación real se prepara en Windows con el runtime conservador.')
        with sqlite3.connect(workspace.database.as_uri()+'?mode=ro',uri=True) as db:
            versions=dict(db.execute("SELECT key,value FROM meta WHERE key IN ('schema_version','coding_schema_version')"))
        if versions!={'schema_version':'7','coding_schema_version':'3'}:raise ValueError('La migración inicial requiere núcleo 7/TIFF 3. Actualizar esquema es una operación distinta.')
        before=source_state(workspace);program=code_files(code_root);toolkit=code_files(tool_root)
        required=sum((workspace.root/n).stat().st_size for n in before['archivos'])+workspace.database.stat().st_size
        parent=destination.parent
        if not parent.is_dir():raise ValueError('Crea primero la carpeta contenedora del paquete.')
        if shutil.disk_usage(parent).free<required*2+64*1024*1024:raise ValueError('No hay espacio suficiente para preparar y verificar el paquete.')
        staging=parent/('.'+destination.name+'.incompleta-'+uuid.uuid4().hex)
        staging.mkdir();(staging/'INCOMPLETO.txt').write_text('No utilizar. Exportación en curso.',encoding='utf-8')
        changes=[];db=sqlite3.connect(workspace.database.as_uri()+'?mode=ro',uri=True)
        try:create_backup(SimpleNamespace(db=db,path=workspace.database,workspace=workspace),staging/'respaldo',historical_roots,changes,exclude=ignored)
        finally:db.close()
        portable=read_summary(staging/'respaldo/datos/digitalizacion.sqlite3')
        normalization_proof(staging/'respaldo/datos/digitalizacion.sqlite3',changes,report['resumen_base'])
        copy_files(code_root,staging/'programa',program);copy_files(tool_root,staging/'herramientas',toolkit)
        (staging/'informes').mkdir()
        write_json(staging/'informes/origen.json',report);write_json(staging/'informes/portable.json',portable)
        write_json(staging/'informes/normalizacion.json',changes)
        (staging/'LEEME.txt').write_text('PAQUETE DE MIGRACIÓN\nConserva esta carpeta completa y la huella del manifiesto por separado.\n'
            'En Windows 10 prepara Python 3.8.10 x64 y Pillow 9.5.0.\n'
            'Extrae el kit 0.6.3 verificado en otra carpeta; abre su MIGRAR.bat y elige Restaurar migración.\n'
            'No instales .venv ni guardes configuración dentro de este paquete sellado.\n'
            'Guía: herramientas/MIGRACION_WINDOWS10.html. No copies .venv ni abras programa/main.py antes de verificar.\n'
            'El código de programa/ es el capturado en origen; herramientas/ es el kit de traslado.\n',encoding='utf-8')
        if source_state(workspace)!=before or code_files(code_root)!=program:
            raise ValueError('El origen cambió durante la exportación. Cierra todas las herramientas y repite.')
        (staging/'INCOMPLETO.txt').unlink()
        files=tree_files(staging);checked_files(files,package_allowed)
        manifest={'formato':FORMAT,'id':uuid.uuid4().hex,'fecha':report['fecha'],'solo_laboratorio':laboratory,
                  'version_aplicacion':report['version_aplicacion'],'esquemas':versions,'origen':before,
                  'programa':program,'herramientas':toolkit,'archivos':files,'base_portable':portable,'entorno_origen':report['entorno']}
        write_json(staging/MANIFEST,manifest)
        (staging/CHECKSUM).write_text(sha256(staging/MANIFEST)+'  '+MANIFEST+'\n',encoding='ascii')
        verify_package(staging)
        if destination.exists():raise FileExistsError('El destino apareció durante la exportación; no se reemplazó.')
        if source_state(workspace)!=before:raise ValueError('El origen cambió antes de publicar.')
        publish_folder(staging,destination)
        return {'paquete':str(destination),'id':manifest['id'],'sha256_manifiesto':sha256(destination/MANIFEST),
                'conclusion':'EXPORTACION VERIFICADA','solo_laboratorio':laboratory}
    except BaseException:
        if staging and staging.exists():
            (staging/'INCOMPLETO.txt').write_text('Exportación interrumpida. No importar. Conserva el diagnóstico y repite en otra carpeta.',encoding='utf-8')
        raise
    finally:lock.close()


def verify_package(source,expected=None):
    source=Path(source).resolve()
    if (source/'INCOMPLETO.txt').exists():raise ValueError('Paquete incompleto.')
    actual=sha256(plain_path(source,MANIFEST))
    parts=plain_path(source,CHECKSUM).read_text(encoding='ascii').split()
    if len(parts)!=2 or parts[1]!=MANIFEST or not re.fullmatch('[0-9a-f]{64}',parts[0]):raise ValueError('Archivo de comprobación inválido.')
    checksum=parts[0]
    if expected is not None:
        expected=str(expected).strip().lower()
        if not re.fullmatch('[0-9a-f]{64}',expected):raise ValueError('La huella esperada requiere 64 caracteres SHA-256.')
    if actual!=checksum or (expected and actual!=expected):raise ValueError('El SHA-256 del manifiesto no coincide.')
    manifest=json.loads(plain_path(source,MANIFEST).read_text(encoding='utf-8'))
    if not isinstance(manifest,dict) or manifest.get('formato')!=FORMAT or not isinstance(manifest.get('solo_laboratorio'),bool):raise ValueError('Formato de migración desconocido.')
    files=checked_files(manifest.get('archivos'),package_allowed)
    present=tree_files(source)
    if set(present)!=set(files)|{MANIFEST,CHECKSUM}:raise ValueError('El paquete contiene archivos omitidos o ajenos al manifiesto.')
    for name,digest in files.items():
        if present[name]!=digest:raise ValueError('Archivo alterado/faltante en el paquete: '+name)
    for folder in ('programa','herramientas'):
        members=checked_files(manifest.get(folder),code_allowed)
        if {name[len(folder)+1:]:digest for name,digest in files.items() if name.startswith(folder+'/')}!=members:
            raise ValueError('El manifiesto del código no corresponde a sus archivos.')
        if code_files(source/folder)!=members:raise ValueError('El código no tiene todos los componentes requeridos.')
    if code_version(source/'programa')!=manifest['version_aplicacion']:raise ValueError('La versión del código de origen cambió.')
    verify_backup(source/'respaldo')
    database=source/'respaldo/datos/digitalizacion.sqlite3'
    if read_summary(database)!=manifest['base_portable']:raise ValueError('La base portable no coincide con sus entidades e historia.')
    original=json.loads((source/'informes/origen.json').read_text(encoding='utf-8'))
    if original['huella_logica_origen']!=manifest['origen']['base_logica'] or original['entorno']!=manifest['entorno_origen']:
        raise ValueError('La evidencia de origen no corresponde al manifiesto.')
    if json.loads((source/'informes/portable.json').read_text(encoding='utf-8'))!=manifest['base_portable']:
        raise ValueError('El informe portable no corresponde al manifiesto.')
    changes=json.loads((source/'informes/normalizacion.json').read_text(encoding='utf-8'))
    normalization_proof(database,changes,original['resumen_base'])
    copied={name[len('respaldo/'):]:digest for name,digest in files.items()
            if name.startswith(('respaldo/datos/','respaldo/reportes/')) and name!='respaldo/datos/digitalizacion.sqlite3'}
    if copied!=manifest['origen']['archivos']:raise ValueError('Los archivos del paquete no equivalen a los inventariados en origen.')
    return manifest


def compare_source(source,workspace,expected=None):
    manifest=verify_package(source,expected)
    lock=WorkspaceLock(workspace.root)
    try:
        state=source_state(workspace)
        differences=[]
        if state['base_logica']!=manifest['origen']['base_logica']:differences.append('Cambió la base lógica del origen (incluido WAL confirmado).')
        if state['archivos']!=manifest['origen']['archivos']:differences.append('Cambió el inventario o contenido de archivos del origen.')
        return {'conclusion':'MIGRACION NO VERIFICADA' if differences else 'MIGRACION VERIFICADA',
                'alcance':'Equivalencia entre origen congelado y paquete','diferencias':differences,'solo_laboratorio':manifest['solo_laboratorio']}
    finally:lock.close()


def restore_migration(source,destination,expected=None):
    source=Path(source).resolve();destination=disjoint(destination,source)
    manifest=verify_package(source,expected)  # Antes de crear ni ejecutar en destino.
    if destination.exists():raise FileExistsError('La instalación destino ya existe. Verifícala o utiliza otra carpeta nueva.')
    if not destination.parent.is_dir():raise ValueError('Crea primero la carpeta contenedora del destino.')
    required=sum(plain_path(source,name).stat().st_size for name in manifest['archivos'])
    if shutil.disk_usage(destination.parent).free<required*2+64*1024*1024:
        raise ValueError('No hay espacio suficiente para restaurar y ensayar; libera espacio fuera de los datos.')
    staging=destination.parent/('.'+destination.name+'.restauracion-'+uuid.uuid4().hex)
    staging.mkdir();(staging/'INCOMPLETO.txt').write_text('Restauración en curso.',encoding='utf-8')
    try:
        restore_backup(source/'respaldo',staging/'workspace')
        (staging/'workspace/.restauracion_incompleta').write_text('Migración pendiente de ensayo y activación. Usa el asistente; no borres esta marca.',encoding='utf-8')
        copy_files(source/'programa',staging/'programa',manifest['programa'])
        copy_files(source/'herramientas',staging/'herramientas',manifest['herramientas'])
        evidence=staging/'evidencia';evidence.mkdir()
        copy_files(source,evidence,{MANIFEST:sha256(source/MANIFEST),CHECKSUM:sha256(source/CHECKSUM)})
        state={'formato':FORMAT,'paquete_id':manifest['id'],'manifest_sha256':sha256(source/MANIFEST),
               'estado':'Pendiente de verificación','solo_laboratorio':manifest['solo_laboratorio']}
        write_json(staging/'migracion.json',state)
        launch='@echo off\r\nsetlocal DisableDelayedExpansion\r\ncall "%~dp0herramientas\\EJECUTAR.bat" migracion abrir --instalacion "%~dp0."\r\npause\r\n'
        (staging/'INICIAR_MIGRADO.bat').write_bytes(launch.encode('ascii'))
        result=verify_destination(staging)
        if result['diferencias']:raise ValueError('La restauración no coincide: '+'; '.join(result['diferencias']))
        (staging/'INCOMPLETO.txt').unlink()
        if destination.exists():raise FileExistsError('El destino apareció durante la restauración; no se reemplazó.')
        publish_folder(staging,destination)
        return {'instalacion':str(destination),'estado':'Datos verificados; falta ensayo y activación','solo_laboratorio':manifest['solo_laboratorio']}
    except BaseException:
        if staging.exists():(staging/'INCOMPLETO.txt').write_text('Restauración interrumpida. No abrir. Repetir a otra carpeta.',encoding='utf-8')
        raise


def load_installation(root):
    root=Path(root).resolve()
    state=json.loads(plain_path(root,'migracion.json').read_text(encoding='utf-8'))
    manifest_path=plain_path(root,'evidencia/'+MANIFEST)
    if sha256(manifest_path)!=state.get('manifest_sha256'):raise ValueError('La evidencia del destino fue alterada.')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('id')!=state.get('paquete_id') or manifest.get('formato')!=FORMAT:raise ValueError('La instalación no corresponde al paquete.')
    return root,state,manifest


def verify_destination(root,locked=False):
    if not locked:
        candidate=Path(root).resolve()
        if not (candidate/'workspace/datos/digitalizacion.sqlite3').is_file():raise ValueError('No existe una instalación restaurada en esa carpeta.')
        lock=WorkspaceLock(candidate/'workspace')
        try:return verify_destination(root,locked=True)
        finally:lock.close()
    root,state,manifest=load_installation(root);ws=Workspace(root/'workspace')
    differences=[];summary=None
    try:
        check_database(ws.database)
        summary=read_summary(ws.database)
        if summary!=manifest['base_portable']:
            differences.append('La base, entidades o auditoría difieren de la copia portable.')
            for table in sorted(set(summary['tablas'])|set(manifest['base_portable']['tablas'])):
                actual=summary['tablas'].get(table);expected=manifest['base_portable']['tablas'].get(table)
                if actual!=expected:differences.append('Tabla '+table+': contenido distinto; filas destino/origen '+str(actual['filas'] if actual else None)+'/'+str(expected['filas'] if expected else None)+'.')
        actual_files=payload_files(ws);expected_files=manifest['origen']['archivos']
        if actual_files!=expected_files:
            differences.append('Archivos: {} faltantes, {} adicionales, {} alterados.'.format(
                len(set(expected_files)-set(actual_files)),len(set(actual_files)-set(expected_files)),
                sum(actual_files[n]!=expected_files[n] for n in set(actual_files)&set(expected_files))))
        report=audit_database(ws.database,ws)
        if not report['correcto']:differences.append('Hay referencias, hashes, páginas o relaciones TIFF inválidos.')
        if code_files(root/'programa')!=manifest['programa']:differences.append('El programa no es el código exacto del origen.')
        if code_files(root/'herramientas')!=manifest['herramientas']:differences.append('Las herramientas del destino fueron alteradas.')
    except (ValueError,OSError,sqlite3.Error):differences.append('No se completó la lectura y validación de todos los componentes.')
    return {'conclusion':'MIGRACION NO VERIFICADA' if differences else 'MIGRACION VERIFICADA',
            'alcance':'Datos y código equivalentes; el ensayo y activación se registran por separado',
            'diferencias':differences,'paquete_id':manifest['id'],'solo_laboratorio':manifest['solo_laboratorio'],
            'conteos':{name:row['filas'] for name,row in summary['tablas'].items()} if summary else {}}
