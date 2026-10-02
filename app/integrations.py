"""Lotes documentales sucesivos dentro de un ciclo, sin fusionar ciclos históricos."""
from .core import date, integer, now, STATES


def migrate(store):
    """Dentro de la transacción de migración; fechas originales no se inventan."""
    db=store.db
    for work in store.rows('SELECT * FROM trabajos ORDER BY id'):
        ident=db.execute('''INSERT INTO integraciones(trabajo_id,numero,folio_id,prestamo_item_id,
            motivo,recibido,fisicos,estado,digitalizador,creado,cerrado,operador,origen)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (work['id'],0,work['folio_id'],work['prestamo_item_id'],'Carga inicial: historial anterior conservado',
             work['recibido'],work['fisicos'],work['estado'],work['digitalizador'],now(),
             work['estado_desde'] if work['estado']==STATES[-1] else None,store.operador,
             'Migración técnica; creado no acredita fecha de recepción')).lastrowid
        db.execute('UPDATE trabajos SET integracion_actual_id=? WHERE id=?',(ident,work['id']))
        for table in ('conteos','historial'):
            db.execute('UPDATE '+table+' SET integracion_id=? WHERE trabajo_id=?',(ident,work['id']))
        db.execute('UPDATE archivos_tiff SET integracion_id=?,integracion_ingreso_id=? WHERE trabajo_id=?',(ident,ident,work['id']))


class Integrations:
    def __init__(self,store):self.s=store;self.db=store.db

    def current(self,work):
        rows=self.s.rows('SELECT i.* FROM integraciones i JOIN trabajos t ON t.integracion_actual_id=i.id WHERE t.id=?',(work,))
        if not rows:raise ValueError('El expediente no tiene integración actual. Revisa la migración de esta copia.')
        return rows[0]

    def list(self,work):
        return self.s.rows('''SELECT i.*,f.numero AS folio,COALESCE(a.tiff,0) AS tiff,
            COALESCE(a.paginas,0) AS paginas,COALESCE(c.bloques,0) AS bloques,
            CASE WHEN i.numero=0 THEN 'Carga inicial' ELSE 'Integración '||i.numero END AS etiqueta
            FROM integraciones i JOIN folios f ON f.id=i.folio_id
            LEFT JOIN (SELECT integracion_id,COUNT(*) AS tiff,SUM(paginas) AS paginas FROM archivos_tiff
                WHERE activo=1 GROUP BY integracion_id) a ON a.integracion_id=i.id
            LEFT JOIN (SELECT integracion_id,COUNT(*) AS bloques FROM conteos WHERE activo=1 GROUP BY integracion_id) c ON c.integracion_id=i.id
            WHERE i.trabajo_id=? ORDER BY i.numero''',(work,))

    def totals(self,work):
        rows=self.list(work);missing=sum(row['fisicos'] is None for row in rows)
        return {'hojas_confirmadas':sum(row['fisicos'] or 0 for row in rows),
                'conteos_pendientes':missing,'hojas_totales':None if missing else sum(row['fisicos'] for row in rows),
                'tiff':sum(row['tiff'] for row in rows),'paginas':sum(row['paginas'] for row in rows),
                'integraciones':max(0,len(rows)-1),'lotes':len(rows)}

    def start(self,work,reason,received,folio=None,reference='',digitalizer='',confirmed=False,checkpoint=None):
        from .operations import Operations
        from .directory import Directory
        from .delivery import Deliveries
        Operations(self.s).permit('asignacion')
        before=self.s.one('trabajos',work);current=self.current(work)
        received=date(received)
        if not reason.strip() or not received or not reference.strip():
            raise ValueError('Registra motivo, fecha real de recepción y referencia/acuse de la nueva documentación.')
        if not confirmed:raise ValueError('Confirma físicamente CURP, legajo y documentación recibida antes de iniciar la integración.')
        if not before['activo'] or before['estado']!=STATES[-1]:
            raise ValueError('Primero revisa y aprueba la entrega anterior. Para corregirla usa reapertura con motivo; no otra integración.')
        if current['fisicos'] is None or before['fisicos'] is None:
            raise ValueError('La integración anterior no tiene conteo confirmado.')
        previous=self.s.rows("SELECT * FROM entregas WHERE trabajo_id=? AND estado NOT IN ('Preparando','Incompleta') ORDER BY numero DESC LIMIT 1",(work,))
        if not previous or previous[0]['estado']!='Aprobada':raise ValueError('Se requiere una entrega anterior aprobada y verificable.')
        Deliveries(self.s).verify(previous[0]['id'])
        from .delivery import content_hash
        report=Deliveries(self.s).inventory(work,final=True)
        if report['resultado'] not in ('OK','OK con advertencias') or content_hash(report['items'])!=previous[0]['inventario_hash']:
            raise ValueError('El expediente vigente difiere de su entrega aprobada. Revisa y corrige antes de recibir otra integración.')
        if self.s.rows("SELECT id FROM operaciones_tiff WHERE trabajo_id=? AND estado='Preparada'",(work,)):
            raise ValueError('Recupera primero la operación TIFF interrumpida.')
        folio=integer(folio or current['folio_id'],1)
        if not self.s.one('folios',folio)['activo']:raise ValueError('El folio de recepción está inactivo.')
        # Este resguardo antecede a la transición; no reemplaza un respaldo completo.
        self.s.backup()
        with self.db:
            # Releer bajo transacción: una segunda petición no crea otro lote abierto.
            self.db.execute('UPDATE trabajos SET id=id WHERE id=?',(work,))
            if self.s.one('trabajos',work)['estado']!=STATES[-1]:raise ValueError('El expediente ya tiene una integración en curso.')
            stamp=now();number=current['numero']+1
            operator=digitalizer.strip() or before['digitalizador']
            operator_id=Directory(self.s).ensure('persona',operator)
            item=self.db.execute('''INSERT INTO prestamo_items(folio_id,expediente_id,curp_esperada,legajo_esperado,
                curp_recibida,legajo_recibido,validacion,validado_por,validado_at,discrepancia,custodia,origen)
                VALUES(?,?,?,?,?,?,'Aceptado',?,?,?,'Prestado a Digitalización',?)''',
                (folio,before['expediente_id'],before['curp'],before['legajo'],before['curp'],before['legajo'],
                 self.s.operador,stamp,reference.strip(),'Integración '+str(number)+': documentación adicional')).lastrowid
            ident=self.db.execute('''INSERT INTO integraciones(trabajo_id,numero,folio_id,prestamo_item_id,
                referencia,motivo,recibido,estado,digitalizador,creado,operador,origen)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                (work,number,folio,item,reference.strip(),reason.strip(),received,STATES[0],operator,stamp,self.s.operador,'Recepción confirmada de nueva documentación')).lastrowid
            self.db.execute('UPDATE historial SET fin=? WHERE trabajo_id=? AND fin IS NULL',(stamp,work))
            self.db.execute("UPDATE sesiones_revision SET fin=?,estado='Cerrada por nueva integración' WHERE fin IS NULL AND entrega_id IN (SELECT id FROM entregas WHERE trabajo_id=?)",(stamp,work))
            self.db.execute('''UPDATE trabajos SET integracion_actual_id=?,estado=?,estado_desde=?,fisicos=NULL,
                carpetas=0,calidad='No revisado',digitalizador=?,digitalizador_id=? WHERE id=?''',
                (ident,STATES[0],stamp,operator,operator_id,work))
            self.db.execute('INSERT INTO historial(trabajo_id,estado,inicio,motivo,operador) VALUES(?,?,?,?,?)',
                (work,STATES[0],stamp,'Nueva integración '+str(number)+': '+reason.strip(),self.s.operador))
            self.db.execute("UPDATE asignaciones SET fin=? WHERE trabajo_id=? AND fin IS NULL",(stamp,work))
            if operator:
                self.db.execute('''INSERT INTO asignaciones(trabajo_id,folio_id,persona,rol,inicio,registrado,operador,motivo,origen,persona_id)
                    VALUES(?,?,?,'Digitalizador',?,?,?,?,?,?)''',
                    (work,folio,operator,stamp,stamp,self.s.operador,reason.strip(),'Nueva integración',operator_id))
            self.s.invalidate_inventory(work,'Nueva integración: contar, digitalizar, codificar y generar una entrega completa actualizada')
            Operations(self.s).receipt_status(folio)
            Operations(self.s).event(work,'Nueva integración '+str(number),reason.strip(),item)
            self.s.audit('integraciones',ident,'iniciar',None,self.current(work),reason.strip())
            if checkpoint:checkpoint()
        return ident

    def check_delivery(self,work):
        current=self.current(work)
        if current['numero'] and self.totals(work)['conteos_pendientes']:
            raise ValueError('Confirma el conteo de las nuevas hojas antes de Organizar / entregar.')
        if current['numero'] and not self.s.rows('SELECT id FROM archivos_tiff WHERE integracion_id=? AND activo=1',(current['id'],)):
            raise ValueError('Digitaliza la documentación nueva de esta integración antes de entregar.')

    def manifest(self,work):
        result=[]
        for row in self.list(work):
            record={k:row[k] for k in ('id','numero','etiqueta','folio','recibido','referencia','fisicos','tiff','paginas')}
            record['archivos']=self.s.rows('SELECT id AS archivo_id,documento_id,integracion_ingreso_id FROM archivos_tiff WHERE integracion_id=? AND activo=1 ORDER BY id',(row['id'],))
            result.append(record)
        return result

    def context(self,work):
        row=self.current(work);w=self.s.one('trabajos',work)
        person=self.s.rows('SELECT nombre FROM personas WHERE curp=?',(w['curp'],))
        return {'nombre':person[0]['nombre'].strip() if person and person[0]['nombre'].strip() else 'Nombre no registrado',
                'curp':w['curp'],'legajo':w['legajo'],'integracion':row['numero'],
                'etiqueta':'Carga inicial' if row['numero']==0 else 'Integración '+str(row['numero']),
                'folio':self.s.one('folios',row['folio_id'])['numero'],'prestamo_item_id':row['prestamo_item_id']}
