"""Adaptador de presentación. Las decisiones siguen en los servicios probados."""
import datetime as dt
import io
import json
from pathlib import Path
from app.core import STATES, integer
from app.operations import Operations, KANBAN
from app.integrations import Integrations
from app.coding import CodingService, render_page
from app.delivery import Deliveries
from app.review import Reviews
from app.dashboard import Dashboard, STAGES
from app.analytics import Cube
from app.batch_tiff import BatchTiff
from app.reception import Reception


PERMISSIONS = {
    'folio': 'recepcion', 'expected': 'recepcion', 'receipt': 'recepcion', 'accept': 'recepcion', 'difference': 'recepcion',
    'legajos': 'recepcion', 'import_list': 'recepcion', 'assign': 'asignacion', 'integration': 'asignacion',
    'count': 'proceso', 'confirm_count': 'proceso', 'edit_count': 'proceso', 'state': 'proceso',
    'card': 'tarjeta', 'custody': 'custodia', 'upload': 'proceso', 'code': 'proceso', 'edit': 'proceso',
    'rename': 'proceso', 'original': 'corregir', 'batch': 'corregir', 'batch_code': 'proceso', 'recover': 'corregir',
    'correction': 'corregir', 'replace': 'corregir', 'resolve_correction': 'corregir',
    'deliver': 'entrega', 'validate': 'entrega', 'begin_review': 'revision', 'approve': 'aprobar',
    'observe': 'observar', 'respond': 'corregir', 'incident': 'proceso', 'catalog': 'administrar',
    'directory': 'administrar', 'backup': 'administrar', 'export_delivery': 'entrega',
    'pages': 'corregir', 'edit_pending': 'proceso', 'revision': 'corregir',
}


def listing(store, filters):
    works = store.works(texto=filters.get('q', ''), folio=filters.get('folio', ''),
                        digitalizador=filters.get('digitalizador', ''), estado=filters.get('estado', ''), partial=True)
    if filters.get('prioridad'):
        works = [w for w in works if w['prioridad'] == filters['prioridad']]
    today = dt.date.today().isoformat()
    for work in works:
        work['atrasado'] = bool(work.get('fecha_objetivo') and work['fecha_objetivo'] < today and work['estado'] != STATES[-1])
        work['siguiente'] = next_action(work)
    if filters.get('pendiente') == 'vencidos':
        works = [w for w in works if w['atrasado']]
    if filters.get('pendiente') == 'sin_asignar':
        works = [w for w in works if not w['digitalizador']]
    return works


def next_action(w):
    if w.get('recepcion') != 'Aceptado': return 'Cotejar y aceptar recepción'
    if w.get('bloqueo'): return 'Atender bloqueo registrado'
    if not w.get('digitalizador'): return 'Asignar digitalizador'
    if w.get('fisicos') is None: return 'Contar y confirmar hojas nuevas'
    if not w.get('total_tiff'): return 'Importar y codificar TIFF'
    if w['estado'] == STATES[-1]: return 'Entrega aprobada · revisar devolución'
    if w['estado'] in STATES[8:10]: return 'Resolver observaciones'
    return 'Validar documentos y revisar entrega'


def overview(store, filters):
    works = listing(store, filters)
    snap = Dashboard(store).snapshot(works, filters)
    snap['kpis'] = [{'label': k, 'value': snap['metrica'][k]} for k in ['Trabajos activos', 'Hojas físicas confirmadas', 'Archivos TIFF', 'Páginas conocidas']]
    snap['attention'] = sorted(works, key=lambda w: (not w['atrasado'], w['prioridad'] not in ('Urgente', 'Alta'), w['id']))[:8]
    snap['vencidos'] = sum(w['atrasado'] for w in works)
    return snap


def board(store, filters):
    rows = listing(store, filters)
    buckets = [STATES[:1], STATES[1:7], STATES[7:8], STATES[8:10], STATES[10:]]
    return [{'title': name, 'items': [w for w in rows if w['estado'] in states]} for name, states in zip(KANBAN, buckets)]


