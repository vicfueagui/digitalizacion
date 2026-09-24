"""Validación de inventario y entregas nuevas, exactas e independientes."""
import hashlib
import html
import json
import os
import shutil
import uuid
from pathlib import Path
from .core import now,js
from .assets import canonical
from .backup import sha256
from .manifests import plain_path,checked_files
from .operations import Operations


def canonical_json(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def content_hash(value):return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def verify_folder(root,expected_hash=None):
    root=Path(root).resolve()
    if (root/'INCOMPLETA.txt').exists():raise ValueError('La entrega tiene una copia interrumpida.')
    manifest=json.loads(plain_path(root,'manifest.json').read_text(encoding='utf-8'))
    if not isinstance(manifest,dict) or manifest.get('format')!=1 or not isinstance(manifest.get('items'),list):raise ValueError('Manifiesto de entrega desconocido.')
    digest=content_hash(manifest)
    if expected_hash and digest!=expected_hash:raise ValueError('El manifest hash no coincide con el de la entrega registrada.')
    items=manifest['items']
    if not items or any(not isinstance(i,dict) or not {'ruta','sha256','bytes','paginas','document_asset_id','file_version_id'}.issubset(i) for i in items):raise ValueError('Manifiesto sin elementos TIFF completos.')
    files=checked_files({i['ruta']:i['sha256'] for i in items},lambda n:n.startswith(('PERSONALES/','FEDERAL/')))
    if len(files)!=len(items) or len({i['document_asset_id'] for i in items})!=len(items):raise ValueError('Identidades o rutas repetidas dentro de la entrega.')
    if content_hash(items)!=manifest.get('inventario_hash'):raise ValueError('Inventario hash inconsistente.')
    if {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}!=set(files)|{'manifest.json'}:raise ValueError('La carpeta no coincide exactamente con el manifiesto.')
    from .coding import page_info
    for i in items:
        p=plain_path(root,i['ruta'])
        if sha256(p)!=i['sha256'] or p.stat().st_size!=i['bytes'] or len(page_info(p,True))!=i['paginas']:raise ValueError('TIFF exportado alterado: '+i['ruta'])
    return manifest


class Deliveries:
    def __init__(self,store,role='Responsable'):
        self.s=store;self.db=store.db;self.ops=Operations(store,role)

    def basis(self,work):
        w=self.s.one('trabajos',work)
        records=[]
        for row in self.s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=? ORDER BY id',(work,)):
            r=dict(row)
            try:
                p=self.s.workspace.path(row['ruta']);r['observed_hash']=sha256(p) if p.is_file() else None
            except (ValueError,OSError):r['observed_hash']=None
            records.append(r)
        extra=[]
        base=self.s.workspace.path('datos/tiff/trabajo_'+str(work))
        if base.exists():
            # Archivos nuevos externos también invalidan una validación anterior.
            extra=sorted(str(p.relative_to(base)) for p in base.rglob('*') if p.is_file())
        catalogue=self.s.rows("SELECT codigo,carpeta,activo FROM catalogos WHERE tipo='documento' ORDER BY codigo")
        observed=self.s.rows('SELECT o.id,o.estado,o.bloqueante,o.entrega_resuelta FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE e.trabajo_id=? ORDER BY o.id',(work,))
        return content_hash({'work':{k:w[k] for k in ('id','expediente_id','curp','legajo','folio_id','fisicos','digitalizador')},'files':records,'catalogue':catalogue,'observations':observed,'paths':extra,
                             'corrections':self.s.rows('SELECT c.id,c.estado FROM correcciones_tiff c JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? ORDER BY c.id',(work,))})

    def inventory(self,work,final=False):
        from .coding import page_info
        w=self.s.one('trabajos',work);issues=[];items=[];hashes={};names=set()
        def issue(level,rule,message,archivo=None):issues.append({'severidad':level,'regla':rule,'mensaje':message,'archivo_id':archivo})
        catalogue={r['codigo']:r for r in self.s.rows("SELECT * FROM catalogos WHERE tipo='documento'")}
        records=self.s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=? AND activo=1 ORDER BY id',(work,))
        for r in records:
            ident=r['id'];code=catalogue.get(r['codigo']);path=None
            if not r['documento_id'] or not r['version_id']:
                issue('BLOQUEANTE','identidad','TIFF sin documento/versión relacionados',ident);continue
            if not code or not code['activo']:
                issue('REQUIERE REVISIÓN','codigo','Código desconocido/inactivo o sin codificar',ident);continue
            if code['carpeta'] not in ('PERSONALES','FEDERAL'):
                issue('REQUIERE REVISIÓN','carpeta','Carpeta no configurada en catálogo',ident);continue
            name=canonical(self.s,r)
            if name.casefold() in names:issue('BLOQUEANTE','colision','Colisión de nombre canónico',ident)
            names.add(name.casefold())
            try:
                path=self.s.workspace.path(r['ruta'])
                if not path.is_file():raise ValueError('Archivo activo inexistente')
                measured=sha256(path)
                if measured!=r['hash_actual']:raise ValueError('SHA-256 distinto al registrado: archivo modificado externamente')
                original=self.s.workspace.path(r['original'])
                if not original.is_file() or sha256(original)!=r['hash_original']:raise ValueError('Original ausente o alterado')
                pages=len(page_info(path,True))
                if pages!=r['paginas']:raise ValueError('Cantidad de páginas distinta al registro')
                version=self.s.rows('SELECT * FROM versiones_archivo WHERE id=?',(r['version_id'],))[0]
                if version['documento_id']!=r['documento_id'] or version['sha256']!=measured:raise ValueError('La versión no corresponde al documento/contenido')
                if sha256(self.s.workspace.path(version['ruta']))!=measured:raise ValueError('La copia de versión perdió integridad')
                # La carpeta de trabajo puede ser Entrada; la salida organizada debe concordar.
                import re
                if not re.match(re.escape(r['codigo'])+r'(?:[ _(.]|\.)',path.name,re.I):issue('REQUIERE REVISIÓN','nombre','Nombre de trabajo y código no coinciden',ident)
                if path.parent.name in ('PERSONALES','FEDERAL') and path.parent.name!=code['carpeta']:issue('REQUIERE REVISIÓN','ubicacion','Carpeta de trabajo distinta del catálogo',ident)
                item={'document_asset_id':r['documento_id'],'file_version_id':r['version_id'],'archivo_id':ident,'nombre_canonico':name,'nombre_origen':r['nombre_origen'],
                      'nombre_trabajo':path.name,'codigo':r['codigo'],'carpeta':code['carpeta'],'sha256':measured,'bytes':path.stat().st_size,'paginas':pages,
                      'modalidad':'Individual' if pages==1 else 'Multi','activo':True,'ruta':code['carpeta']+'/'+name}
                items.append(item);hashes.setdefault(measured,[]).append(ident)
                if r['nombre_origen'] is None:issue('ADVERTENCIA','origen','Nombre original desconocido en el registro legado',ident)
            except (ValueError,OSError,KeyError,IndexError) as error:issue('BLOQUEANTE','integridad',str(error),ident)
        known={str(self.s.workspace.path(r['ruta'])).casefold() for r in records}
        base=self.s.workspace.path('datos/tiff/trabajo_'+str(work))
        for folder in (base/w['curp']/'PERSONALES',base/w['curp']/'FEDERAL'):
            if folder.exists():
                for p in folder.rglob('*'):
                    if p.is_file() and str(p.resolve()).casefold() not in known:issue('BLOQUEANTE' if p.suffix.lower() in ('.tif','.tiff') else 'REQUIERE REVISIÓN','residuo','Archivo no registrado en salida: '+p.name)
        duplicates=[ids for ids in hashes.values() if len(ids)>1]
        for ids in duplicates:issue('ADVERTENCIA','duplicado_exacto','Mismo contenido en registros '+', '.join(map(str,ids))+'; conservar hasta decidir')
        operations=self.s.rows("SELECT id FROM operaciones_tiff WHERE trabajo_id=? AND estado='Preparada'",(work,))
        replacements=self.s.rows("SELECT s.id FROM sustituciones_tiff s JOIN correcciones_tiff c ON c.id=s.correccion_id JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? AND s.fase!='Completada'",(work,))
        if operations or replacements:issue('BLOQUEANTE','operacion_pendiente','Hay operaciones TIFF interrumpidas')
        corrections=self.s.rows("SELECT c.id FROM correcciones_tiff c JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? AND c.estado='Pendiente'",(work,))
        if corrections:issue('BLOQUEANTE','reescaneo','Hay reescaneos pendientes')
        observations=self.s.rows("SELECT o.* FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE e.trabajo_id=? AND o.estado NOT IN ('Validada','Anulada')",(work,))
        for o in observations:issue('BLOQUEANTE' if final and o['bloqueante'] else 'ADVERTENCIA','observacion','Observación '+str(o['id'])+': '+o['estado'])
        if not records:issue('REQUIERE REVISIÓN','vacio','No hay TIFF activos; no se puede entregar un expediente vacío')
        if final:
            if w['conciliacion_pendiente']:issue('BLOQUEANTE','conciliacion','El vínculo del ciclo histórico con el maestro requiere confirmación')
            if w['fisicos'] is None:issue('BLOQUEANTE','conteo','Conteo físico sin confirmar')
            if self.s.rows("SELECT id FROM incidencias WHERE trabajo_id=? AND estado='Abierta'",(work,)):issue('BLOQUEANTE','incidencia','Hay incidencias abiertas')
            item=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(w['prestamo_item_id'],))
            if w['procedencia']!='Legado importado' and (not item or item[0]['validacion']!='Aceptado'):issue('BLOQUEANTE','recepcion','Recepción del préstamo no confirmada')
        levels={i['severidad'] for i in issues}
        result='BLOQUEANTE' if 'BLOQUEANTE' in levels else 'REQUIERE REVISIÓN' if 'REQUIERE REVISIÓN' in levels else 'OK con advertencias' if levels else 'OK'
        totals={'archivos':len(records),'archivos_verificados':len(items),'paginas_conocidas':sum(i['paginas'] for i in items),'paginas_desconocidas':len(records)-len(items),
                'individuales':sum(i['paginas']==1 for i in items),'multi':sum(i['paginas']>=2 for i in items),'por_carpeta':{},'por_codigo':{}}
        for i in items:
            for key,value in (('por_carpeta',i['carpeta']),('por_codigo',i['codigo'])):totals[key][value]=totals[key].get(value,0)+1
        return {'trabajo_id':work,'expediente_id':w['expediente_id'],'curp':w['curp'],'legajo':w['legajo'],'folio_id':w['folio_id'],
                'fecha':now(),'operador':self.s.operador,'final':final,'resultado':result,'totales':totals,'problemas':issues,'duplicados_exactos':duplicates,'items':sorted(items,key=lambda i:i['document_asset_id'])}

    def validate(self,work,final=False,delivery=None):
        report=self.inventory(work,final);basis=self.basis(work);ident=uuid.uuid4().hex
        with self.db:
            self.db.execute('UPDATE validaciones SET vigente=0 WHERE trabajo_id=?',(work,))
            self.db.execute('INSERT INTO validaciones VALUES(?,?,?,?,?,?,?,?,?)',(ident,work,delivery,now(),self.s.operador,report['resultado'],1,basis,js(report)))
        report['validacion_id']=ident
        return report

    def current_validation(self,work):
        rows=self.s.rows('SELECT * FROM validaciones WHERE trabajo_id=? AND vigente=1 ORDER BY rowid DESC LIMIT 1',(work,))
        if not rows:return None
        if rows[0]['huella_base']!=self.basis(work):
            if self.db.in_transaction:self.db.execute('UPDATE validaciones SET vigente=0 WHERE trabajo_id=?',(work,))
            else:
                with self.db:self.db.execute('UPDATE validaciones SET vigente=0 WHERE trabajo_id=?',(work,))
            return None
        return rows[0]

    def prepare(self,work):
        self.ops.permit('entrega')
        current=self.s.one('trabajos',work)
        if not current['activo'] or current['estado']=='Expediente cerrado':raise ValueError('Reactiva o reabre el ciclo con motivo antes de generar otra entrega.')
        report=self.validate(work)
        if report['resultado'] not in ('OK','OK con advertencias'):raise ValueError('Entrega bloqueada: '+'; '.join(i['mensaje'] for i in report['problemas']))
        w=self.s.one('trabajos',work);ident=uuid.uuid4().hex
        number=self.db.execute('SELECT COALESCE(MAX(numero),0)+1 FROM entregas WHERE trabajo_id=?',(work,)).fetchone()[0]
        root=self.s.workspace.path('datos/entregas/{}_L{}_C{}_ENTREGA_{:04d}'.format(w['curp'],w['legajo'],work,number))
        basis=self.basis(work)
        with self.db:self.db.execute('INSERT INTO entregas(id,trabajo_id,numero,creado,operador,estado,ruta) VALUES(?,?,?,?,?,?,?)',
                                    (ident,work,number,now(),self.s.operador,'Preparando',self.s.workspace.relative(root)))
        try:
            root.mkdir(parents=True,exist_ok=False);marker=root/'INCOMPLETA.txt';marker.write_text('No distribuir: entrega en preparación.',encoding='utf-8')
            from .coding import CodingService,page_info
            coder=CodingService(self.s)
            for i in report['items']:
                target=plain_path(root,i['ruta']);target.parent.mkdir(parents=True,exist_ok=True)
                source=self.s.workspace.path(self.s.rows('SELECT ruta FROM archivos_tiff WHERE id=?',(i['archivo_id'],))[0]['ruta'])
                coder.copy_new(source,target)
                if sha256(target)!=i['sha256'] or target.stat().st_size!=i['bytes'] or len(page_info(target,True))!=i['paginas']:raise ValueError('Falló la verificación de la entrega: '+i['nombre_canonico'])
            inventory_hash=content_hash(report['items'])
            manifest={'format':1,'expediente_id':w['expediente_id'],'curp':w['curp'],'legajo':w['legajo'],'ciclo_id':work,'entrega_id':ident,'numero':number,
                      'fecha':now(),'digitalizador':w['digitalizador'],'generado_por':self.s.operador,'estado':'Publicada para revisión','inventario_hash':inventory_hash,
                      'advertencias':report['problemas'],'items':report['items']}
            manifest_hash=content_hash(manifest)
            with (root/'manifest.json').open('x',encoding='utf-8') as out:out.write(canonical_json(manifest))
            if self.basis(work)!=basis:raise ValueError('El inventario cambió durante la exportación. La entrega quedó incompleta.')
            with self.db:
                for i in report['items']:
                    self.db.execute('INSERT INTO entrega_items(entrega_id,documento_id,version_id,archivo_id,nombre,nombre_origen,codigo,carpeta,sha256,bytes,paginas,modalidad,ruta) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (ident,i['document_asset_id'],i['file_version_id'],i['archivo_id'],i['nombre_canonico'],i['nombre_origen'],i['codigo'],i['carpeta'],i['sha256'],i['bytes'],i['paginas'],i['modalidad'],i['ruta']))
                self.db.execute("UPDATE entregas SET estado='Publicada',manifest_hash=?,inventario_hash=?,manifest=? WHERE id=?",(manifest_hash,inventory_hash,js(manifest),ident))
                self.db.execute('UPDATE validaciones SET entrega_id=? WHERE id=?',(ident,report['validacion_id']))
                self.ops.event(work,'Entrega '+str(number),'Snapshot inmutable '+manifest_hash)
            marker.unlink();self.verify(ident)
            metrics=coder.metrics(work,report['items'],[],root)
            with self.db:
                self.db.execute('INSERT INTO ejecuciones(huella,curp,fecha,payload,trabajo_id,ambito,valido,observacion) VALUES(?,?,?,?,?,?,?,?)',
                    (ident,w['curp'],now(),js(metrics),work,'Legajo',1,'Derivado de entrega '+str(number)+' / '+manifest_hash))
                self.db.execute('DELETE FROM inventario_pendiente WHERE trabajo_id=?',(work,))
                self.db.execute('UPDATE trabajos SET carpetas=1 WHERE id=?',(work,))
            return ident
        except BaseException:
            with self.db:self.db.execute("UPDATE entregas SET estado='Incompleta' WHERE id=?",(ident,))
            raise

    def get(self,ident):
        rows=self.s.rows('SELECT * FROM entregas WHERE id=?',(ident,))
        if not rows:raise ValueError('Entrega inexistente.')
        return rows[0]

    def verify(self,ident):
        row=self.get(ident)
        if row['estado'] not in ('Publicada','En revisión','Aprobada','Con observaciones'):raise ValueError('Entrega incompleta o no publicada.')
        root=self.s.workspace.path(row['ruta'])
        if (root/'INCOMPLETA.txt').exists():raise ValueError('Entrega interrumpida.')
        manifest=verify_folder(root,row['manifest_hash'])
        if content_hash(manifest)!=row['manifest_hash'] or manifest!=json.loads(row['manifest']):raise ValueError('El manifiesto de la entrega fue alterado.')
        files={i['ruta']:i['sha256'] for i in manifest['items']}
        checked_files(files,lambda n:n.startswith(('PERSONALES/','FEDERAL/')))
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        if actual!=set(files)|{'manifest.json'}:raise ValueError('La carpeta no coincide exactamente con el manifiesto.')
        for i in manifest['items']:
            p=plain_path(root,i['ruta'])
            if sha256(p)!=i['sha256'] or p.stat().st_size!=i['bytes']:raise ValueError('TIFF exportado alterado: '+i['nombre_canonico'])
        return manifest

    def export_copy(self,ident,destination):
        self.ops.permit('entrega');manifest=self.verify(ident);row=self.get(ident)
        source=self.s.workspace.path(row['ruta']);target=Path(destination).resolve()
        if source==target or source in target.parents:raise ValueError('Exporta a una carpeta nueva fuera de la entrega original.')
        target.mkdir(parents=True,exist_ok=False);marker=target/'INCOMPLETA.txt';marker.write_text('Copia de entrega en curso; no distribuir.',encoding='utf-8')
        for name in ['manifest.json']+[i['ruta'] for i in manifest['items']]:
            out=plain_path(target,name);out.parent.mkdir(parents=True,exist_ok=True)
            with plain_path(source,name).open('rb') as inp,out.open('xb') as dest:
                shutil.copyfileobj(inp,dest,1024*1024);dest.flush();os.fsync(dest.fileno())
        self.verify(ident)
        marker.unlink()
        try:verify_folder(target,row['manifest_hash'])
        except BaseException:
            marker.write_text('Copia no verificada; repetir en otro destino nuevo.',encoding='utf-8');raise
        with self.db:self.ops.event(row['trabajo_id'],'Exportar entrega '+str(row['numero']),'Copia independiente verificada: '+str(target))
        return target

    def diff(self,before,after):
        a={i['document_asset_id']:i for i in self.verify(before)['items']} if before else {}
        b={i['document_asset_id']:i for i in self.verify(after)['items']}
        result={'agregados':[],'retirados':[],'reemplazados':[],'renombrados':[],'recodificados':[],'movidos':[],'sin_cambios':[]}
        for doc in sorted(set(a)|set(b)):
            if doc not in a:result['agregados'].append(doc);continue
            if doc not in b:result['retirados'].append(doc);continue
            changed=False
            for category,key in (('reemplazados','file_version_id'),('renombrados','nombre_canonico'),('recodificados','codigo'),('movidos','carpeta')):
                if a[doc][key]!=b[doc][key]:result[category].append(doc);changed=True
            if a[doc].get('nombre_trabajo')!=b[doc].get('nombre_trabajo') and doc not in result['renombrados']:
                result['renombrados'].append(doc);changed=True
            if not changed:result['sin_cambios'].append(doc)
        return result

    def export_report(self,work):
        report=self.validate(work);out=self.s.workspace.reports/('validacion_'+report['validacion_id']+'.html');out.parent.mkdir(parents=True,exist_ok=True)
        text='<html lang="es"><meta charset="utf-8"><title>Validación del expediente</title><h1>'+html.escape(report['resultado'])+'</h1><pre>'+html.escape(json.dumps(report,ensure_ascii=False,indent=2))+'</pre></html>'
        with out.open('x',encoding='utf-8') as f:f.write(text)
        return out
