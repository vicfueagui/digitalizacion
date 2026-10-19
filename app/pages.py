"""Derivación TIFF verificada: preparar archivos antes de activar identidades.

Las fuentes nunca se mueven ni se reescriben. Todas las altas, procedencias,
retiros lógicos e invalidación se confirman juntas en SQLite. Un corte anterior
al commit conserva las fuentes activas y deja un diario recuperable. Los
resultados incompletos quedan fuera del inventario, conservados como evidencia.
"""
import hashlib
import io
import json
import os
import re
import uuid
from pathlib import Path
from .coding import digest, page_info, pillow
from .core import now, js
from .integrations import Integrations

MAX_PAGES = 2000
MAX_SOURCES = 500


def ranges(text, count):
    """Lista ordenada 1-based, sin repeticiones ni intervalos descendentes."""
    if not isinstance(text,str) or not text.strip(): raise ValueError('Indica las páginas.')
    pages=[]
    for part in text.replace('–','-').split(','):
        match=re.fullmatch(r'\s*(\d+)(?:\s*-\s*(\d+))?\s*',part)
        if not match: raise ValueError('Usa páginas o rangos: 1,3-5.')
        first=int(match[1]);last=int(match[2] or first)
        if not 1<=first<=last<=count: raise ValueError('Rango fuera del documento o descendente.')
        pages.extend(range(first,last+1))
    if len(set(pages))!=len(pages): raise ValueError('Una página aparece más de una vez.')
    return pages


def signature(plan):
    return hashlib.sha256(js(plan).encode('utf8')).hexdigest()


def write_pages(target, ordered):
    """Una página en memoria; no convertir modos, dimensiones ni DPI."""
    Image,Tiff=pillow()
    class Writer(Tiff.AppendingTiffWriter):
        def close(self):
            if getattr(self,'_closed_once',False): return
            try:
                if hasattr(self,'f') and not self.f.closed: super().close()
            finally:
                self._closed_once=True
                if isinstance(self,io.BytesIO): io.BytesIO.close(self)
    with Writer(str(target),True) as writer:
        for source,index in ordered:
            with Image.open(str(source)) as original:
                original.seek(index)
                tags={k:original.tag_v2[k] for k in (269,270,271,272,285,306,315,33432) if k in original.tag_v2}
                with original.copy() as frame:
                    kwargs=dict(compression='tiff_deflate',dpi=original.info.get('dpi',(300,300)),tiffinfo=tags)
                    if original.info.get('icc_profile'): kwargs['icc_profile']=original.info['icc_profile']
                    frame.save(writer,format='TIFF',**kwargs)
                    writer.newFrame()
    with Path(target).open('r+b') as stream: os.fsync(stream.fileno())
    verify_pages(target,ordered)


def verify_pages(target,ordered):
    Image,_=pillow()
    if len(page_info(target,True))!=len(ordered): raise ValueError('El resultado perdió páginas.')
    with Image.open(str(target)) as result:
        for position,(source,index) in enumerate(ordered):
            result.seek(position)
            with Image.open(str(source)) as original:
                original.seek(index)
                # copy() aplica la orientación TIFF igual que el visor existente.
                with original.copy() as expected:
                    if (result.size,result.mode,result.tobytes())!=(expected.size,expected.mode,expected.tobytes()):
                        raise ValueError('Cambió el contenido u orden de páginas; no se activa la operación.')
                    if expected.mode=='P' and result.getpalette()!=expected.getpalette():
                        raise ValueError('Cambió la paleta de color; no se activa la operación.')
                    a=original.info.get('dpi',(300,300));b=result.info.get('dpi',(300,300))
                    if any(abs(float(x)-float(y))>0.01 for x,y in zip(a,b)):
                        raise ValueError('No se pudo conservar el DPI; no se activa la operación.')
                    if original.info.get('icc_profile')!=result.info.get('icc_profile'):
                        raise ValueError('No se pudo conservar el perfil de color.')