def detail(store, work):
    w = store.one('trabajos', work)
    people = store.rows('SELECT nombre FROM personas WHERE curp=?', (w['curp'],))
    w['nombre'] = people[0]['nombre'] if people else 'Nombre no registrado'
    service = Integrations(store)
    current = service.current(work)
    coder = CodingService(store)
    files = store.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=? ORDER BY activo DESC,id', (work,))
    for row in files:
        row['nombre'] = Path(row['ruta']).name
    return dict(work=w, context=service.context(work), current=current, integrations=service.list(work), totals=service.totals(work),
                files=files, catalog=coder.catalog(), counts=store.rows('SELECT * FROM conteos WHERE integracion_id=? ORDER BY id', (current['id'],)),
                folios=store.rows('SELECT * FROM folios WHERE activo=1 ORDER BY id DESC'),
                deliveries=store.rows('SELECT * FROM entregas WHERE trabajo_id=? ORDER BY numero DESC', (work,)),
                observations=store.rows('SELECT o.* FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE e.trabajo_id=? ORDER BY o.id DESC', (work,)),
                sessions=store.rows("SELECT s.* FROM sesiones_revision s JOIN entregas e ON e.id=s.entrega_id WHERE e.trabajo_id=? AND s.fin IS NULL", (work,)),
                history=store.rows('SELECT * FROM historial WHERE trabajo_id=? ORDER BY id DESC LIMIT 60', (work,)),
                corrections=coder.corrections(work), incidents=store.rows('SELECT * FROM incidencias WHERE trabajo_id=? ORDER BY id DESC', (work,)),
                related=store.associated(work), states=STATES)


def image(store, work, file_id, page):
    coder = CodingService(store)
    row = coder.file(file_id)
    if row['trabajo_id'] != work: raise ValueError('Archivo de otro expediente.')
    if not 0 <= page < row['paginas']: raise ValueError('Página fuera del documento.')
    frame = render_page(coder.path(row['ruta']), page)
    try:
        frame.thumbnail((1800, 1800))
        out = io.BytesIO()
        with frame.convert('RGB') as rgb:
            rgb.save(out, format='PNG')
        return out.getvalue()
    finally:
        frame.close()


