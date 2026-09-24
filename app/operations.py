"""Préstamos y ciclos independientes. Acciones de dominio para UI y futura API."""
import uuid
from .core import curp, integer, now, date, STATES

CUSTODY=['Registrado','Recibido por Digitalización','Con discrepancia','Prestado a Digitalización','En devolución','Devuelto','Devolución aceptada','Incidencia de custodia']
KANBAN=['Recibidos / Por asignar','En digitalización','En revisión','Correcciones','Listos / Finalizados']
ROLES={'Administrador':None,'Responsable':None,'Digitalizador':{'proceso','tarjeta','entrega','corregir','legado'},'Revisor':{'revision','observar','aprobar'},'Consulta':set(),'Archivo':{'recepcion','custodia'}}


class Operations:
    def __init__(self,store,role='Responsable'):
        if role not in ROLES:raise ValueError('Rol desconocido.')
        self.s=store;self.db=store.db;self.role=role

    def permit(self,action):
        allowed=ROLES[self.role]
        if allowed is not None and action not in allowed:raise ValueError('El rol no permite esta acción: '+action)

    def event(self,work,action,reason,item=None):
        if not reason.strip():raise ValueError('Indica motivo o evidencia.')
        w=self.s.one('trabajos',work) if work else None
        master=w['expediente_id'] if w else None
        if item and not master:
            master=self.s.rows('SELECT expediente_id FROM prestamo_items WHERE id=?',(item,))[0]['expediente_id']
        self.db.execute('INSERT INTO eventos_operativos(expediente_id,trabajo_id,prestamo_item_id,evento,fecha,operador,motivo) VALUES(?,?,?,?,?,?,?)',
                        (master,work,item or (w['prestamo_item_id'] if w else None),action,now(),self.s.operador,reason))

    def master(self,person,legajo):
        person=curp(person);legajo=integer(legajo,1)
        rows=self.s.rows('SELECT id FROM expedientes WHERE curp=? AND legajo=?',(person,legajo))
        if rows:return rows[0]['id']
        ident=uuid.uuid4().hex
        self.db.execute('INSERT INTO expedientes VALUES(?,?,?,?,?)',(ident,person,legajo,now(),'Registrado'))
        return ident

    def receive_folio(self,folio,origin,delivered_by,received_by,receipt='',received_at=None):
        self.permit('recepcion')
        if not all(v.strip() for v in (origin,delivered_by,received_by)):raise ValueError('Indica origen y personas que entregan/reciben.')
        stamp=received_at or now()
        # Fecha/hora explícita, sin convertir una fecha de solicitud en recepción.
        import datetime
        try:datetime.datetime.fromisoformat(stamp)
        except ValueError:raise ValueError('Recepción: usa fecha/hora ISO, por ejemplo 2026-09-21T09:30:00-06:00.')
        before=self.s.one('folios',folio)
        with self.db:
            from .directory import Directory
            directory=Directory(self.s)
            refs=[directory.ensure(kind,value,allow_inactive=before[field]==value) for kind,value,field in [('area',origin,'area_origen'),('persona',delivered_by,'entrega'),('persona',received_by,'recibe')]]
            self.db.execute('UPDATE folios SET area_origen=?,entrega=?,recibe=?,acuse=?,recepcion_at=?,fecha_recepcion=? WHERE id=?',
                            (origin,delivered_by,received_by,receipt,stamp,stamp[:10],folio))
            self.db.execute('UPDATE folios SET area_id=?,entrega_id=?,recibe_id=? WHERE id=?',tuple(refs)+(folio,))
            self.s.audit('folios',folio,'recepción',before,self.s.one('folios',folio),'Recepción registrada; validar cada elemento')

    def expect(self,folio,person,legajo,location='',name=''):
        self.permit('recepcion');self.s.one('folios',folio)
        with self.db:
            master=self.master(person,legajo)
            if self.s.rows('SELECT id FROM prestamo_items WHERE folio_id=? AND expediente_id=?',(folio,master)):
                raise ValueError('El expediente ya está en la lista de este folio.')
            self.db.execute('INSERT OR IGNORE INTO personas(curp,nombre) VALUES(?,?)',(curp(person),name))
            item=self.db.execute('INSERT INTO prestamo_items(folio_id,expediente_id,curp_esperada,legajo_esperado,ubicacion_original) VALUES(?,?,?,?,?)',
                (folio,master,curp(person),integer(legajo,1),location)).lastrowid
            from .directory import Directory
            self.db.execute('UPDATE prestamo_items SET ubicacion_id=? WHERE id=?',(Directory(self.s).ensure('ubicacion',location),item))
            self.event(None,'Elemento esperado', 'Registrado en lista de préstamo',item)
            self.receipt_status(folio)
        return item

    def receipt_status(self,folio):
        from .operational_migration import update_receipt
        update_receipt(self.db,folio)

    def unlisted(self,folio,person,legajo,reason,location=''):
        self.permit('recepcion');self.s.one('folios',folio)
        person=curp(person);legajo=integer(legajo,1)
        if not reason.strip():raise ValueError('Indica la discrepancia y evidencia de entrega no relacionada.')
        with self.db:
            master=self.master(person,legajo)
            if self.s.rows('SELECT id FROM prestamo_items WHERE folio_id=? AND expediente_id=?',(folio,master)):raise ValueError('Ese expediente ya tiene un elemento; registra allí la discrepancia.')
            self.db.execute('INSERT OR IGNORE INTO personas(curp,nombre) VALUES(?,?)',(person,''))
            item=self.db.execute("INSERT INTO prestamo_items(folio_id,expediente_id,curp_esperada,curp_recibida,legajo_recibido,validacion,validado_por,validado_at,discrepancia,ubicacion_original,custodia,origen) VALUES(?,?,'',?,?,'Discrepancia',?,?,?,?, 'Con discrepancia','No relacionado')",
                (folio,master,person,legajo,self.s.operador,now(),reason,location)).lastrowid
            from .directory import Directory
            self.db.execute('UPDATE prestamo_items SET ubicacion_id=? WHERE id=?',(Directory(self.s).ensure('ubicacion',location),item))
            self.receipt_status(folio);self.event(None,'Expediente recibido no relacionado',reason,item)
        return item

    def validate_item(self,item,decision,received_curp='',received_legajo=None,reason='',accept_unlisted=False):
        with self.db:
            self._validate_item(item,decision,received_curp,received_legajo,reason,accept_unlisted)

    def _validate_item(self,item,decision,received_curp='',received_legajo=None,reason='',accept_unlisted=False):
        """Validación dentro de la transacción del llamador (individual o por lote)."""
        self.permit('recepcion')
        if decision not in ('Aceptado','Discrepancia','Faltante','Pendiente'):raise ValueError('Validación de recepción inválida.')
        rows=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))
        if not rows:raise ValueError('Elemento inexistente.')
        row=rows[0]
        if row['custodia'] in ('En devolución','Devuelto','Devolución aceptada'):raise ValueError('Este préstamo ya está en devolución.')
        if not reason.strip():raise ValueError('Registra evidencia de la comprobación física.')
        actual=curp(received_curp) if received_curp else None
        leg=integer(received_legajo,1,nullable=True)
        expected=(row['curp_esperada'],row['legajo_esperado'])
        if accept_unlisted and row['origen']=='No relacionado':expected=(row['curp_recibida'],row['legajo_recibido'])
        if decision=='Aceptado' and (actual,leg)!=expected:
            raise ValueError('Para aceptar deben coincidir CURP y legajo comprobados físicamente.')
        if decision=='Aceptado' and (not actual or not leg or not row['expediente_id']):raise ValueError('Confirma primero CURP y legajo esperado de este elemento.')
        self.db.execute('UPDATE prestamo_items SET validacion=?,curp_recibida=?,legajo_recibido=?,validado_por=?,validado_at=?,discrepancia=?,custodia=? WHERE id=?',
            (decision,actual,leg,self.s.operador,now(),reason,'Prestado a Digitalización' if decision=='Aceptado' else 'Con discrepancia' if decision in ('Discrepancia','Faltante') else 'Registrado',item))
        self.receipt_status(row['folio_id'])
        self.s.audit('prestamo_items',item,'validación',row,self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0],reason)
        self.event(None,'Validación de recepción: '+decision,reason,item)

    def create_cycle(self,item):
        self.permit('asignacion')
        row=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0]
        if row['validacion']!='Aceptado':raise ValueError('Valida físicamente este elemento antes de iniciar su ciclo.')
        existing=self.s.rows('SELECT id FROM trabajos WHERE prestamo_item_id=?',(item,))
        if existing:return existing[0]['id']
        person=row['curp_esperada'] or row['curp_recibida'];legajo=row['legajo_esperado'] or row['legajo_recibido']
        name=self.s.rows('SELECT nombre FROM personas WHERE curp=?',(person,))
        ident=self.s.save_work(row['folio_id'],person,name[0]['nombre'] if name else '',legajo)
        return ident

    def assign(self,person,reason,work=None,folio=None,role='Digitalizador',collaborate=False):
        self.permit('asignacion')
        if not person.strip() or not reason.strip() or role not in ('Digitalizador','Revisor','Responsable'):raise ValueError('Indica persona, rol y motivo.')
        if (work is None)==(folio is None):raise ValueError('Selecciona un ciclo o un folio.')
        targets=[self.s.one('trabajos',work)] if work else self.s.rows('SELECT * FROM trabajos WHERE folio_id=? AND activo=1',(folio,))
        if not targets:raise ValueError('El folio no tiene ciclos aceptados.')
        for w in targets:
            item=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(w['prestamo_item_id'],))[0]
            if item['validacion']!='Aceptado' or item['custodia']!='Prestado a Digitalización':raise ValueError('La asignación exige recepción aceptada y préstamo abierto para todos los ciclos elegidos.')
        with self.db:
            from .directory import Directory
            person_id=Directory(self.s).ensure('persona',person)
            for w in targets:
                stamp=now()
                if not collaborate:self.db.execute('UPDATE asignaciones SET fin=? WHERE trabajo_id=? AND rol=? AND fin IS NULL',(stamp,w['id'],role))
                self.db.execute('INSERT INTO asignaciones(trabajo_id,folio_id,persona,rol,inicio,registrado,operador,motivo,origen) VALUES(?,?,?,?,?,?,?,?,?)',
                                (w['id'],folio,person,role,stamp,stamp,self.s.operador,reason,'Confirmada'))
                self.db.execute('UPDATE asignaciones SET persona_id=? WHERE trabajo_id=? AND persona=? AND fin IS NULL',(person_id,w['id'],person))
                if role=='Digitalizador' and not collaborate:self.db.execute('UPDATE trabajos SET digitalizador=?,digitalizador_id=? WHERE id=?',(person,person_id,w['id']))
                self.event(w['id'],'Asignación '+role,person+': '+reason)
        return len(targets)

    def custody(self,item,state,reason,received_by=''):
        self.permit('custodia')
        row=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0]
        transitions={'Prestado a Digitalización':['En devolución','Incidencia de custodia'],'En devolución':['Devuelto','Incidencia de custodia'],
                     'Devuelto':['Devolución aceptada','Incidencia de custodia'],'Incidencia de custodia':['Prestado a Digitalización','En devolución','Devuelto']}
        if state not in transitions.get(row['custodia'],[]):raise ValueError('Movimiento de custodia no permitido desde '+row['custodia'])
        if state in ('Devuelto','Devolución aceptada') and not received_by.strip():raise ValueError('Indica quién recibe/acepta la devolución.')
        with self.db:
            from .directory import Directory
            receiver_id=Directory(self.s).ensure('persona',received_by)
            self.db.execute('UPDATE prestamo_items SET custodia=? WHERE id=?',(state,item))
            if state=='Devuelto':self.db.execute('UPDATE prestamo_items SET devolucion_at=?,devolucion_recibe=?,devolucion_recibe_id=? WHERE id=?',(now(),received_by,receiver_id,item))
            if state=='Devolución aceptada':self.db.execute('UPDATE prestamo_items SET aceptacion_at=? WHERE id=?',(now(),item))
            self.event(None,'Custodia: '+state,reason+(' / Recibe: '+received_by if received_by else ''),item)

    def card_metadata(self,work,note,priority='Normal',tag='',block='',due=None):
        self.permit('tarjeta')
        if priority not in ('Baja','Normal','Alta','Urgente'):raise ValueError('Prioridad inválida.')
        due=date(due)
        with self.db:
            before=self.s.one('trabajos',work)
            self.db.execute('UPDATE trabajos SET notas=?,prioridad=?,etiqueta=?,bloqueo=?,fecha_objetivo=? WHERE id=?',(note,priority,tag,block,due,work))
            self.s.audit('trabajos',work,'tarjeta',before,self.s.one('trabajos',work),'Nota/prioridad sin cambiar etapa')

    def legacy_cycle(self,person,legajo,name=''):
        self.permit('legado')
        # Agrupación técnica explícita para conservar la FK histórica, nunca un folio físico inventado.
        person=curp(person);legajo=integer(legajo,1)
        folio=self.s.save_folio('LEGADO-SIN-FOLIO-'+uuid.uuid4().hex[:12].upper(),'')
        ident=self.s.save_work(folio,person,name,legajo,motivo='Alta técnica de ciclo legado sin folio comprobado')
        with self.db:
            self.db.execute("UPDATE trabajos SET procedencia='Legado importado' WHERE id=?",(ident,))
            self.db.execute("UPDATE folios SET area_origen='Legado sin folio comprobado' WHERE id=?",(folio,))
            self.db.execute("UPDATE prestamo_items SET origen='Contexto técnico legado; no acredita préstamo' WHERE id=?",(self.s.one('trabajos',ident)['prestamo_item_id'],))
            self.event(ident,'Ciclo legado','No existe folio físico confiable; procedencia y custodia sin confirmar')
        return ident

    def confirm_legacy_link(self,work,reason):
        self.permit('asignacion');w=self.s.one('trabajos',work)
        if not reason.strip():raise ValueError('Documenta cómo verificaste la identidad y el contexto del ciclo.')
        master=self.s.rows('SELECT * FROM expedientes WHERE id=?',(w['expediente_id'],))
        if not master or (master[0]['curp'],master[0]['legajo'])!=(curp(w['curp']),w['legajo']):
            raise ValueError('El vínculo requiere revisión de identidad; no se modificaron los registros originales.')
        with self.db:
            self.db.execute('UPDATE trabajos SET conciliacion_pendiente=0 WHERE id=?',(work,))
            self.event(work,'Vínculo histórico confirmado',reason+'; se conservan los ciclos y archivos separados')
