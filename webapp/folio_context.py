"""Lecturas por elemento/recepción; no sustituye el ciclo vigente del maestro."""
from app.directory import normalized


def folio_view(store, folio_id=None, query='', condition='', principals=None):
    folios = store.rows('SELECT * FROM folios WHERE activo=1 ORDER BY id DESC')
    if not folio_id:
        return dict(folios=folios, folio=None, items=[], summary=[], filtered=0)
    folio = store.one('folios', int(folio_id))
    if principals is None: principals={w['id'] for w in store.works()}
    rows = store.rows('''SELECT p.*,COALESCE(n.nombre,e.nombre,'') AS nombre,
        i.id AS integracion_id,i.numero AS integracion,i.trabajo_id AS ciclo,
        i.estado AS etapa,i.digitalizador,i.fisicos,i.recibido,
        t.integracion_actual_id,t.calidad,t.activo AS ciclo_activo,
        (SELECT COUNT(*) FROM integraciones x WHERE x.trabajo_id=t.id AND x.numero>0) AS integraciones,
        (SELECT COUNT(*) FROM archivos_tiff a WHERE a.integracion_id=i.id AND a.activo=1) AS tiff,
        (SELECT SUM(paginas) FROM archivos_tiff a WHERE a.integracion_id=i.id AND a.activo=1) AS paginas
        FROM prestamo_items p LEFT JOIN personas e ON e.curp=p.curp_esperada
        LEFT JOIN personas n ON n.curp=p.curp_recibida
        LEFT JOIN integraciones i ON i.prestamo_item_id=p.id
        LEFT JOIN trabajos t ON t.id=i.trabajo_id
        WHERE p.folio_id=? ORDER BY p.id,i.numero''', (folio['id'],))
    for row in rows:
        row['condicion'] = ('Devuelto' if row['devolucion_at'] else
                            'Recibido / cotejado' if row['validacion']=='Aceptado' else
                            'Esperado' if row['validacion']=='Pendiente' else row['validacion'])
        row['ciclo_historico'] = bool(row['ciclo'] and row['ciclo'] not in principals)
        row['historica'] = bool(row['integracion_id'] and (row['integracion_id'] != row['integracion_actual_id'] or row['ciclo_historico']))
        row['curp_visible'] = row['curp_recibida'] or row['curp_esperada']
        row['legajo_visible'] = row['legajo_recibido'] or row['legajo_esperado']
    summary = [{'label':'Elementos esperados', 'value':sum(bool(r['curp_esperada']) for r in rows)},
               {'label':'Cotejados / recibidos', 'value':sum(r['validacion']=='Aceptado' for r in rows)},
               {'label':'Pendientes', 'value':sum(r['validacion']=='Pendiente' for r in rows)},
               {'label':'Faltantes', 'value':sum(r['validacion']=='Faltante' for r in rows)},
               {'label':'Discrepancias', 'value':sum(r['validacion']=='Discrepancia' for r in rows)},
               {'label':'Devueltos', 'value':sum(bool(r['devolucion_at']) for r in rows)}]
    items = [r for r in rows if (not query or normalized(query) in normalized(r['nombre']+' '+r['curp_visible']))
             and (not condition or r['condicion']==condition)]
    return dict(folios=folios, folio=folio, items=items, summary=summary, filtered=len(items))