class PageOperations:
    def __init__(self,coder): self.c=coder;self.s=coder.store

    def plan(self,work,spec):
        if not isinstance(spec,dict):raise ValueError('Plan de páginas inválido.')
        self.c.active_work(work)
        kind=spec.get('kind');ids=spec.get('ids',[])
        if not isinstance(ids,list) or not 1<=len(ids)<=MAX_SOURCES: raise ValueError('Selecciona entre 1 y 500 TIFF.')
        ids=[int(i) for i in ids]
        if len(set(ids))!=len(ids): raise ValueError('TIFF repetido en la selección.')
        if kind not in ('split','extract','merge'): raise ValueError('Operación de páginas desconocida.')
        if (kind=='merge' and len(ids)<2) or (kind!='merge' and len(ids)!=1): raise ValueError('Cantidad de TIFF incompatible con la operación.')
        rows=[];sources=[]
        for ident in ids:
            row,path=self.c.checked(ident)
            if row['trabajo_id']!=work: raise ValueError('No se mezclan expedientes, legajos o ciclos.')
            infos=page_info(path,True)
            if len(infos)!=row['paginas']: raise ValueError('Metadatos TIFF inconsistentes.')
            rows.append(row)
            sources.append(dict(id=ident,version=row['version_id'],hash=row['hash_actual'],pages=row['paginas'],
                                name=Path(row['ruta']).name,code=row['codigo'],integration=row['integracion_id']))
        if len({r['integracion_id'] for r in rows})!=1: raise ValueError('No se mezclan integraciones distintas.')
        current=Integrations(self.s).current(work)
        if rows[0]['integracion_id']!=current['id']: raise ValueError('Estas páginas pertenecen a una integración histórica; trabaja en la integración actual.')
        total=sum(r['paginas'] for r in rows)
        if total>MAX_PAGES: raise ValueError('Máximo 2000 páginas por operación en este equipo.')
        disposition=spec.get('disposition')
        if disposition not in ('keep','replace'): raise ValueError('Elige conservar fuentes o sustituirlas mediante retiro trazable.')
        outputs=[];retire=[]
        def output(label,pages):
            outputs.append(dict(label=label,pages=pages))
        if kind=='merge':
            overrides=spec.get('merge_pages',{})
            if not isinstance(overrides,dict) or set(overrides)-{str(i) for i in ids}:raise ValueError('Orden de páginas ajeno a la selección.')
            ordered=[]
            for row in rows:
                sequence=ranges(overrides[str(row['id'])],row['paginas']) if str(row['id']) in overrides else list(range(1,row['paginas']+1))
                if sorted(sequence)!=list(range(1,row['paginas']+1)):raise ValueError('La unión incluye todas las páginas de cada fuente, exactamente una vez. Para seleccionar solo algunas utiliza Extraer.')
                ordered.extend([[row['id'],p] for p in sequence])
            output('Unión',ordered)
            if disposition=='replace': retire=ids[:]
        else:
            row=rows[0];n=row['paginas'];mode=spec.get('mode');groups=[]
            if kind=='extract':
                selected=ranges(spec.get('ranges',''),n)
                groups=[[p] for p in selected] if mode=='individual' else [selected]
                if mode not in ('individual','multi'): raise ValueError('Elige salida individual o multipágina.')
                if disposition=='replace':
                    remaining=[p for p in range(1,n+1) if p not in selected]
                    if remaining: output('Remanente de la fuente',[[row['id'],p] for p in remaining])
            elif mode=='each': groups=[[p] for p in range(1,n+1)]
            elif mode in ('before','after'):
                page=int(spec.get('page',0));cut=page-1 if mode=='before' else page
                if not 1<=page<=n or not 0<cut<n: raise ValueError('El corte debe dejar páginas a ambos lados.')
                groups=[list(range(1,cut+1)),list(range(cut+1,n+1))]
            elif mode=='cuts':
                cuts=sorted(ranges(spec.get('ranges',''),n))
                if cuts[-1]>=n: raise ValueError('No se puede cortar después de la última página.')
                start=1
                for end in cuts+[n]: groups.append(list(range(start,end+1)));start=end+1
            elif mode=='groups':
                size=int(spec.get('size',0))
                if not 1<=size<=n: raise ValueError('Tamaño de grupo fuera de rango.')
                groups=[list(range(p,min(p+size,n+1))) for p in range(1,n+1,size)]
            elif mode=='ranges': groups=[ranges(s,n) for s in str(spec.get('ranges','')).split(';')]
            else: raise ValueError('Forma de división desconocida.')
            if kind=='split' and sorted(p for group in groups for p in group)!=list(range(1,n+1)):
                raise ValueError('La división completa requiere cada página exactamente una vez.')
            for pos,group in enumerate(groups,1): output('Resultado '+str(pos),[[row['id'],p] for p in group])
            if disposition=='replace': retire=ids[:]
        code=None
        if spec.get('keep_code') is True:
            codes={r['codigo'] for r in rows}
            if len(codes)!=1 or not next(iter(codes)) or not any(c['codigo']==next(iter(codes)) for c in self.c.catalog()):
                raise ValueError('Solo se conserva un mismo código activo, confirmado expresamente.')
            code=next(iter(codes))
        after=total+sum(len(o['pages']) for o in outputs)-sum(r['paginas'] for r in rows if r['id'] in retire)
        return dict(kind=kind,work=work,integration=current['id'],sources=sources,outputs=outputs,retire=retire,
                    code=code,before_pages=total,after_pages=after,extra_pages=after-total,
                    notice='Los derivados no son nuevos escaneos. Las hojas físicas y las incidencias no cambian. El remanente, si existe, recibe identidad nueva. Se conservan fuentes e historial.')

    def run(self,work,spec,expected,reason,checkpoint=None):
        if not str(reason).strip(): raise ValueError('Registra el motivo de la derivación.')
        plan=self.plan(work,spec)
        if signature(plan)!=expected: raise ValueError('Las versiones o el plan cambiaron. Revisa una vista previa nueva.')
        key=uuid.uuid4().hex;folder=self.c.work_dir(work)/'derivados'/key
        folder.mkdir(parents=True,exist_ok=False)
        details=dict(plan=plan,folder=self.c.relative(folder),reason=reason,files=[],results=[])
        op=self.c.log(work,None,'paginas',details)
        checkpoint=checkpoint or (lambda stage:None)
        checkpoint('prepared')
        sources={r['id']:self.c.file(r['id']) for r in plan['sources']}
        # Ninguna alta/retirada ocurre hasta verificar TODOS los resultados.
        for pos,out in enumerate(plan['outputs'],1):
            original=folder/('derivado-%04d.tif'%pos)
            working=folder/((plan['code'] or 'DERIVADO')+'_'+key[:8]+'_%04d.tif'%pos)
            ordered=[(self.c.path(sources[i]['ruta']),p-1) for i,p in out['pages']]
            write_pages(original,ordered)
            self.c.copy_new(original,working)
            sha=digest(original)
            if digest(working)!=sha: raise ValueError('Copia derivada no verificada.')
            details['files'].append(dict(original=self.c.relative(original),working=self.c.relative(working),sha=sha))
            with self.s.db: self.s.db.execute('UPDATE operaciones_tiff SET detalle=? WHERE id=?',(js(details),op))
            checkpoint('file-'+str(pos))
        for source in plan['sources']:
            row=self.c.file(source['id'])
            if row['version_id']!=source['version'] or digest(self.c.path(row['ruta']))!=source['hash']:
                raise ValueError('Cambió una fuente mientras se preparaban los resultados. Recupera la operación.')
        checkpoint('verified')
        for files in details['files']:
            if any(digest(self.c.path(files[key]))!=files['sha'] for key in ('original','working')):
                raise ValueError('Un resultado preparado cambió. Las fuentes siguen activas; recupera la operación.')
        from .assets import create_document,register_version,lifecycle
        # El commit incluye el diario: nunca habrá fuentes retiradas sin salidas activas.
        with self.s.db:
            for out,files in zip(plan['outputs'],details['files']):
                ident=self.s.db.execute('''INSERT INTO archivos_tiff(trabajo_id,ruta,original,hash_original,hash_actual,paginas,
                    codigo,fecha_origen,creacion_origen,importado,integracion_id,integracion_ingreso_id,nombre_origen)
                    VALUES(?,?,?,?,?,?,?,0,0,?,?,?,?)''',
                    (work,files['working'],files['original'],files['sha'],files['sha'],len(out['pages']),plan['code'],now(),
                     plan['integration'],plan['integration'],Path(files['working']).name)).lastrowid
                document=create_document(self.s,work,Path(files['working']).name)
                version=register_version(self.s,document,files['original'],files['sha'],self.c.path(files['original']).stat().st_size,
                                         len(out['pages']),'Derivación de páginas verificada',source=ident)
                self.s.db.execute('UPDATE archivos_tiff SET documento_id=?,version_id=? WHERE id=?',(document,version,ident))
                for index,(source,page) in enumerate(out['pages'],1):
                    self.s.db.execute('INSERT INTO procedencia_paginas VALUES(?,?,?,?,?,?)',
                                     (ident,index,source,sources[source]['version_id'],page,op))
                details['results'].append(ident)
                checkpoint('registered-'+str(len(details['results'])))
            for ident in plan['retire']:
                self.s.db.execute("UPDATE archivos_tiff SET activo=0,estado='Retirado' WHERE id=?",(ident,))
                lifecycle(self.c,ident,'Retirado')
                self.s.audit('archivos_tiff',ident,'retirar por derivación',sources[ident],self.c.file(ident),reason)
            checkpoint('retired')
            self.c.invalidate(work)
            self.s.audit('operaciones_tiff',op,'derivar páginas',plan,details['results'],reason)
            self.s.db.execute('UPDATE operaciones_tiff SET detalle=? WHERE id=?',(js(details),op))
            self.c.finish(op,'Completada')
            checkpoint('before-commit')
        checkpoint('committed')
        return dict(message='Páginas verificadas. {} TIFF nuevos; {} fuentes retiradas de forma trazable.'.format(len(details['results']),len(plan['retire'])),
                    ids=details['results'],operation=op)

    def recover(self,op):
        details=json.loads(op['detalle'])
        # No se borran ni sobreescriben archivos: conservar preparación en cuarentena lógica.
        for source in details['plan']['sources']:
            row=self.c.file(source['id'])
            if not row['activo'] or row['version_id']!=source['version'] or digest(self.c.path(row['ruta']))!=source['hash']:
                raise ValueError('Fuente inesperada. Conserva la preparación para revisión; no se modificó ningún archivo.')
        if self.s.rows('SELECT 1 FROM procedencia_paginas WHERE operacion_id=?',(op['id'],)):
            raise ValueError('Diario incoherente: hay resultados registrados. Requiere revisión.')
        with self.s.db:
            self.c.finish(op['id'],'Recuperada sin aplicar')
            self.s.audit('operaciones_tiff',op['id'],'recuperar derivación',None,dict(folder=details['folder']),
                         'Fuentes intactas; preparación conservada fuera del inventario. Revisar antes de una nueva solicitud.')
