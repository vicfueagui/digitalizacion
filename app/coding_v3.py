"""Correcciones de escaneo, bajas reversibles y atajos numéricos."""
import json
import os
import uuid
from pathlib import Path
from .core import now,js
from .workspace import portable_name


def preview_image(image,size):
    from PIL import Image
    # Pillow fuerza vecino cercano en modo 1/P: convertir SOLO la vista.
    source=image.convert('L') if image.mode=='1' else image.convert('RGB') if image.mode=='P' else image
    return source.resize(size,Image.Resampling.LANCZOS)


def default_shortcut(code):
    prefix,number=code.split('-');number=int(number)
    return ('Ctrl+Shift',number) if prefix=='HL' else ('Ctrl',100+number) if prefix=='FP' else ('Ctrl',number)


class NumericInput:
    """La liberación de Ctrl confirma el número completo, sin temporizadores ambiguos."""
    def __init__(self):self.clear()
    def clear(self):self.digits='';self.combo=None;self.invalid=False
    def digit(self,digit,shift=False):
        combo='Ctrl+Shift' if shift else 'Ctrl'
        if self.combo not in (None,combo):self.invalid=True
        if str(digit) not in '0123456789' or len(str(digit))!=1:self.invalid=True
        self.combo=combo
        if len(self.digits)<3:self.digits+=str(digit)
        else:self.invalid=True
        if self.invalid:return 'Secuencia cancelada: máximo 999 y modificadores constantes. Suelta Ctrl.'
        return self.combo+' + '+self.digits
    def finish(self):
        result=(self.combo,int(self.digits)) if self.digits and not self.invalid else None
        self.clear();return result


