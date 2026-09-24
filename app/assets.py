"""Identidad documental estable y versiones de contenido independientes del nombre."""
import uuid
from .core import now


def uid():return uuid.uuid4().hex


def migrate(store):
    for row in store.rows('SELECT * FROM archivos_tiff ORDER BY id'):
        document=create_document(store,row['trabajo_id'],None)
        previous=None
        # Sin abrir/mover archivos: fechas/rutas/hash existentes quedan conservados.
        previous=register_version(store,document,row['original'],row['hash_original'],None,None,'Original legado',previous,'Histórico',row['id'])
        for rev in store.rows('SELECT * FROM revisiones_tiff WHERE archivo_id=? ORDER BY id',(row['id'],)):
            previous=register_version(store,document,rev['ruta'],rev['hash'],None,None,'Revisión legada: '+rev['operacion'],previous,'Histórico',row['id'])
        current=register_version(store,document,row['ruta'],row['hash_actual'],None,row['paginas'],'Estado al migrar (fecha histórica desconocida)',previous,'Activo' if row['activo'] else 'Retirado',row['id'])
        store.db.execute('UPDATE archivos_tiff SET documento_id=?,version_id=? WHERE id=?',(document,current,row['id']))
        if not row['activo']:store.db.execute("UPDATE documentos_logicos SET estado='Retirado' WHERE id=?",(document,))


def create_document(store,work,original_name):
    master=store.one('trabajos',work)['expediente_id']
    if not master:raise ValueError('El ciclo requiere conciliación con un expediente maestro antes de incorporar TIFF.')
    sequence=store.db.execute('SELECT COALESCE(MAX(secuencia),0)+1 FROM documentos_logicos WHERE expediente_id=?',(master,)).fetchone()[0]
    ident=uid()
    store.db.execute('INSERT INTO documentos_logicos(id,expediente_id,secuencia,nombre_origen,creado) VALUES(?,?,?,?,?)',(ident,master,sequence,original_name,now()))
    return ident


def register_version(store,document,path,sha,size,pages,action,previous=None,state='Activo',source=None):
    ident=uid()
    store.db.execute('INSERT INTO versiones_archivo VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                     (ident,document,previous,path,sha,size,pages,now(),store.operador,action,state,source))
    return ident


def imported(service,ident,source):
    row=service.file(ident);s=service.store
    document=create_document(s,row['trabajo_id'],source.name)
    version=register_version(s,document,row['original'],row['hash_actual'],service.path(row['original']).stat().st_size,row['paginas'],'Importación verificada',source=ident)
    s.db.execute('UPDATE archivos_tiff SET documento_id=?,version_id=?,nombre_origen=? WHERE id=?',(document,version,source.name,ident))


def changed(service,ident,old,revision,action):
    row=service.file(ident);s=service.store
    # Una versión migrada puede apuntar a la copia de trabajo: preservar su ubicación anterior.
    current=s.rows('SELECT * FROM versiones_archivo WHERE id=?',(old['version_id'],))[0]
    if service.path(current['ruta'])==service.path(old['ruta']):
        s.db.execute('UPDATE versiones_archivo SET ruta=? WHERE id=?',(service.relative(revision),old['version_id']))
    blob=service.path('datos/versiones/'+uid()+'.tif');blob.parent.mkdir(parents=True,exist_ok=True)
    service.copy_new(service.path(row['ruta']),blob)
    from .coding import digest,page_info
    if digest(blob)!=row['hash_actual'] or len(page_info(blob,True))!=row['paginas']:raise ValueError('La nueva versión no supera la comprobación de contenido.')
    s.db.execute("UPDATE versiones_archivo SET estado='Supersedido' WHERE id=?",(old['version_id'],))
    version=register_version(s,row['documento_id'],service.relative(blob),row['hash_actual'],blob.stat().st_size,row['paginas'],action,old['version_id'],source=ident)
    s.db.execute('UPDATE archivos_tiff SET version_id=? WHERE id=?',(version,ident))


def lifecycle(service,ident,state):
    row=service.file(ident);s=service.store
    # Mantener referencias migradas válidas después de mover la copia de trabajo.
    version=s.rows('SELECT * FROM versiones_archivo WHERE id=?',(row['version_id'],))[0]
    if not service.path(version['ruta']).exists():s.db.execute('UPDATE versiones_archivo SET ruta=? WHERE id=?',(row['ruta'],row['version_id']))
    s.db.execute('UPDATE versiones_archivo SET estado=? WHERE id=?',(state,row['version_id']))
    s.db.execute('UPDATE documentos_logicos SET estado=? WHERE id=?',(state,row['documento_id']))


def replacement(service,old_id,new_id):
    old=service.file(old_id);new=service.file(new_id);s=service.store
    if old['documento_id']==new['documento_id']:return
    # Conservar la importación provisional, vinculando una versión sucesora al documento corregido.
    source=s.rows('SELECT * FROM versiones_archivo WHERE id=?',(new['version_id'],))[0]
    s.db.execute("UPDATE documentos_logicos SET estado='Histórico' WHERE id=?",(new['documento_id'],))
    s.db.execute("UPDATE versiones_archivo SET estado='Histórico' WHERE id=?",(new['version_id'],))
    ident=register_version(s,old['documento_id'],source['ruta'],source['sha256'],source['bytes'],source['paginas'],'Reescaneo completo confirmado',old['version_id'],source=new_id)
    s.db.execute('UPDATE archivos_tiff SET documento_id=?,version_id=? WHERE id=?',(old['documento_id'],ident,new_id))
    s.db.execute("UPDATE versiones_archivo SET estado='Supersedido' WHERE id=?",(old['version_id'],))
    s.db.execute("UPDATE documentos_logicos SET estado='Activo' WHERE id=?",(old['documento_id'],))


def canonical(store,row):
    document=store.rows('SELECT * FROM documentos_logicos WHERE id=?',(row['documento_id'],))[0]
    return '{}__{:03d}__{}.tif'.format(row['codigo'] or 'SIN_CODIGO',document['secuencia'],document['id'][:12].upper())
