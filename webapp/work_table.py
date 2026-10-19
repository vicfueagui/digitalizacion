"""Una consulta de agregados por ámbito; sin abrir TIFF ni N consultas por fila."""
from .domain import listing


def build(store,filters,order='nombre',descending=False):
    works=listing(store,filters)
    aggregates={r['trabajo_id']:r for r in store.rows('''SELECT trabajo_id,
        SUM(CASE WHEN activo=1 AND codigo IS NOT NULL THEN 1 ELSE 0 END) AS coded,
        SUM(CASE WHEN activo=1 AND codigo IS NULL THEN 1 ELSE 0 END) AS uncoded
        FROM archivos_tiff GROUP BY trabajo_id''')}
    incidents={r['trabajo_id']:r['n'] for r in store.rows("SELECT trabajo_id,COUNT(*) AS n FROM incidencias WHERE estado!='Resuelta' GROUP BY trabajo_id")}
    counts={r['trabajo_id']:r['n'] for r in store.rows('SELECT trabajo_id,COUNT(*) AS n FROM integraciones WHERE fisicos IS NULL GROUP BY trabajo_id')}
    for w in works:
        w.update(aggregates.get(w['id'],dict(coded=0,uncoded=0)))
        w['alerts']=incidents.get(w['id'],0);w['unconfirmed']=counts.get(w['id'],0)
    allowed=('nombre','folio_integracion','digitalizador','estado','recibido_integracion','total_tiff','total_paginas','uncoded')
    if order not in allowed:order='nombre'
    works.sort(key=lambda w:((w.get(order) or 0) if order in ('total_tiff','total_paginas','uncoded') else str(w.get(order) or '').casefold(),w['id']),reverse=descending)
    summary=dict(works=len(works),people=len({w['curp'] for w in works}),uncoded=sum(w['uncoded'] for w in works),
                 unconfirmed=sum(w['unconfirmed'] for w in works),alerts=sum(w['alerts'] for w in works))
    return works,summary
