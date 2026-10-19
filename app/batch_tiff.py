"""Selecciones explícitas, prevalidación completa y progreso durable por archivo.

Cada archivo conserva el diario recuperable existente. Un lote interrumpido no
se presenta como transacción atómica: muestra terminados, error y pendientes.
"""
import json
import uuid
from .core import now,js


class BatchTiff:
    def __init__(self,service):self.c=service;self.s=service.store

    def preflight(self,work,ids,action,reason,code=None):
        if action not in ('retirar','recuperar','codificar') or not reason.strip():raise ValueError('Selecciona acción e indica motivo.')
        if action=='codificar' and not any(c['codigo']==code for c in self.c.catalog()):raise ValueError('Código no activo.')
        ids=list(dict.fromkeys(int(i) for i in ids))
        if not ids:raise ValueError('Selecciona al menos un TIFF.')
        self.c.active_work(work);documents=set()
        from .coding import digest
        for ident in ids:
            row=self.c.file(ident)
            if row['trabajo_id']!=work:raise ValueError('La selección contiene TIFF de otro expediente.')
            if bool(row['activo'])!=(action!='recuperar'):raise ValueError('La selección cambió; actualiza la lista antes de continuar.')
            path=self.c.path(row['ruta'])
            if not path.is_file() or digest(path)!=row['hash_actual']:raise ValueError('No se pudo verificar el TIFF '+str(ident))
            if action=='recuperar':
                if row['documento_id'] in documents or self.s.rows('SELECT id FROM archivos_tiff WHERE documento_id=? AND activo=1',(row['documento_id'],)):
                    raise ValueError('Recupera una sola versión por documento y retira primero cualquier versión activa.')
                documents.add(row['documento_id'])
        return ids

    def run(self,work,ids,action,reason,checkpoint=None,code=None):
        ids=self.preflight(work,ids,action,reason,code);ident=uuid.uuid4().hex
        result={'completados':[],'pendientes':ids[:],'error':None}
        if action=='codificar':result['codigo']=code
        with self.s.db:self.s.db.execute('INSERT INTO lotes_tiff VALUES(?,?,?,?,?,?,?,?,?)',(ident,work,action,reason.strip(),self.s.operador,now(),'En curso',js(ids),js(result)))
        for file_id in ids:
            try:
                # El diario individual y el estado activo permiten conciliar un corte
                # incluso entre la confirmación del archivo y la del lote.
                if checkpoint:checkpoint(file_id)
                if action=='codificar':self.c.assign(file_id,code)
                else:(self.c.exclude if action=='retirar' else self.c.restore_removed)(file_id,reason)
                result['completados'].append(file_id);result['pendientes'].remove(file_id)
            except Exception as error:
                result['error']=str(error)
                break
            finally:
                with self.s.db:self.s.db.execute('UPDATE lotes_tiff SET resultado=? WHERE id=?',(js(result),ident))
        state='Completado' if not result['pendientes'] else 'Parcial'
        with self.s.db:
            self.s.db.execute('UPDATE lotes_tiff SET estado=? WHERE id=?',(state,ident))
            self.s.audit('lotes_tiff',ident,action,None,result,reason)
        return dict(result,id=ident,estado=state)

    def status(self,ident):
        row=self.s.rows('SELECT * FROM lotes_tiff WHERE id=?',(ident,))[0]
        result=json.loads(row['resultado']);desired=row['accion']=='recuperar'
        # Solo conciliación informativa: no repetir mutaciones automáticamente.
        result['estado_actual']={str(i):(self.c.file(i)['codigo']==result.get('codigo') if row['accion']=='codificar'
                                      else bool(self.c.file(i)['activo'])==desired) for i in json.loads(row['seleccion'])}
        return dict(result,estado=row['estado'],id=ident)