class CodingV3:
    def ensure_numeric(self):
        with self.store.db:
            for cat in self.store.rows("SELECT * FROM catalogos WHERE tipo='documento' ORDER BY codigo"):
                if self.store.rows('SELECT * FROM atajos_numericos WHERE catalogo_id=?',(cat['id'],)):continue
                combo,num=default_shortcut(cat['codigo'])
                if not 1<=num<=999:num=None
                if num is None or self.store.rows('SELECT * FROM atajos_numericos WHERE combinacion=? AND numero=?',(combo,num)):
                    num=next((n for n in range(1,1000) if not self.store.rows('SELECT * FROM atajos_numericos WHERE combinacion=? AND numero=?',(combo,n))),None)
                if num is None:raise ValueError('No quedan atajos numéricos disponibles.')
                self.store.db.execute('INSERT INTO atajos_numericos VALUES(?,?,?)',(cat['id'],combo,num))

    def set_numeric(self,cid,combo,number):
        if combo not in ('Ctrl','Ctrl+Shift') or not str(number).isdigit() or not 1<=int(number)<=999:raise ValueError('Combinación Ctrl o Ctrl+Shift y número entero de 1 a 999.')
        with self.store.db:
            before=self.store.rows('SELECT * FROM atajos_numericos WHERE catalogo_id=?',(cid,))
            self.store.db.execute('UPDATE atajos_numericos SET combinacion=?,numero=? WHERE catalogo_id=?',(combo,int(number),cid))
            self.store.audit('atajos_numericos',cid,'configurar',before,{'combinacion':combo,'numero':int(number)},'Atajo numérico elegido')

    def mark_correction(self,ident,page,location,problem):
        row,path=self.checked(ident)
        if not location.strip() or not problem.strip() or not 1<=int(page)<=row['paginas']:raise ValueError('Indica página TIFF, ubicación de la hoja física y problema.')
        with self.store.db:
            incident=self.store.db.execute("INSERT INTO incidencias(trabajo_id,codigo_snapshot,documento,problema,accion,creado) VALUES(?,?,?,?,?,?)",(row['trabajo_id'],'REESCANEO',path.name+' / página '+str(page),problem,'Ubicación física: '+location,now())).lastrowid
            ident_c=self.store.db.execute('INSERT INTO correcciones_tiff(archivo_id,pagina,ubicacion,problema,creado,incidencia_id) VALUES(?,?,?,?,?,?)',(ident,page,location,problem,now(),incident)).lastrowid
            self.invalidate(row['trabajo_id']);self.store.audit('correcciones_tiff',ident_c,'marcar',None,{'archivo':ident,'pagina':page,'ubicacion':location,'problema':problem},'Requiere nuevo escaneo')
        return ident_c

    def corrections(self,work):
        return self.store.rows('''SELECT c.*,a.ruta,a.trabajo_id,a.codigo,t.curp,t.legajo,f.numero AS folio,
            cat.titulo AS documento FROM correcciones_tiff c JOIN archivos_tiff a ON a.id=c.archivo_id
            JOIN trabajos t ON t.id=a.trabajo_id JOIN folios f ON f.id=t.folio_id
            LEFT JOIN catalogos cat ON cat.codigo=a.codigo AND cat.tipo='documento'
            WHERE a.trabajo_id=? ORDER BY c.id''',(work,))

    def exclude(self,ident,reason,checkpoint=None):
        row,path=self.checked(ident)
        if not reason.strip():raise ValueError('Indica por qué se retira el TIFF.')
        target=self.path(self.work_dir(row['trabajo_id'])/'retirados'/(str(ident)+'_'+path.name));target.parent.mkdir(exist_ok=True)
        if target.exists():target=target.with_name(uuid.uuid4().hex+'_'+target.name)
        op=self.log(row['trabajo_id'],ident,'renombrar',{'antes':row['ruta'],'despues':self.relative(target),'baja':True})
        moved=False
        try:
            self.move_file(path,target);moved=True
            with self.store.db:
                self.store.db.execute("UPDATE archivos_tiff SET ruta=?,activo=0,estado='Retirado' WHERE id=?",(self.relative(target),ident));self.invalidate(row['trabajo_id'])
                from .assets import lifecycle
                lifecycle(self,ident,'Retirado')
                self.store.audit('archivos_tiff',ident,'retirar',row,self.file(ident),reason);self.finish(op,'Completada')
                if checkpoint:checkpoint()
        except Exception as error:
            if getattr(error,'requires_recovery',False):raise
            if moved:self.move_file(target,path)
            with self.store.db:self.finish(op,'Fallida sin cambios')
            raise

    def restore_removed(self,ident,reason):
        from .coding import digest
        row=self.file(ident);self.active_work(row['trabajo_id'])
        if row['activo']:raise ValueError('El archivo ya está activo.')
        if self.store.rows('SELECT id FROM archivos_tiff WHERE trabajo_id=? AND documento_id=? AND activo=1',(row['trabajo_id'],row['documento_id'])):
            raise ValueError('Ya hay una versión activa de este documento. Retírala con motivo antes de recuperar la anterior.')
        if not reason.strip():raise ValueError('Indica motivo.')
        source=self.path(row['ruta'])
        if not source.exists() or digest(source)!=row['hash_actual']:raise ValueError('No se pudo verificar el TIFF retirado.')
        # Mantener el nombre original si está disponible.
        name=portable_name(row['ruta']).split('_',1)[-1]
        target=self.free_name(self.work_dir(row['trabajo_id'])/'entrada'/name)
        op=self.log(row['trabajo_id'],ident,'renombrar',{'antes':row['ruta'],'despues':self.relative(target)})
        moved=False
        try:
            self.move_file(source,target);moved=True
            with self.store.db:
                self.store.db.execute("UPDATE archivos_tiff SET ruta=?,activo=1,estado='Entrada' WHERE id=?",(self.relative(target),ident));self.invalidate(row['trabajo_id'])
                from .assets import lifecycle
                lifecycle(self,ident,'Activo')
                self.store.audit('archivos_tiff',ident,'restaurar retirado',row,self.file(ident),reason);self.finish(op,'Completada')
        except Exception as error:
            if getattr(error,'requires_recovery',False):raise
            if moved:self.move_file(target,source)
            with self.store.db:self.finish(op,'Fallida sin cambios')
            raise

    def replace_correction(self,cid,new_id,reason):
        self.begin_replacement(cid,new_id,reason,'completo')

    def replace_scanned_page(self,cid,new_id,reason):
        self.begin_replacement(cid,new_id,reason,'pagina')

    def begin_replacement(self,cid,new_id,reason,kind):
        from .coding import page_info
        found=self.store.rows('SELECT * FROM correcciones_tiff WHERE id=?',(cid,))
        if not found or found[0]['estado']!='Pendiente':raise ValueError('La corrección no está pendiente.')
        c=found[0];old=self.file(c['archivo_id']);new,path=self.checked(new_id)
        if old['id']==new['id'] or old['trabajo_id']!=new['trabajo_id']:raise ValueError('Selecciona OTRO TIFF del mismo expediente/legajo.')
        if not reason.strip():raise ValueError('Confirma la revisión del nuevo escaneo.')
        if kind=='completo' and old['paginas']!=new['paginas']:raise ValueError('El reemplazo completo debe conservar la cantidad de páginas.')
        if kind=='pagina' and (new['paginas']!=1 or not old['activo']):raise ValueError('Se requiere un TIFF nuevo de una página y el anterior activo.')
        page_info(path,True)
        with self.store.db:
            if self.store.rows("SELECT 1 FROM sustituciones_tiff WHERE correccion_id=? AND fase!='Completada'",(cid,)):
                raise ValueError('Sustitución pendiente. Usa Recuperar operación.')
            # Una marca reabierta puede recibir otro reemplazo; su historial queda en auditoría.
            self.store.db.execute('INSERT OR REPLACE INTO sustituciones_tiff(correccion_id,nuevo_id,tipo,fase,motivo,creado) VALUES(?,?,?,?,?,?)',(cid,new_id,kind,'Preparada',reason,now()))
            self.invalidate(old['trabajo_id'])
        self.apply_replacement(cid)

    def apply_replacement(self,cid):
        self._resuming_replacement=True
        try:self._apply_replacement(cid)
        finally:self._resuming_replacement=False

    def _apply_replacement(self,cid):
        entry=self.store.rows('SELECT * FROM sustituciones_tiff WHERE correccion_id=?',(cid,))[0]
        c=self.store.rows('SELECT * FROM correcciones_tiff WHERE id=?',(cid,))[0]
        old=self.file(c['archivo_id']);new=self.file(entry['nuevo_id']);reason=entry['motivo']
        def phase(value):self.store.db.execute('UPDATE sustituciones_tiff SET fase=? WHERE correccion_id=?',(value,cid))
        if entry['fase']=='Completada':return
        if entry['fase']=='Preparada':
            if entry['tipo']=='pagina':
                _,path=self.checked(new['id'])
                self.save_edit(old['id'],c['pagina']-1,[('replace_page',str(path),0)],checkpoint=lambda:phase('Aplicada'))
            else:
                if old['codigo'] and new['codigo']!=old['codigo']:self.assign(new['id'],old['codigo'])
                with self.store.db:phase('Aplicada')
        entry=self.store.rows('SELECT * FROM sustituciones_tiff WHERE correccion_id=?',(cid,))[0]
        if entry['fase']=='Aplicada':
            retired=new['id'] if entry['tipo']=='pagina' else old['id']
            if self.file(retired)['activo']:
                self.exclude(retired,'Sustitución registrada: '+reason,checkpoint=lambda:phase('Retirada'))
            else:
                with self.store.db:phase('Retirada')
        with self.store.db:
            if entry['tipo']=='completo':
                from .assets import replacement
                replacement(self,old['id'],new['id'])
            sql="SELECT * FROM correcciones_tiff WHERE archivo_id=? AND estado='Pendiente'"
            args=(old['id'],)
            if entry['tipo']=='pagina':sql+=' AND pagina=?';args+=(c['pagina'],)
            state='Página sustituida' if entry['tipo']=='pagina' else 'Sustituida'
            for record in self.store.rows(sql,args):
                self.store.db.execute('UPDATE correcciones_tiff SET estado=?,resuelto=?,nuevo_id=? WHERE id=?',(state,now(),new['id'],record['id']))
                self.store.db.execute("UPDATE incidencias SET estado='Resuelta',resuelto=?,accion=? WHERE id=?",(now(),reason,record['incidencia_id']))
            self.invalidate(old['trabajo_id']);self.store.audit('correcciones_tiff',cid,'sustituir '+entry['tipo'],c,{'nuevo_id':new['id']},reason)
            phase('Completada')

    def resume_replacements(self,work):
        rows=self.store.rows("SELECT s.correccion_id FROM sustituciones_tiff s JOIN correcciones_tiff c ON c.id=s.correccion_id JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? AND s.fase!='Completada' ORDER BY s.id",(work,))
        for row in rows:self.apply_replacement(row['correccion_id'])
        return len(rows)

    def resolve_without_replacement(self,cid,reason):
        if not reason.strip():raise ValueError('Explica la revisión o anulación.')
        row=self.store.rows('SELECT * FROM correcciones_tiff WHERE id=?',(cid,))[0]
        if self.store.rows("SELECT 1 FROM sustituciones_tiff WHERE correccion_id=? AND fase!='Completada'",(cid,)):raise ValueError('Recupera primero la sustitución interrumpida.')
        self.active_work(self.file(row['archivo_id'])['trabajo_id'])
        if row['estado']!='Pendiente':raise ValueError('La corrección ya está resuelta.')
        with self.store.db:
            self.store.db.execute("UPDATE correcciones_tiff SET estado='Revisada',resuelto=? WHERE id=?",(now(),cid))
            self.store.db.execute("UPDATE incidencias SET estado='Resuelta',resuelto=?,accion=? WHERE id=?",(now(),reason,row['incidencia_id']))
            self.store.audit('correcciones_tiff',cid,'resolver',row,None,reason)
