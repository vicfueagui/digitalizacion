"""Enlace conservador de trabajos anteriores con maestros y préstamos."""
import uuid
from .core import now


def update_receipt(db, folio):
    states=[r[0] for r in db.execute('SELECT validacion FROM prestamo_items WHERE folio_id=?',(folio,))]
    status='Aceptado' if states and all(v=='Aceptado' for v in states) else 'Aceptado parcialmente' if 'Aceptado' in states else 'Con pendientes'
    db.execute('UPDATE folios SET recepcion_estado=? WHERE id=?',(status,folio))


def link_work(store, work, legacy=False):
    db=store.db;w=store.one('trabajos',work);person=w['curp'].strip().upper()
    found=store.rows('SELECT id FROM expedientes WHERE curp=? AND legajo=?',(person,w['legajo']))
    if found:master=found[0]['id']
    else:
        master=uuid.uuid4().hex
        db.execute('INSERT INTO expedientes VALUES(?,?,?,?,?)',(master,person,w['legajo'],now(),'Legado por revisar' if legacy else 'Registrado'))
    if not w['prestamo_item_id']:
        expected=store.rows('SELECT id FROM prestamo_items WHERE folio_id=? AND expediente_id=?',(w['folio_id'],master)) if not legacy else []
        if expected:item=expected[0]['id']
        else:
            item=db.execute('INSERT INTO prestamo_items(folio_id,expediente_id,curp_esperada,legajo_esperado,origen) VALUES(?,?,?,?,?)',
                            (w['folio_id'],master,person,w['legajo'],'Legado por revisar' if legacy else 'Registrado')).lastrowid
            if not legacy:update_receipt(db,w['folio_id'])
    else:item=w['prestamo_item_id']
    db.execute('UPDATE trabajos SET expediente_id=?,prestamo_item_id=?,procedencia=? WHERE id=?',
               (master,item,'Legado por revisar' if legacy else w['procedencia'],work))
    if w['digitalizador'] and not store.rows('SELECT id FROM asignaciones WHERE trabajo_id=?',(work,)):
        db.execute('INSERT INTO asignaciones(trabajo_id,persona,rol,inicio,registrado,operador,motivo,origen) VALUES(?,?,?,?,?,?,?,?)',
                   (work,w['digitalizador'],'Digitalizador',None if legacy else now(),now(),store.operador,'Dato preexistente; recepción pendiente de confirmar','Legado' if legacy else 'Declarada'))
    return master,item


def migrate(store):
    for w in store.rows('SELECT id FROM trabajos ORDER BY id'):link_work(store,w['id'],legacy=True)
    store.db.execute('''UPDATE trabajos SET conciliacion_pendiente=1 WHERE expediente_id IN
        (SELECT expediente_id FROM trabajos GROUP BY expediente_id HAVING COUNT(*)>1)''')
    for row in store.rows('SELECT expediente_id,COUNT(*) AS cantidad FROM trabajos WHERE conciliacion_pendiente=1 GROUP BY expediente_id'):
        store.db.execute('INSERT INTO pendientes(tipo,detalle) VALUES(?,?)',('Ciclos históricos por conciliar',
            'Expediente maestro '+row['expediente_id']+': '+str(row['cantidad'])+' registros conservados; no se fusionaron archivos ni conteos.'))
