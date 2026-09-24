"""Codificación local de copias TIFF. Nunca modifica el origen seleccionado."""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from . import VERSION
from .core import ROOT, now, js
from .workspace import portable_name

ALPHABET='ASDFGHJKLQWERTYUIOPZXCVBNM'
SHORTCUTS=[a+b for a in ALPHABET[:8] for b in ALPHABET[:8]]
SHORTCUTS += [a+b for a in ALPHABET for b in ALPHABET if a+b not in SHORTCUTS]
MAX_PIXELS=36000000


class MoveRecoveryRequired(ValueError):
    requires_recovery = True


def pillow():
    try:
        from PIL import Image, TiffImagePlugin
    except ImportError:
        raise ValueError('Falta el visor TIFF. Cierra el programa y ejecuta INSTALAR_VISOR.bat; consulta ACTUALIZACION.html.')
    return Image,TiffImagePlugin


def digest(path):
    h=hashlib.sha256()
    with open(str(path),'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def page_info(path, decode=False):
    Image,_=pillow();result=[]
    with Image.open(str(path)) as im:
        if im.format!='TIFF':raise ValueError('El archivo no es TIFF: '+Path(path).name)
        for i in range(im.n_frames):
            im.seek(i)
            if im.width*im.height>MAX_PIXELS:
                raise ValueError('La página {} supera 36 millones de píxeles. Usa una copia a menor resolución en este equipo.'.format(i+1))
            if im.mode not in ('1','L','RGB','RGBA','P'):
                raise ValueError('Modo TIFF no admitido para edición: '+im.mode)
            if decode:im.load()
            result.append({'size':im.size,'mode':im.mode,'dpi':im.info.get('dpi',(300,300))})
    if not result:raise ValueError('TIFF sin páginas.')
    return result


def combined_operations(ops):
    result=[]
    for op in ops:
        if op[0]=='rotate':
            angle=float(op[1])
            if not -180<=angle<=180:raise ValueError('Ángulo fuera de -180 a 180 grados.')
            if result and result[-1][0]=='rotate':angle+=result.pop()[1]
            angle=(angle+180)%360-180
            result.append(('rotate',angle))
        else:result.append(op)
    return [op for op in result if op[0]!='rotate' or abs(op[1])>1e-9]


def render_page(path,index,ops=()):
    Image,_=pillow()
    with Image.open(str(path)) as im:
        im.seek(index)
        if im.width*im.height>MAX_PIXELS:raise ValueError('Página demasiado grande para este visor.')
        # Copiar una sola página; Pillow aplica la orientación TIFF al decodificar.
        frame=im.copy()
    for op in combined_operations(ops):
        if op[0]=='crop':
            x1,y1,x2,y2=map(int,op[1:])
            if not (0<=x1<x2<=frame.width and 0<=y1<y2<=frame.height):raise ValueError('Recorte fuera de la imagen.')
            frame=frame.crop((x1,y1,x2,y2))
        elif op[0]=='rotate':
            angle=float(op[1])
            if not (-180<=angle<=180):raise ValueError('Ángulo fuera de -180 a 180 grados.')
            if angle%90==0:
                frame=frame.rotate(angle,expand=True)
            else:
                # Interpolación en gris/color; no convertir texto a blanco/negro con umbral arbitrario.
                mode='RGB' if frame.mode in ('RGB','RGBA','P') else 'L'
                frame=frame.convert(mode).rotate(angle,resample=Image.Resampling.BICUBIC,expand=True,fillcolor='white')
        elif op[0]=='replace_page':
            frame.close();frame=render_page(op[1],int(op[2]))
        else:raise ValueError('Operación desconocida.')
    return frame


def stream_edit(source,target,page,ops):
    """Reescribe todas las páginas con memoria acotada, editando solo la elegida."""
    Image,Tiff=pillow();infos=page_info(source)
    if not 0<=page<len(infos):raise ValueError('Página inexistente.')
    with Image.open(str(source)) as original, Tiff.AppendingTiffWriter(str(target),True) as writer:
        for index,info in enumerate(infos):
            original.seek(index)
            # Solo etiquetas descriptivas, nunca offsets/compression/orientation heredados.
            tags={tag:original.tag_v2[tag] for tag in (269,270,271,272,285,306,315,33432) if tag in original.tag_v2}
            image=render_page(source,index,ops) if index==page else original.copy()
            dpi=info['dpi']
            if index==page:
                replacement=next((op for op in ops if op[0]=='replace_page'),None)
                if replacement:dpi=page_info(replacement[1])[int(replacement[2])]['dpi']
            if index==page:
                rotation=sum(float(op[1]) for op in ops if op[0]=='rotate')
                if rotation%180 in (90,):dpi=(dpi[1],dpi[0])
            kwargs={'compression':'tiff_deflate','dpi':dpi,'tiffinfo':tags}
            if original.info.get('icc_profile'):kwargs['icc_profile']=original.info['icc_profile']
            image.save(writer,format='TIFF',**kwargs);writer.newFrame();image.close()
    # Comprobar todas las páginas, no solo el encabezado o la primera página.
    if len(page_info(target,True))!=len(infos):raise ValueError('La copia editada perdió páginas; no se aplicará.')
    with Image.open(str(source)) as a,Image.open(str(target)) as b:
        for index in range(len(infos)):
            expected=render_page(source,index,ops) if index==page else None
            a.seek(index);b.seek(index)
            if expected is None:expected=a.copy()
            if expected.size!=b.size or expected.mode!=b.mode or expected.tobytes()!=b.tobytes():
                raise ValueError('La verificación de píxeles falló; no se reemplazó la copia de trabajo.')
            expected.close()


from .coding_v3 import CodingV3

class CodingService(CodingV3):
    def __init__(self,store,root=None):
        self.store=store;self.root=store.workspace.root
        if root is not None and Path(root).resolve()!=self.root:
            raise ValueError('La raíz TIFF debe coincidir con el espacio de la base.')
        self.ensure_shortcuts();self.ensure_numeric()

    def ensure_shortcuts(self):
        with self.store.db:
            used={r['secuencia'] for r in self.store.rows('SELECT * FROM atajos')}
            for cat in self.store.rows("SELECT * FROM catalogos WHERE tipo='documento' ORDER BY codigo,id"):
                if not self.store.rows('SELECT * FROM atajos WHERE catalogo_id=?',(cat['id'],)):
                    seq=next((s for s in SHORTCUTS if s not in used),None)
                    if not seq:continue  # Atajos antiguos opcionales; no limitar los numéricos.
                    favorite=len(used)+1 if len(used)<9 else None
                    if favorite and self.store.rows('SELECT catalogo_id FROM atajos WHERE favorito=?',(favorite,)):favorite=None
                    self.store.db.execute('INSERT INTO atajos(catalogo_id,secuencia,favorito) VALUES(?,?,?)',(cat['id'],seq,favorite));used.add(seq)

    def catalog(self):
        self.ensure_shortcuts();self.ensure_numeric()
        return self.store.rows("SELECT c.*,a.secuencia,a.favorito,n.combinacion,n.numero FROM catalogos c LEFT JOIN atajos a ON a.catalogo_id=c.id JOIN atajos_numericos n ON n.catalogo_id=c.id WHERE c.tipo='documento' AND c.activo=1 ORDER BY c.codigo")

    def set_shortcut(self,catalog_id,sequence,favorite=None):
        sequence=sequence.strip().upper()
        if not re.fullmatch('[A-Z]{2}',sequence):raise ValueError('Escribe dos letras A-Z, por ejemplo AS.')
        favorite=int(favorite) if favorite else None
        if favorite is not None and favorite not in range(1,10):raise ValueError('Favorito: 1 a 9 o vacío.')
        with self.store.db:
            before=self.store.rows('SELECT * FROM atajos WHERE catalogo_id=?',(catalog_id,))
            self.store.db.execute('UPDATE atajos SET secuencia=?,favorito=? WHERE catalogo_id=?',(sequence,favorite,catalog_id))
            self.store.audit('atajos',catalog_id,'configurar',before,{'secuencia':sequence,'favorito':favorite},'Preferencia del operador')

    def path(self,relative):return self.store.workspace.path(relative)

    def relative(self,path):return self.store.workspace.relative(path)

    def work_dir(self,work):return self.path('datos/tiff/trabajo_'+str(int(work)))

    def active_work(self,work):
        if self.store.rows("SELECT id FROM operaciones_tiff WHERE trabajo_id=? AND estado='Preparada'",(work,)):
            raise ValueError('Existe una operación interrumpida. Pulsa Recuperar operación antes de continuar.')
        if not getattr(self,'_resuming_replacement',False) and self.store.rows("SELECT s.id FROM sustituciones_tiff s JOIN correcciones_tiff c ON c.id=s.correccion_id JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? AND s.fase!='Completada'",(work,)):
            raise ValueError('Hay una sustitución interrumpida. Usa Recuperar operación antes de cambiar archivos.')
        w=self.store.one('trabajos',work)
        if not w['activo'] or w['estado']=='Expediente cerrado':raise ValueError('Reactiva o reabre el expediente antes de codificar.')
        return w

    def recover(self,work):
        pending=self.store.rows("SELECT * FROM operaciones_tiff WHERE trabajo_id=? AND estado='Preparada' ORDER BY id",(work,))
        recovered=0
        for op in pending:
            info=json.loads(op['detalle'])
            if op['tipo']=='importar':
                # Cuarentena de copias sin registrar; nunca eliminar la fuente externa.
                quarantine=self.path(self.work_dir(work)/'recuperados');quarantine.mkdir(exist_ok=True)
                for key in ('original','copia'):
                    path=self.path(info[key])
                    if path.exists():self.move_file(path,quarantine/(uuid.uuid4().hex+path.suffix))
            else:
                row=self.file(op['archivo_id']);expected=self.path(row['ruta'])
                if expected.exists() and digest(expected)==row['hash_actual']:
                    if op['tipo'] in ('renombrar','organizar'):
                        other=self.path(info['despues'] if op['tipo']=='renombrar' else info['target'])
                        # Interrupción entre link y unlink: el destino es otro enlace al MISMO archivo.
                        if other!=expected and other.exists() and os.path.samefile(str(other),str(expected)):
                            other.unlink()
                else:
                    if op['tipo'] in ('editar','restaurar original'):
                        backup=self.path(info['respaldo'])
                        if not backup.exists() or digest(backup)!=row['hash_actual']:raise ValueError('No se puede recuperar automáticamente. Conserva la carpeta y revisa el registro '+str(op['id']))
                        temp=expected.with_name('.recover_'+uuid.uuid4().hex+'.tmp');shutil.copy2(str(backup),str(temp));os.replace(str(temp),str(expected))
                    else:
                        other=self.path(info['despues']) if op['tipo']=='renombrar' else self.path(info['target'])
                        if expected.exists() or not other.exists() or digest(other)!=row['hash_actual']:raise ValueError('Conflicto durante recuperación. No se sobrescribieron archivos.')
                        self.move_file(other,expected)
            with self.store.db:
                self.finish(op['id'],'Recuperada sin aplicar')
                self.store.audit('operaciones_tiff',op['id'],'recuperar',op,None,'Recuperación conservadora tras interrupción')
            recovered+=1
        return recovered+self.resume_replacements(work)

    def files(self,work,order='Fecha escaneo',reverse=False):
        rows=self.store.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=? AND activo=1',(work,))
        keys={'Fecha escaneo':lambda r:(r['fecha_origen'],r['id']),'Fecha creación':lambda r:(r['creacion_origen'],r['id']),'Nombre':lambda r:portable_name(r['ruta']).casefold(),'Código':lambda r:(r['codigo'] or '',r['id'])}
        return sorted(rows,key=keys[order],reverse=reverse)

    def file(self,ident):
        rows=self.store.rows('SELECT * FROM archivos_tiff WHERE id=?',(ident,))
        if not rows:raise ValueError('Archivo inexistente.')
        return rows[0]

    def checked(self,ident):
        r=self.file(ident);self.active_work(r['trabajo_id']);p=self.path(r['ruta'])
        if not r['activo']:raise ValueError('El TIFF está retirado. Restáuralo desde Retirados antes de usarlo.')
        if not p.is_file() or digest(p)!=r['hash_actual']:raise ValueError('La copia de trabajo cambió o desapareció fuera del programa. Conserva originales y consulta el historial antes de continuar.')
        return r,p

    def invalidate(self,work):
        self.store.invalidate_inventory(work,'Cambios TIFF pendientes de organizar y validar')

    def log(self,work,ident,kind,detail):
        with self.store.db:
            return self.store.db.execute('INSERT INTO operaciones_tiff(fecha,trabajo_id,archivo_id,tipo,estado,detalle) VALUES(?,?,?,?,?,?)',(now(),work,ident,kind,'Preparada',js(detail))).lastrowid

    def finish(self,op,state):self.store.db.execute('UPDATE operaciones_tiff SET estado=? WHERE id=?',(state,op))

    def copy_new(self, source, target):
        target=self.path(target)
        # Apertura exclusiva: una colisión concurrente nunca trunca el archivo existente.
        with target.open('xb') as out, Path(source).open('rb') as inp:
            shutil.copyfileobj(inp,out,1024*1024)
            out.flush();os.fsync(out.fileno())
        shutil.copystat(str(source),str(target))

    def move_file(self, source, target):
        source=self.path(source);target=self.path(target)
        if source==target:return
        if any(p.name.casefold()==target.name.casefold() for p in target.parent.iterdir()):
            raise ValueError('Colisión de destino; no se sobrescribió: '+target.name)
        # link es atómico y falla si ya existe el destino. Ambos viven en la misma raíz.
        os.link(str(source),str(target))
        try:
            source.unlink()
        except Exception as error:
            try:
                # Solo retirar el enlace que acabamos de crear; nunca un archivo ajeno.
                if not os.path.samefile(str(source),str(target)):
                    raise OSError('El destino cambió durante el movimiento.')
                target.unlink()
            except OSError:
                raise MoveRecoveryRequired('Movimiento interrumpido. Se conservaron los archivos; usa Recuperar operación.') from error
            raise

    def import_files(self,work,paths,allow_duplicates=False,on_import=None):
        self.active_work(work);base=self.work_dir(work)
        self.path(base/'entrada').mkdir(parents=True,exist_ok=True)
        self.path(base/'originales').mkdir(exist_ok=True)
        result={'importados':0,'duplicados':0,'errores':[]}
        for source in paths:
            source=Path(source).resolve()
            try:
                if source.suffix.lower() not in ('.tif','.tiff'):raise ValueError('No es un TIFF.')
                if (self.root/'datos'/'tiff') in source.parents:raise ValueError('Selecciona escaneos externos, no copias ya gestionadas.')
                pages=len(page_info(source,True));sha=digest(source)
                if self.store.rows('SELECT id FROM archivos_tiff WHERE trabajo_id=? AND hash_original=?',(work,sha)):
                    result['duplicados']+=1
                    if not allow_duplicates:continue
                stat=source.stat();key=uuid.uuid4().hex
                original=self.path(base/'originales'/(key+source.suffix.lower()))
                # UUID además de reserva exclusiva: nunca eliminar una colisión ajena al recuperar.
                target=self.path(base/'entrada'/(key+'_'+source.name))
                op=self.log(work,None,'importar',{'fuente':str(source),'original':self.relative(original),'copia':self.relative(target)})
                try:
                    self.copy_new(source,original);self.copy_new(original,target)
                    if digest(original)!=sha or digest(target)!=sha:raise ValueError('El escaneo cambió durante la copia.')
                    with self.store.db:
                        ident=self.store.db.execute('INSERT INTO archivos_tiff(trabajo_id,ruta,original,hash_original,hash_actual,paginas,fecha_origen,creacion_origen,importado) VALUES(?,?,?,?,?,?,?,?,?)',
                            (work,self.relative(target),self.relative(original),sha,sha,pages,stat.st_mtime,stat.st_ctime,now())).lastrowid
                        from .assets import imported
                        imported(self,ident,source)
                        if on_import:on_import(ident)
                        self.invalidate(work);self.store.audit('archivos_tiff',ident,'importar',None,{'ruta':self.relative(target),'sha256':sha},'Copia verificada; escaneo original intacto');self.finish(op,'Completada')
                    result['importados']+=1
                except Exception:
                    # La operación preparada se recupera a cuarentena, sin borrar documentos.
                    raise
            except Exception as e:
                result['errores'].append(source.name+': '+str(e))
                if self.store.rows("SELECT id FROM operaciones_tiff WHERE trabajo_id=? AND estado='Preparada'",(work,)):
                    result['errores'].append('Importación detenida. Usa Recuperar operación antes de continuar.')
                    break
        return result

    @staticmethod
    def free_name(path,exclude=None):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        occupied={p.name.casefold() for p in path.parent.iterdir() if exclude is None or p.resolve()!=Path(exclude).resolve()}
        candidate=path;n=2
        while candidate.name.casefold() in occupied:
            candidate=path.with_name(path.stem+' ('+str(n)+')'+path.suffix);n+=1
        return candidate

    def code_for_name(self,name):
        match=re.fullmatch(r'((?:DP|FP|HL)-\d{2,3})(?:[ _(-].*)?\.(?:tif|tiff)',name,re.I)
        if not match:return None
        code=match[1].upper()
        return next((c for c in self.catalog() if c['codigo']==code),None)

    def rename(self,ident,name,code=None):
        row,old=self.checked(ident)
        if not name or name!=Path(name).name or any(ch in name for ch in '<>:"/\\|?*') or name.endswith((' ','.')) or len(name)>150:
            raise ValueError('Nombre inválido. Sin rutas ni caracteres especiales; máximo 150 caracteres.')
        cat=self.code_for_name(name)
        if not cat:raise ValueError('El nombre debe comenzar con un código activo, por ejemplo DP-01 (2).tif.')
        target=self.work_dir(row['trabajo_id'])/'entrada'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if any(p.name.casefold()==name.casefold() and p.resolve()!=old.resolve() for p in target.parent.iterdir()):raise ValueError('Ya existe ese nombre. No se sobrescribió ningún archivo.')
        if target.resolve()==old.resolve() and row['codigo']==cat['codigo']:return row
        op=self.log(row['trabajo_id'],ident,'renombrar',{'antes':self.relative(old),'despues':self.relative(target)})
        moved=False
        try:
            if old.resolve()!=target.resolve():self.move_file(old,target);moved=True
            with self.store.db:
                self.store.db.execute("UPDATE archivos_tiff SET ruta=?,codigo=?,estado='Entrada' WHERE id=?",(self.relative(target),cat['codigo'],ident));self.invalidate(row['trabajo_id'])
                from .assets import lifecycle
                lifecycle(self,ident,'Activo')
                self.store.audit('archivos_tiff',ident,'renombrar',row,self.file(ident),'Codificación '+cat['codigo']);self.finish(op,'Completada')
        except Exception as error:
            if getattr(error,'requires_recovery',False):raise
            if moved:self.move_file(target,old)
            with self.store.db:self.finish(op,'Fallida sin cambios')
            raise
        return self.file(ident)

    def assign(self,ident,code):
        row,old=self.checked(ident)
        if row['codigo']==code:return row
        if not any(c['codigo']==code for c in self.catalog()):raise ValueError('Código no activo.')
        base=self.work_dir(row['trabajo_id'])/'entrada'
        # Reservar también los nombres ya organizados en las otras carpetas.
        occupied={portable_name(r['ruta']).casefold() for r in self.files(row['trabajo_id']) if r['id']!=ident}
        occupied|={p.name.casefold() for p in base.iterdir() if p.resolve()!=old.resolve()}
        name=code+old.suffix.lower();n=2
        while name.casefold() in occupied:name=code+' ('+str(n)+')'+old.suffix.lower();n+=1
        return self.rename(ident,name,code)

    def save_edit(self,ident,page,ops,checkpoint=None):
        if not ops:return
        row,path=self.checked(ident);base=self.work_dir(row['trabajo_id'])/'revisiones';base.mkdir(exist_ok=True)
        revision=self.path(base/(uuid.uuid4().hex+'.tif'));temp=path.with_name('.edit_'+uuid.uuid4().hex+'.tmp')
        try:
            stream_edit(path,temp,page,ops)
            self.copy_new(path,revision)
            if digest(revision)!=row['hash_actual']:raise ValueError('No se pudo verificar el respaldo de edición.')
            op=self.log(row['trabajo_id'],ident,'editar',{'pagina':page+1,'operaciones':ops,'respaldo':self.relative(revision),'destino':row['ruta']})
            replaced=False
            try:
                sha=digest(temp);os.replace(str(temp),str(path));replaced=True
                with self.store.db:
                    self.store.db.execute('INSERT INTO revisiones_tiff(archivo_id,ruta,fecha,operacion,hash) VALUES(?,?,?,?,?)',(ident,self.relative(revision),now(),js({'pagina':page+1,'ops':ops}),row['hash_actual']))
                    self.store.db.execute('UPDATE archivos_tiff SET hash_actual=? WHERE id=?',(sha,ident));self.invalidate(row['trabajo_id'])
                    from .assets import changed
                    changed(self,ident,row,revision,'Edición de página')
                    self.store.audit('archivos_tiff',ident,'editar página',row,self.file(ident),js({'pagina':page+1,'ops':ops,'respaldo':self.relative(revision)}));self.finish(op,'Completada')
                    if checkpoint:checkpoint()
            except Exception:
                if replaced:shutil.copy2(str(revision),str(temp));os.replace(str(temp),str(path))
                with self.store.db:self.finish(op,'Fallida sin cambios')
                raise
        finally:
            if temp.exists():temp.unlink()

    def restore_original(self,ident):
        row,path=self.checked(ident);original=self.path(row['original'])
        if digest(original)!=row['hash_original']:raise ValueError('El respaldo original no coincide con su huella.')
        base=self.work_dir(row['trabajo_id'])/'revisiones';base.mkdir(exist_ok=True);revision=self.path(base/(uuid.uuid4().hex+'.tif'))
        self.copy_new(path,revision);temp=path.with_name('.restore_'+uuid.uuid4().hex+'.tmp')
        op=self.log(row['trabajo_id'],ident,'restaurar original',{'ruta':row['ruta'],'respaldo':self.relative(revision)})
        try:
            shutil.copy2(str(original),str(temp));os.replace(str(temp),str(path))
            with self.store.db:
                self.store.db.execute('INSERT INTO revisiones_tiff(archivo_id,ruta,fecha,operacion,hash) VALUES(?,?,?,?,?)',(ident,self.relative(revision),now(),'Restaurar original',row['hash_actual']))
                self.store.db.execute('UPDATE archivos_tiff SET hash_actual=? WHERE id=?',(row['hash_original'],ident));self.invalidate(row['trabajo_id'])
                from .assets import changed
                changed(self,ident,row,revision,'Restaurar original')
                for correction in self.store.rows("SELECT * FROM correcciones_tiff WHERE archivo_id=? AND estado='Página sustituida'",(ident,)):
                    self.store.db.execute("UPDATE correcciones_tiff SET estado='Pendiente',resuelto=NULL,nuevo_id=NULL WHERE id=?",(correction['id'],))
                    self.store.db.execute("UPDATE incidencias SET estado='Abierta',resuelto=NULL WHERE id=?",(correction['incidencia_id'],))
                self.store.audit('archivos_tiff',ident,'restaurar original',row,self.file(ident),'Restauración solicitada por el operador');self.finish(op,'Completada')
        except Exception:
            shutil.copy2(str(revision),str(temp));os.replace(str(temp),str(path))
            with self.store.db:self.finish(op,'Fallida sin cambios')
            raise

    def plan(self,work):
        w=self.active_work(work);rows=self.files(work);plan=[]
        if self.store.rows("SELECT s.id FROM sustituciones_tiff s JOIN correcciones_tiff c ON c.id=s.correccion_id JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? AND s.fase!='Completada'",(work,)):raise ValueError('Hay una sustitución interrumpida. Usa Recuperar operación.')
        if self.store.rows("SELECT c.id FROM correcciones_tiff c JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? AND c.estado='Pendiente'",(work,)):raise ValueError('Hay correcciones pendientes. Resuélvelas en Reescaneos antes de generar el inventario.')
        if w['fisicos'] is None:raise ValueError('Confirma primero el conteo físico para generar el reporte.')
        dest=self.work_dir(work)/w['curp']
        for row in rows:
            _,source=self.checked(row['id']);cat=self.code_for_name(source.name)
            if not cat:raise ValueError('Falta codificar: '+source.name)
            if cat['carpeta'] not in ('PERSONALES','FEDERAL'):raise ValueError('Revisa la carpeta del código '+cat['codigo'])
            target=self.path(dest/cat['carpeta']/source.name)
            if target.parent.exists() and any(p.name.casefold()==target.name.casefold() and p.resolve()!=source.resolve() for p in target.parent.iterdir()):raise ValueError('Colisión en destino: '+target.name)
            measured=len(page_info(source,True))
            if measured!=row['paginas']:raise ValueError('Las páginas del TIFF no coinciden con su registro.')
            plan.append({'id':row['id'],'source':self.relative(source),'target':self.relative(target),'carpeta':cat['carpeta'],'codigo':cat['codigo'],'paginas':row['paginas']})
        targets=[x['target'].casefold() for x in plan]
        if len(targets)!=len(set(targets)):raise ValueError('Dos archivos comparten nombre de destino.')
        # No ocultar archivos añadidos por fuera del módulo en carpetas de destino.
        known={str(self.path(r['ruta'])).casefold() for r in rows}
        if dest.exists():
            unknown=[p for p in dest.rglob('*') if p.is_file() and p.suffix.lower() in ('.tif','.tiff') and str(p.resolve()).casefold() not in known]
            if unknown:raise ValueError('Hay TIFF externos no registrados en el destino. Revisa: '+unknown[0].name)
        return plan

    def organize(self,work):
        with self.store.db:self.invalidate(work)
        plan=self.plan(work);w=self.active_work(work);dest=self.work_dir(work)/w['curp'];moved=[]
        for folder in ('PERSONALES','FEDERAL'):self.path(dest/folder).mkdir(parents=True,exist_ok=True)
        for item in plan:
            old=self.path(item['source']);target=self.path(item['target']);row=self.file(item['id'])
            op=self.log(work,row['id'],'organizar',item)
            changed=old.resolve()!=target.resolve();did_move=False
            try:
                if changed:self.move_file(old,target);did_move=True
                with self.store.db:
                    self.store.db.execute("UPDATE archivos_tiff SET ruta=?,codigo=?,estado='Organizado' WHERE id=?",(self.relative(target),item['codigo'],row['id']))
                    from .assets import lifecycle
                    lifecycle(self,row['id'],'Activo')
                    self.store.audit('archivos_tiff',row['id'],'organizar',row,self.file(row['id']),'Organización por catálogo activo');self.finish(op,'Completada')
                if changed:moved.append(item)
            except Exception as error:
                if getattr(error,'requires_recovery',False):raise
                if did_move:self.move_file(target,old)
                with self.store.db:self.finish(op,'Fallida sin cambios')
                raise ValueError('La organización se detuvo. Los archivos ya organizados siguen registrados. Corrige el problema y vuelve a previsualizar.')
        payload=self.metrics(work,plan,moved,dest)
        stamp=dt.datetime.now().isoformat(timespec='seconds');unique=uuid.uuid4().hex
        out=self.store.workspace.reports/('codificacion_'+unique);out.mkdir(parents=True)
        self.store.csv_write(out/'inventario.csv',[dict(payload,FOLIO=self.store.one('folios',w['folio_id'])['numero'],LEGAJO=w['legajo'],TRABAJO_ID=work,ALCANCE='Legajo',ID_EJECUCION=unique)])
        self.store.csv_write(out/'archivos.csv',[{'id':i['id'],'codigo':i['codigo'],'carpeta':i['carpeta'],'paginas':i['paginas'],'ruta':i['target']} for i in plan])
        with self.store.db:
            self.store.db.execute('INSERT INTO ejecuciones(huella,curp,fecha,payload,trabajo_id,ambito,valido,observacion) VALUES(?,?,?,?,?,?,?,?)',(unique,w['curp'],stamp,js(payload),work,'Legajo',1,'Generado por módulo de codificación '+VERSION+'; trabajo '+str(work)))
            self.store.db.execute('DELETE FROM inventario_pendiente WHERE trabajo_id=?',(work,))
            self.store.db.execute('UPDATE trabajos SET carpetas=1 WHERE id=?',(work,))
            self.store.audit('trabajos',work,'inventario TIFF',None,{'archivos':len(plan),'reporte':str(out)},'Archivos verificados y separados por trabajo/legajo')
        from .delivery import Deliveries
        try:
            if plan:Deliveries(self.store).prepare(work)
            else:Deliveries(self.store).validate(work)
        except Exception:
            with self.store.db:self.invalidate(work)
            raise
        return out

    def metrics(self,work,items,moved,dest):
        # Esquema explícito idéntico en métricas al original, origen APP identificado sin fingir ejecución BAT.
        p={'VERSION_BAT':'APP_'+VERSION,'VERSION_REGLA':'1P_INDIVIDUAL_2P_MULTI','FECHA':dt.datetime.now().strftime('%d/%m/%Y'),'HORA':dt.datetime.now().strftime('%H:%M:%S')}
        w=self.store.one('trabajos',work);p.update(CURP=w['curp'],DIGITALIZADOR=self.store.operador,HOJAS_FISICAS=w['fisicos'])
        for group,rows in [('MOV',moved),('INV',items)]:
            for suffix,folder in [('P','PERSONALES'),('F','FEDERAL'),('TOTAL',None)]:
                subset=[r for r in rows if folder is None or r['carpeta']==folder];prefix=group+'_'+suffix
                ind=sum(r['paginas']==1 for r in subset);multi=sum(r['paginas']>=2 for r in subset);pages=sum(r['paginas'] for r in subset)
                p[prefix+('_ARCHIVOS_CARPETAS' if prefix=='INV_TOTAL' else '_ARCHIVOS')]=len(subset)
                for key,val in [('INDIVIDUALES',ind),('MULTI',multi),('NO_CLASIFICADOS',0),('PAG_INDIVIDUALES',ind),('PAG_MULTI',pages-ind)]:p[prefix+'_'+key]=val
                p[prefix+('_PAG_CARPETAS' if prefix=='INV_TOTAL' else '_PAG_TOTAL')]=pages
        p.update(INV_P_DP=sum(r['codigo'].startswith('DP') and r['carpeta']=='PERSONALES' for r in items),INV_P_FP=sum(r['codigo'].startswith('FP') and r['carpeta']=='PERSONALES' for r in items),INV_F_HL=sum(r['codigo'].startswith('HL') and r['carpeta']=='FEDERAL' for r in items),TOTAL_DIGITALES_TIFF=len(items),TIFF_RAIZ_CURP=0,PAG_CONOCIDAS_RAIZ=0,TIFF_NO_LEGIBLES_RAIZ=0,TOTAL_PAG_DIGITALES_CONOCIDAS=sum(r['paginas'] for r in items),ESTADO_CONTEO_PAGINAS='COMPLETO',CONFLICTOS=0,ERRORES_MOVIMIENTO=0,ERRORES_LECTURA_TIFF=0,TIFF_SUELTOS_ESCANER=0,TIFF_NO_ESPERADOS_CURP=0,RESULTADO='OK',RUTA_EXPEDIENTE=str(dest),APUNTE_FOLDER='Generado por aplicación; inventario limitado a las copias gestionadas de este trabajo.')
        return p
