"""Reconstruir un candidato comprobable. Nunca reparar el workspace de forma implícita."""
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .backup import sha256,snapshot
from .coding import stream_edit,page_info
from .integrity import runtime_info
from .manifests import plain_path
from .portability import active_relative
from .update_recovery import write_json
from .workspace import WorkspaceLock


def reconstruct_candidate(workspace,file_id,revision_id,operation_id,destination):
    destination=Path(destination).resolve()
    if destination==workspace.root or workspace.root in destination.parents:
        raise ValueError('El candidato debe quedar fuera del workspace original.')
    if destination.exists():raise FileExistsError('El destino del candidato ya existe.')
    if not workspace.database.is_file():raise ValueError('No existe la base del workspace que se quiere investigar.')
    lock=WorkspaceLock(workspace.root)
    try:
        with tempfile.TemporaryDirectory(prefix='digitalizacion-reconstruccion-') as temp:
            dbcopy=Path(temp)/'evidencia.sqlite3'
            source=sqlite3.connect(workspace.database.as_uri()+'?mode=ro',uri=True)
            try:snapshot(source,dbcopy)
            finally:source.close()
            db=sqlite3.connect(str(dbcopy));db.row_factory=sqlite3.Row
            try:
                row=db.execute('SELECT * FROM archivos_tiff WHERE id=?',(file_id,)).fetchone()
                revision=db.execute('SELECT * FROM revisiones_tiff WHERE id=? AND archivo_id=?',(revision_id,file_id)).fetchone()
                operation=db.execute("SELECT * FROM operaciones_tiff WHERE id=? AND archivo_id=? AND tipo='editar' AND estado='Completada'",(operation_id,file_id)).fetchone()
                if not all((row,revision,operation)):raise ValueError('No hay una cadena de revisión/operación completada para ese TIFF.')
                original=plain_path(workspace.root,active_relative(workspace,row['original']))
                if not original.is_file() or sha256(original)!=row['hash_original']:
                    raise ValueError('El original no supera su hash. Conserva la evidencia.')
                path=plain_path(workspace.root,active_relative(workspace,revision['ruta']))
                if not path.is_file() or sha256(path)!=revision['hash']:raise ValueError('La revisión falta o no coincide con su hash.')
                detail=json.loads(operation['detalle']);record=json.loads(revision['operacion'])
                page=detail.get('pagina');ops=detail.get('operaciones')
                if record.get('pagina')!=page or record.get('ops')!=ops:
                    raise ValueError('La revisión y la operación no describen la misma transformación.')
                if not isinstance(page,int) or not isinstance(ops,list) or not ops:
                    raise ValueError('Operación sin evidencia de página/transformación.')
                for op in ops:
                    if (not isinstance(op,(list,tuple)) or not op or
                            (op[0]=='rotate' and len(op)!=2) or (op[0]=='crop' and len(op)!=5) or
                            op[0] not in ('rotate','crop')):
                        raise ValueError('Solo se reconstruyen giros/recortes documentados. No se adivinan reemplazos ni fuentes externas.')
                temporary=Path(temp)/'candidato.tif'
                stream_edit(path,temporary,page-1,ops)
                actual=sha256(temporary)
                if actual!=row['hash_actual']:
                    raise ValueError('La reconstrucción NO coincide byte a byte con el hash esperado. No se publicó ni reparó nada.')
                if len(page_info(temporary,True))!=row['paginas']:raise ValueError('Las páginas no coinciden.')
                destination.mkdir(parents=True,exist_ok=False)
                marker=destination/'INCOMPLETO.txt'
                marker.write_text('Candidato en preparación. No utilizar.',encoding='utf-8')
                # Solo copia externa nueva; el TIFF original/actual y SQLite permanecen intactos.
                import shutil
                copied=destination/'candidato.tif';shutil.copy2(str(temporary),str(copied))
                if sha256(copied)!=row['hash_actual']:raise ValueError('Falló la copia del candidato.')
                report={'formato':1,'resultado':'CANDIDATO EXACTO; WORKSPACE SIN REPARAR','archivo_id':file_id,
                        'revision_id':revision_id,'operacion_id':operation_id,'sha256':actual,
                        'hash_original':row['hash_original'],'hash_revision':revision['hash'],
                        'paginas':row['paginas'],'operaciones':ops,'pagina':page,'entorno':runtime_info()}
                write_json(destination/'evidencia.json',report)
                marker.unlink()
                return report
            finally:db.close()
    finally:lock.close()
