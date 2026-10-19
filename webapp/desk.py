"""DTO de la estación TIFF y miniaturas acotadas, sin rutas físicas en el cliente."""
from collections import OrderedDict
import io
from pathlib import Path
from app.coding import CodingService, render_page, page_info
from app.integrations import Integrations

THUMBNAILS = OrderedDict()
THUMB_LIMIT = 64


def state(store, work):
    coder = CodingService(store)
    current = Integrations(store).current(work)
    context = Integrations(store).context(work)
    w = store.one('trabajos',work)
    rows = store.rows('''SELECT a.*,v.bytes AS file_bytes,EXISTS(SELECT 1 FROM procedencia_paginas p WHERE p.archivo_id=a.id) AS derived
        FROM archivos_tiff a LEFT JOIN versiones_archivo v ON v.id=a.version_id WHERE trabajo_id=? ORDER BY a.id''', (work,))
    files = [dict(id=r['id'],name=(r['nombre_origen'] or Path(r['ruta']).name) if not r['codigo'] else Path(r['ruta']).name,code=r['codigo'] or '',pages=r['paginas'],
                  active=bool(r['activo']),status=r['estado'],imported=r['importado'],date=r['fecha_origen'],
                  integration=r['integracion_id'],version=r['hash_actual'],version_id=r['version_id'],bytes=r['file_bytes'],
                  source_name=r['nombre_origen'],derived=bool(r['derived'])) for r in rows]
    catalog = [dict(id=r['id'],code=r['codigo'],title=r['titulo'],description=r.get('descripcion') or r.get('carpeta') or '',
                    combo=r['combinacion'],number=r['numero'],sequence=r['secuencia']) for r in coder.catalog()]
    return dict(work=work,context=context,files=files,catalog=catalog,integration=current['id'],
                closed=w['estado']=='Expediente cerrado' or not w['activo'])


def preview(store, work, ident, page=0, original=False, thumbnail=False, revision=None,ops=(),full=False):
    coder = CodingService(store)
    row = coder.file(ident)
    if row['trabajo_id'] != work: raise ValueError('TIFF de otro expediente.')
    path = coder.path(row['original'] if original else row['ruta'])
    if revision:
        versions = store.rows('SELECT ruta FROM revisiones_tiff WHERE id=? AND archivo_id=?', (revision,ident))
        if not versions: raise ValueError('Versión ajena al documento.')
        path = coder.path(versions[0]['ruta'])
    stamp = path.stat()
    key = (str(store.workspace.root),ident,str(path),stamp.st_size,stamp.st_mtime_ns,row['hash_actual'])
    if thumbnail and key in THUMBNAILS:
        THUMBNAILS.move_to_end(key)
        return THUMBNAILS[key]
    if page < 0: raise ValueError('Página fuera del documento.')
    frame = render_page(path,page,ops)
    try:
        if thumbnail or not full:frame.thumbnail((200,240) if thumbnail else (1800,1800))
        out = io.BytesIO()
        with frame.convert('RGB') as rgb: rgb.save(out,format='PNG')
        result = out.getvalue()
    finally: frame.close()
    if thumbnail:
        THUMBNAILS[key] = result
        while len(THUMBNAILS)>THUMB_LIMIT: THUMBNAILS.popitem(last=False)
    return result


def history(store,work,ident,page,original=False,revision=None):
    coder = CodingService(store)
    row = coder.file(ident)
    if row['trabajo_id'] != work: raise ValueError('TIFF ajeno.')
    path=coder.path(row['original'] if original else row['ruta'])
    if revision:
        matches=store.rows('SELECT ruta FROM revisiones_tiff WHERE id=? AND archivo_id=?',(revision,ident))
        if not matches:raise ValueError('Revisión ajena.')
        path=coder.path(matches[0]['ruta'])
    dimensions = page_info(path)
    if not 0<=page<len(dimensions): raise ValueError('Página inexistente.')
    versions = store.rows('SELECT id,fecha,operacion FROM revisiones_tiff WHERE archivo_id=? ORDER BY id DESC',(ident,))
    origins=store.rows('SELECT pagina,archivo_fuente_id,version_fuente_id,pagina_fuente FROM procedencia_paginas WHERE archivo_id=? ORDER BY pagina',(ident,))
    return dict(width=dimensions[page]['size'][0], height=dimensions[page]['size'][1], versions=versions,origins=origins)


def edits(values):
    import math
    operations=values.get('operations')
    if not isinstance(operations,list) or not 1<=len(operations)<=40: raise ValueError('De 1 a 40 ajustes por página.')
    result=[]
    for op in operations:
        if not isinstance(op,list) or not op: raise ValueError('Ajuste inválido.')
        if op[0]=='rotate' and len(op)==2:
            angle=float(op[1])
            if not math.isfinite(angle) or not -180<=angle<=180: raise ValueError('Ángulo fuera de −180 a 180.')
            result.append(('rotate',angle))
        elif op[0]=='crop' and len(op)==5 and all(type(n) is int and n>=0 for n in op[1:]): result.append(tuple(op))
        else: raise ValueError('Ajuste no permitido.')
    return result