def act(store, role, action, work, data, uploads=()):
    if action not in PERMISSIONS: raise ValueError('Acción desconocida.')
    ops = Operations(store, role)
    permission = 'observar' if action == 'respond' and data.get('estado') in ('Validada', 'Anulada', 'Abierta') else PERMISSIONS[action]
    ops.permit(permission)
    reason = str(data.get('motivo', '')).strip()
    if not reason: raise ValueError('Indica el motivo o la evidencia de la acción.')
    ident = lambda key: integer(data.get(key), 1)
    coder = CodingService(store)
    result = {'message': 'Acción registrada correctamente.', 'work': work}
    # Verificar siempre pertenencia al expediente, incluso con POST manipulado.
    if work:
        store.one('trabajos', work)
    if action in ('count','edit_count','confirm_count') and Integrations(store).current(work)['fisicos'] is not None:
        raise ValueError('El conteo está confirmado. Abre Conteo rápido y usa Reabrir con motivo.')
    if action in ('code', 'edit', 'rename', 'original', 'correction','edit_pending','revision'):
        if coder.file(ident('archivo'))['trabajo_id'] != work: raise ValueError('TIFF de otro expediente.')
    if action in ('begin_review', 'approve', 'export_delivery'):
        if Deliveries(store).get(data.get('entrega', ''))['trabajo_id'] != work: raise ValueError('Entrega de otro expediente.')
    if action == 'folio': result['folio'] = store.save_folio(data.get('numero', ''), data.get('fecha', ''), data.get('responsable', ''), motivo=reason)
    elif action == 'expected': ops.expect(ident('folio'), data.get('curp', ''), data.get('legajo', ''), data.get('ubicacion', ''), data.get('nombre', ''))
    elif action == 'receipt': ops.receive_folio(ident('folio'), data.get('origen', ''), data.get('entrega', ''), data.get('recibe', ''), data.get('acuse', ''), data.get('fecha_hora') or None)
    elif action == 'accept':
        result.update(Reception(store, role).accept(ident('folio'), data.get('seleccion', []), reason, data.get('confirmado') == 'on', data.get('legajo') or None))
    elif action == 'difference':
        ops.validate_item(ident('item'), data.get('decision'), data.get('curp', ''), data.get('legajo') or None, reason, data.get('confirmado') == 'on')
    elif action == 'legajos':
        from app.intake import register_legajos
        register_legajos(store, ident('item'), data.get('legajos', ''), reason)
    elif action == 'assign': ops.assign(data.get('persona', ''), reason, work=work, role=data.get('rol', 'Digitalizador'))
    elif action == 'integration': result['integration'] = Integrations(store).start(work, reason, data.get('fecha', ''), data.get('folio') or None, data.get('acuse', ''), data.get('persona', ''), data.get('confirmado') == 'on')
    elif action == 'count': store.add_count(work, data.get('cantidad'), reason)
    elif action == 'confirm_count': store.confirm_count(work)
    elif action == 'edit_count':
        rows = store.rows('SELECT trabajo_id FROM conteos WHERE id=?', (ident('bloque'),))
        if not rows or rows[0]['trabajo_id'] != work: raise ValueError('Bloque ajeno al expediente.')
        store.edit_count(ident('bloque'), data.get('cantidad'), reason, data.get('anular') == 'on')
    elif action == 'state': store.change_state(work, data.get('estado', ''), reason)
    elif action == 'card': ops.card_metadata(work, data.get('notas', ''), data.get('prioridad', 'Normal'), data.get('etiqueta', ''), data.get('bloqueo', ''), data.get('fecha') or None)
    elif action == 'custody': ops.custody(Integrations(store).current(work)['prestamo_item_id'], data.get('custodia'), reason, data.get('recibe', ''))
    elif action == 'upload':
        if not uploads: raise ValueError('Selecciona archivos TIFF.')
        imported = coder.import_files(work, uploads)
        result['message'] = 'Importación: {} TIFF nuevos, {} duplicados. {}'.format(imported['importados'], imported['duplicados'], '; '.join(imported['errores']) or 'Codifica los documentos nuevos.')
        result['warning'] = bool(imported['errores'])
    elif action == 'code': coder.assign(ident('archivo'), data.get('codigo', ''))
    elif action == 'batch_code':
        batch = BatchTiff(coder).run(work, data.get('seleccion',[]), 'codificar', reason, code=data.get('codigo',''))
        result.update(batch=batch, warning=bool(batch['pendientes']))
        result['message'] = '{}: {} codificados; {} pendientes.'.format(batch['estado'],len(batch['completados']),len(batch['pendientes']))
    elif action == 'rename': coder.rename(ident('archivo'), data.get('nombre', ''))
    elif action == 'edit':
        page = integer(data.get('pagina'), 1) - 1
        if page >= coder.file(ident('archivo'))['paginas']: raise ValueError('Página fuera del TIFF.')
        if data.get('tipo') == 'girar':
            import math
            angle = float(data.get('angulo',90))
            if not math.isfinite(angle) or not -180<=angle<=180: raise ValueError('Ángulo fuera de rango.')
            edits = [('rotate', angle)]
        elif data.get('tipo') == 'recortar': edits = [('crop',) + tuple(integer(data.get(k)) for k in ('x1', 'y1', 'x2', 'y2'))]
        else: raise ValueError('Ajuste desconocido.')
        coder.save_edit(ident('archivo'), page, edits)
    elif action == 'edit_pending':
        from .desk import edits
        coder.save_edit(ident('archivo'),integer(data.get('pagina'),1)-1,edits(data))
    elif action == 'pages':
        from app.pages import PageOperations
        if data.get('confirmado')!='on': raise ValueError('Confirma el plan de páginas.')
        result.update(PageOperations(coder).run(work,data.get('spec',{}),data.get('fingerprint',''),reason))
    elif action == 'revision':
        if data.get('confirmado')!='on': raise ValueError('Confirma restaurar la revisión.')
        coder.restore_original(ident('archivo'),revision_id=ident('revision'))
    elif action == 'original': coder.restore_original(ident('archivo'))
    elif action == 'batch':
        batch = BatchTiff(coder).run(work, data.get('seleccion', []), data.get('tipo'), reason)
        result.update(batch=batch, warning=bool(batch['pendientes']))
        result['message'] = '{}: {} archivos terminados y {} pendientes. {}'.format(batch['estado'], len(batch['completados']), len(batch['pendientes']), batch['error'] or '')
    elif action == 'recover': coder.recover(work)
    elif action == 'correction': coder.mark_correction(ident('archivo'), integer(data.get('pagina'), 1), data.get('ubicacion', ''), reason)
    elif action in ('replace', 'resolve_correction'):
        matches = [r for r in coder.corrections(work) if r['id'] == ident('correccion')]
        if not matches: raise ValueError('Corrección de otro expediente.')
        if action == 'resolve_correction': coder.resolve_without_replacement(ident('correccion'), reason)
        else:
            if coder.file(ident('nuevo'))['trabajo_id'] != work: raise ValueError('TIFF nuevo ajeno al expediente.')
            (coder.replace_scanned_page if data.get('tipo') == 'pagina' else coder.replace_correction)(ident('correccion'), ident('nuevo'), reason)
    elif action == 'validate':
        report = Deliveries(store, role).validate(work)
        result['message'] = report['resultado'] + ': ' + '; '.join(x['mensaje'] for x in report['problemas'])
    elif action == 'deliver':
        if data.get('confirmado') != 'on': raise ValueError('Confirma que la entrega será el expediente completo actualizado.')
        result['delivery'] = Deliveries(store, role).prepare(work)
        result['message'] = 'Nueva entrega completa generada. Las anteriores se conservan. Falta revisión y aprobación.'
    elif action == 'begin_review': Reviews(store, role).begin(data['entrega'])
    elif action == 'approve':
        if data.get('confirmado') != 'on': raise ValueError('Confirma el cotejo de la entrega exacta antes de aprobar.')
        Reviews(store, role).approve(data['entrega'], reason)
    elif action == 'observe':
        sessions = store.rows('SELECT e.trabajo_id FROM sesiones_revision s JOIN entregas e ON e.id=s.entrega_id WHERE s.id=?', (data.get('sesion'),))
        if not sessions or sessions[0]['trabajo_id'] != work: raise ValueError('Sesión de revisión ajena.')
        Reviews(store, role).observe(data['sesion'], data.get('tipo'), reason, data.get('persona', ''), location=data.get('ubicacion', ''), blocking=data.get('bloqueante') == 'on')
    elif action == 'respond':
        rows = store.rows('SELECT e.trabajo_id FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE o.id=?', (ident('observacion'),))
        if not rows or rows[0]['trabajo_id'] != work: raise ValueError('Observación de otro expediente.')
        Reviews(store, role).update_observation(ident('observacion'), data.get('estado'), reason, data.get('entrega') or None)
    elif action == 'incident': store.save_incident(work, None, data.get('documento', ''), reason)
    elif action == 'catalog': store.save_catalog('documento', data.get('codigo', ''), data.get('carpeta', ''), data.get('titulo', ''), motivo=reason)
    elif action == 'directory':
        from app.directory import Directory
        Directory(store).save(data.get('tipo'), data.get('nombre', ''), reason)
    elif action == 'backup':
        from .backup import create_web_backup, verify_web_backup
        import uuid
        dest = store.workspace.backups / ('web-' + uuid.uuid4().hex)
        create_web_backup(store, dest)
        verify_web_backup(dest)
        result['message'] = 'Respaldo privado verificado: expedientes, TIFF, entregas, usuarios, permisos y solicitudes. Conserva también la base de origen y las versiones del código. Ubicación: respaldos del workspace.'
    elif action == 'export_delivery':
        import uuid
        dest = store.workspace.reports / ('entrega-' + uuid.uuid4().hex)
        dest.parent.mkdir(parents=True, exist_ok=True)
        Deliveries(store, role).export_copy(data['entrega'], dest)
        result['message'] = 'Copia de entrega verificada en reportes del workspace, en una carpeta nueva.'
    else: raise ValueError('Esta acción todavía no está habilitada.')
    return result
