"""Datasets acotados de metadatos. Los gráficos no abren imágenes ni suman entregas."""
from app.analytics import Cube, day, bucket
from app.dashboard import Dashboard, percentage
from app.directory import normalized
from app.core import date
from .domain import listing
from .folio_context import folio_view


def build(store, filters, config):
    works = listing(store,filters)
    first,last = date(config['start']),date(config['end'])
    if first and last and first>last: raise ValueError('El inicio supera al final.')
    # El inventario de la cabecera filtra fecha de recepción del ciclo.
    cohort = [w for w in works if (not first or w['recibido'] and w['recibido']>=first)
              and (not last or w['recibido'] and w['recibido']<=last)]
    snapshot = Dashboard(store).snapshot(cohort,filters)
    snapshot['kpis'] = [{'label':label,'value':snapshot['metrica'][key]} for label,key in [
        ('Expedientes vigentes','Trabajos activos'),('CURP distintas','CURP distintas'),
        ('TIFF activos','Archivos TIFF'),('Páginas registradas','Páginas conocidas')]]
    cube = Cube(store).snapshot(works,folio=filters.get('folio',''),**config)
    ids=[w['id'] for w in cohort]; marks=','.join('?' for _ in ids) or 'NULL'
    codes=store.rows("SELECT COALESCE(NULLIF(codigo,''),'Sin código') AS label,COUNT(*) AS value FROM archivos_tiff WHERE activo=1 AND trabajo_id IN ("+marks+") GROUP BY codigo ORDER BY value DESC",ids)
    total=sum(r['value'] for r in codes); pending=sum(r['value'] for r in codes if r['label']=='Sin código')
    coding=[{'label':'Codificados','value':total-pending},{'label':'Pendientes de código','value':pending}]
    quality=[]
    for label,sql in [
        ('Observaciones abiertas',"SELECT COUNT(*) AS n FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE o.estado IN ('Abierta','En corrección') AND e.trabajo_id IN ("+marks+")"),
        ('Reescaneos pendientes',"SELECT COUNT(*) AS n FROM correcciones_tiff c JOIN archivos_tiff a ON a.id=c.archivo_id WHERE c.estado='Pendiente' AND a.trabajo_id IN ("+marks+")"),
        ('Entregas aprobadas',"SELECT COUNT(*) AS n FROM entregas WHERE estado='Aprobada' AND trabajo_id IN ("+marks+")"),
        ('Entregas por revisar / aprobar',"SELECT COUNT(*) AS n FROM entregas WHERE estado NOT IN ('Aprobada','Preparando','Incompleta') AND trabajo_id IN ("+marks+")"),
        ('Integraciones sin conteo',"SELECT COUNT(*) AS n FROM integraciones WHERE fisicos IS NULL AND trabajo_id IN ("+marks+")")]:
        quality.append({'label':label,'value':store.rows(sql,ids)[0]['n']})
    folios=store.rows('SELECT id,numero FROM folios WHERE activo=1 ORDER BY id DESC')
    reception=[]; scope_ids={w['id'] for w in works}; principals={w['id'] for w in store.works()}
    for f in folios:
        if filters.get('folio') and normalized(filters['folio']) not in normalized(f['numero']):continue
        context=folio_view(store,f['id'],filters.get('q',''),principals=principals)
        rows=context['items']
        if any(filters.get(k) for k in ('digitalizador','estado','prioridad','pendiente')):
            rows=[r for r in rows if r['ciclo'] in scope_ids]
        if first or last:
            rows=[r for r in rows if r['recibido'] and (not first or r['recibido']>=first) and (not last or r['recibido']<=last)]
        if rows:
            reception.append({'folio':f['numero'],'id':f['id'],
                'expected':sum(bool(r['curp_esperada']) for r in rows),
                'received':sum(r['validacion']=='Aceptado' for r in rows),
                'pending':sum(r['validacion']=='Pendiente' for r in rows),
                'missing':sum(r['validacion']=='Faltante' for r in rows),
                'discrepancy':sum(r['validacion']=='Discrepancia' for r in rows),
                'returned':sum(bool(r['devolucion_at']) for r in rows)})
    # Serie de recepciones adicionales reales, nunca fecha técnica de migración.
    scope=[w['id'] for w in works]; slots=','.join('?' for _ in scope) or 'NULL'
    events=store.rows('SELECT i.recibido,i.numero,f.numero AS folio FROM integraciones i JOIN folios f ON f.id=i.folio_id WHERE i.trabajo_id IN ('+slots+')',scope)
    series={}; unknown=0
    for event in events:
        if filters.get('folio') and normalized(filters['folio']) not in normalized(event['folio']):continue
        stamp=day(event['recibido'])
        if stamp is None:unknown+=1;continue
        if first and stamp.isoformat()<first or last and stamp.isoformat()>last:continue
        key=bucket(stamp,config['period']);row=series.setdefault(key,{'label':key,'initial':0,'additional':0})
        row['additional' if event['numero'] else 'initial']+=1
    return dict(snapshot=snapshot,cube=cube,coding=coding,coding_percent=percentage(total-pending,total),
                frequent=codes[:12],quality=quality,reception=reception,series=[series[k] for k in sorted(series)],
                events_unknown=unknown)
