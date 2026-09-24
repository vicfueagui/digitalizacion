"""Ejecutar desde la actualización extraída, con la aplicación de oficina cerrada."""
import argparse
import datetime
import json
import os
import shutil
import sqlite3
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from app import VERSION
from app.backup import create_backup, sha256
from app.migrations import version, CORE_VERSION, CODING_VERSION
from app.release import allowed
from app.workspace import Workspace, WorkspaceLock
from app.manifests import checked_files, plain_path
from app.update_recovery import data_fingerprint, restore_code, write_json


def inspect_release(source, destination):
    source=Path(source).resolve(); destination=Path(destination).resolve()
    if source==destination or source in destination.parents or destination in source.parents:
        raise ValueError('Extrae la actualización en una carpeta independiente del proyecto de oficina.')
    manifest=json.loads((source/'release-manifest.json').read_text(encoding='utf-8'))
    if not isinstance(manifest,dict) or manifest.get('format')!=1 or not manifest.get('files'):
        raise ValueError('Paquete sin manifiesto de código válido.')
    checked_files(manifest.get('files'),allowed)
    required={'main.py','app/core.py','app/schema.sql','app/workspace.py','app/migrations.py'}
    if not required.issubset(manifest['files']):raise ValueError('Paquete incompleto.')
    for name,expected in manifest['files'].items():
        if not allowed(name):raise ValueError('El paquete intenta incluir una ruta no autorizada: '+name)
        src=plain_path(source,name);target=plain_path(destination,name)
        if not src.is_file() or src.is_symlink() or source not in src.resolve().parents or sha256(src)!=expected:
            raise ValueError('Archivo del paquete faltante o alterado: '+name)
        if target.is_symlink() or destination not in target.resolve().parents:
            raise ValueError('Ruta enlazada fuera del proyecto: '+name)
    if not (destination/'main.py').is_file():raise ValueError('El destino no contiene main.py. Selecciona el proyecto existente.')
    if (destination/'.restauracion_incompleta').exists():raise ValueError('El destino tiene una restauración incompleta.')
    if (destination/'.actualizacion_pendiente.json').exists():
        raise ValueError('La actualización anterior se interrumpió. Conserva el resguardo y revisa la recuperación antes de reintentar.')
    ws=Workspace(destination)
    if not ws.database.is_file():raise ValueError('No existe datos/digitalizacion.sqlite3. No adivino una ubicación productiva distinta.')
    db=sqlite3.connect(ws.database.as_uri()+'?mode=ro',uri=True)
    try:
        if version(db,'schema_version')>CORE_VERSION or version(db,'coding_schema_version')>CODING_VERSION:
            raise ValueError('El destino usa un esquema futuro. Actualización rechazada.')
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('La base requiere revisión antes de actualizar.')
    finally:db.close()
    return manifest


def apply_update(source, destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    manifest=inspect_release(source,destination)
    ws=Workspace(destination);lock=WorkspaceLock(destination)
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
    recovery=destination.parent/(destination.name+'_resguardo_'+stamp)
    try:
        recovery.mkdir(exist_ok=False)
        data_before=data_fingerprint(ws)
        db=sqlite3.connect(ws.database.as_uri()+'?mode=ro',uri=True)
        try:create_backup(SimpleNamespace(db=db,path=ws.database,workspace=ws),recovery/'datos_antes')
        finally:db.close()
        old=recovery/'codigo_antes';staged=recovery/'codigo_nuevo'
        for name,expected in manifest['files'].items():
            target=destination/name
            if target.exists():
                out=old/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(str(target),str(out))
            out=staged/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(str(source/name),str(out))
            if sha256(out)!=expected:raise ValueError('Falló la verificación previa de '+name)
        if data_fingerprint(ws)!=data_before:raise ValueError('Los datos cambiaron durante el resguardo. Cierra todas las aplicaciones antes de actualizar.')
        journal={'recovery_format':1,'data_before':data_before,'new':manifest['files'],'version':manifest['version'],'destination':str(destination),'state':'Preparada','files':list(manifest['files']),
                 'previous':{name:sha256(old/name) for name in manifest['files'] if (old/name).is_file()}}
        journal_path=recovery/'actualizacion.json'
        write_json(journal_path,journal)
        pending=destination/'.actualizacion_pendiente.json'
        write_json(pending,{'resguardo':str(recovery)})
        try:
            for name,expected in manifest['files'].items():
                target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
                # staging en el mismo disco; sustituir solamente archivos de la lista de código.
                os.replace(str(staged/name),str(target))
                if sha256(target)!=expected:raise ValueError('Falló la verificación final de '+name)
        except Exception:
            restore_code(recovery,destination,locked=True)
            raise
        if data_fingerprint(ws)!=data_before:
            raise ValueError('Los datos cambiaron durante la actualización. Se conservó la marca pendiente; revisa el resguardo antes de abrir.')
        journal['state']='Código actualizado; esquema pendiente del primer arranque'
        write_json(journal_path,journal)
        pending.unlink()
        return recovery
    finally:lock.close()


def main():
    parser=argparse.ArgumentParser(description='Actualización '+VERSION+': solo código, con respaldo previo de datos')
    parser.add_argument('--destino',required=True,help='Carpeta del proyecto existente en Windows')
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument('--recuperar-codigo',metavar='RESGUARDO',help='Restituir código anterior solo si los datos no cambiaron')
    actions.add_argument('--aplicar',action='store_true',help='Aplicar después de cerrar todas las versiones del programa')
    args=parser.parse_args();source=Path(__file__).resolve().parent
    if args.recuperar_codigo:
        restore_code(args.recuperar_codigo,args.destino)
        print('Código anterior recuperado. La base y los TIFF no se modificaron.')
    elif args.aplicar:
        out=apply_update(source,args.destino)
        print('Código actualizado. Datos originales conservados. Resguardo:',out)
        print('Valida primero la demo con Python 3.8.10 y consulta docs/WINDOWS7.md antes de abrir producción.')
    else:
        manifest=inspect_release(source,args.destino)
        print('Comprobación correcta:',len(manifest['files']),'archivos de código. No se escribió en el destino.')
        print('Después de validar la demo y cerrar la aplicación, usa el mismo comando agregando --aplicar.')


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,sqlite3.Error) as error:
        print('Actualización detenida:',error,file=sys.stderr);sys.exit(1)
