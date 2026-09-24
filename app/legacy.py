"""Carpetas históricas: diagnóstico de solo lectura, registro externo y adopción."""
import re
import uuid
from pathlib import Path
from .core import now,js
from .backup import sha256
from .coding import CodingService,page_info
from .manifests import plain_path,walk_plain
from .delivery import content_hash
from .operations import Operations


class LegacyImport:
    def __init__(self,store,role='Responsable'):
        self.s=store;self.db=store.db;self.ops=Operations(store,role)

    def preflight(self,work,source):
        w=self.s.one('trabajos',work);root=Path(source).resolve()
        if not root.is_dir():raise ValueError('Selecciona una carpeta CURP existente.')
        if root==self.s.workspace.root or self.s.workspace.root in root.parents:
            raise ValueError('Selecciona una fuente externa, no el propio almacenamiento gestionado.')
        catalog={r['codigo']:r for r in self.s.rows("SELECT * FROM catalogos WHERE tipo='documento'")}
        records=[];issues=[];names={};hashes={};byfolder={};bycode={};size=0;pages=0;individual=0;multi=0;unreadable=[];non_tiff=[]
        def issue(level,rule,message,path=''):issues.append({'severidad':level,'regla':rule,'mensaje':message,'ruta':path})
        if root.name.strip().upper()!=w['curp'].strip().upper():issue('REQUIERE REVISIÓN','curp','El nombre de la carpeta no coincide con la CURP seleccionada')
        for folder in ('PERSONALES','FEDERAL'):
            if not (root/folder).is_dir():issue('ADVERTENCIA','carpeta_ausente','No existe '+folder+'; puede ser una carpeta sin documentos')
        for p in walk_plain(root):
            rel=p.relative_to(root).as_posix()
            try:p=plain_path(root,rel)
            except ValueError as error:issue('BLOQUEANTE','enlace',str(error),rel);continue
            if p.is_dir():
                if len(p.relative_to(root).parts)>1 or p.name not in ('PERSONALES','FEDERAL'):
                    issue('REQUIERE REVISIÓN','subcarpeta','Subcarpeta no reconocida',rel)
                continue
            if not p.is_file():continue
            entry={'ruta':rel,'nombre':p.name,'bytes':p.stat().st_size,'sha256':sha256(p),'tiff':p.suffix.lower() in ('.tif','.tiff'),'paginas':None,'codigo':None,'carpeta':p.parent.name}
            records.append(entry);size+=entry['bytes'];names.setdefault(p.name.casefold(),[]).append(entry);hashes.setdefault(entry['sha256'],[]).append(rel)
            if not entry['tiff']:
                non_tiff.append(rel);issue('ADVERTENCIA','no_tiff','Archivo ajeno al inventario TIFF; no será adoptado',rel);continue
            if p.parent==root:issue('REQUIERE REVISIÓN','raiz','TIFF suelto en la raíz CURP',rel)
            match=re.match(r'^((?:DP|FP|HL)-(\d{1,3}))(?=[ _(.]|\.)',p.name,re.I)
            if match:
                prefix,number=match[1].upper().split('-');code=prefix+'-'+number.zfill(2);entry['codigo']=code
                cat=catalog.get(code)
                if not cat:issue('REQUIERE REVISIÓN','codigo_desconocido','Código inexistente en catálogo: '+code,rel)
                elif not cat['activo']:issue('REQUIERE REVISIÓN','codigo_inactivo','Código inactivo: '+code,rel)
                elif p.parent.name!=cat['carpeta']:issue('REQUIERE REVISIÓN','ubicacion','Carpeta esperada según catálogo: '+cat['carpeta'],rel)
                bycode[code]=bycode.get(code,0)+1
            else:issue('REQUIERE REVISIÓN','nombre','Nombre sin código documental reconocible',rel)
            try:
                count=len(page_info(p,True));entry['paginas']=count;entry['modalidad']='Individual' if count==1 else 'Multi'
                pages+=count;individual+=count==1;multi+=count>=2
            except (ValueError,OSError) as error:
                unreadable.append(rel);issue('BLOQUEANTE','ilegible',str(error),rel)
            byfolder[p.parent.name]=byfolder.get(p.parent.name,0)+1
        collisions=[]
        for name,entries in names.items():
            if len(entries)>1:
                paths=[e['ruta'] for e in entries];collisions.append(paths)
                different=len({e['sha256'] for e in entries})>1
                issue('REQUIERE REVISIÓN' if different else 'ADVERTENCIA','colision','Mismo nombre con '+('contenido diferente' if different else 'contenido idéntico')+': '+', '.join(paths))
        duplicates=[paths for paths in hashes.values() if len(paths)>1]
        for paths in duplicates:issue('ADVERTENCIA','duplicado_exacto','SHA-256 idéntico; no se elimina ninguna copia: '+', '.join(paths))
        tiffs=[r for r in records if r['tiff']]
        if not tiffs:issue('REQUIERE REVISIÓN','vacio','No se encontraron TIFF')
        levels={i['severidad'] for i in issues}
        result='BLOQUEANTE' if 'BLOQUEANTE' in levels else 'REQUIERE REVISIÓN' if 'REQUIERE REVISIÓN' in levels else 'OK con advertencias' if levels else 'OK'
        report={'trabajo_id':work,'expediente_id':w['expediente_id'],'origen':str(root),'resultado':result,'pasa':result in ('OK','OK con advertencias'),
                'archivos':records,'problemas':issues,'duplicados_exactos':duplicates,'colisiones':collisions,'no_tiff':non_tiff,'ilegibles':unreadable,
                'totales':{'archivos':len(records),'tiff':len(tiffs),'paginas_conocidas':pages,'paginas_desconocidas':len(unreadable),'individuales':individual,'multi':multi,'bytes':size,'por_carpeta':byfolder,'por_codigo':bycode},
                'acciones_recomendadas':sorted({i['mensaje'] for i in issues if i['severidad']!='ADVERTENCIA'})}
        report['preflight_hash']=content_hash(report)
        return report

    def register(self,work,report,adopt=False):
        self.ops.permit('legado')
        current=self.preflight(work,report['origen'])
        if current['preflight_hash']!=report['preflight_hash']:raise ValueError('La fuente o el catálogo cambiaron después del diagnóstico. Analiza de nuevo antes de confirmar.')
        if adopt and not current['pasa']:raise ValueError('La carpeta no pasa preflight. Conserva el origen y revisa los problemas antes de adoptar.')
        mode='Adoptar' if adopt else 'Analizar en sitio'
        previous=self.s.rows("SELECT * FROM importaciones_legado WHERE trabajo_id=? AND origen=? AND modo='Adoptar' AND estado!='Completada' ORDER BY rowid DESC LIMIT 1",(work,report['origen'])) if adopt else []
        if previous:
            ident=previous[0]['id']
            import json
            if json.loads(previous[0]['informe'])['preflight_hash']!=report['preflight_hash']:
                raise ValueError('Hay una adopción parcial de otra versión de la fuente. Revisa sus archivos antes de crear otra.')
        else:
            ident=uuid.uuid4().hex
            with self.db:self.db.execute('INSERT INTO importaciones_legado VALUES(?,?,?,?,?,?,?,?)',(ident,work,report['origen'],mode,now(),self.s.operador,'Preparando' if adopt else 'Externa / no gestionada',js(report)))
        if not adopt:return ident
        coder=CodingService(self.s)
        try:
            for entry in report['archivos']:
                if not entry['tiff']:continue
                found=self.s.rows('SELECT * FROM importacion_items WHERE importacion_id=? AND ruta_origen=?',(ident,entry['ruta']))
                if found:archivo=found[0]['archivo_id']
                else:
                    def registered(archivo):
                        self.db.execute('INSERT INTO importacion_items VALUES(?,?,?,?)',(ident,entry['ruta'],archivo,entry['sha256']))
                    result=coder.import_files(work,[plain_path(Path(report['origen']),entry['ruta'])],allow_duplicates=True,on_import=registered)
                    if result['errores']:raise ValueError('; '.join(result['errores']))
                    found=self.s.rows('SELECT * FROM importacion_items WHERE importacion_id=? AND ruta_origen=?',(ident,entry['ruta']))
                    if not found:raise ValueError('No se registró la copia adoptada.')
                    archivo=found[0]['archivo_id']
                row=coder.file(archivo)
                if sha256(coder.path(row['original']))!=entry['sha256']:raise ValueError('Original adoptado alterado; revisión necesaria.')
                coder.assign(archivo,entry['codigo'])
            if self.preflight(work,report['origen'])['preflight_hash']!=report['preflight_hash']:raise ValueError('La fuente cambió durante la adopción. No se confirmó como completa.')
            with self.db:
                self.db.execute("UPDATE importaciones_legado SET estado='Completada' WHERE id=?",(ident,))
                self.ops.event(work,'Adopción histórica','Origen conservado; copias y hashes verificados: '+ident)
            return ident
        except BaseException:
            with self.db:self.db.execute("UPDATE importaciones_legado SET estado='Incompleta' WHERE id=?",(ident,))
            raise
