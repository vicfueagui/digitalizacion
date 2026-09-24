"""Revisión de una entrega exacta y resolución explícita de observaciones."""
import uuid
from .core import now,integer
from .delivery import Deliveries,content_hash
from .operations import Operations

OBSERVATION_TYPES=['Expediente','Conteo','Código/nombre','Carpeta incorrecta','Documento faltante','Documento sobrante','Calidad de imagen','Orientación/recorte','Hoja física','Otro']


class Reviews:
    def __init__(self,store,role='Responsable'):
        self.s=store;self.db=store.db;self.ops=Operations(store,role);self.deliveries=Deliveries(store,role)

    def state(self,work,state,quality,reason):
        w=self.s.one('trabajos',work);stamp=now()
        if w['estado']!=state:
            self.db.execute('UPDATE historial SET fin=? WHERE trabajo_id=? AND fin IS NULL',(stamp,work))
            self.db.execute('INSERT INTO historial(trabajo_id,estado,inicio,motivo,operador) VALUES(?,?,?,?,?)',(work,state,stamp,reason,self.s.operador))
            self.db.execute('UPDATE trabajos SET estado=?,estado_desde=? WHERE id=?',(state,stamp,work))
        self.db.execute('UPDATE trabajos SET calidad=? WHERE id=?',(quality,work))
        self.ops.event(work,state,reason)

    def begin(self,delivery):
        self.ops.permit('revision');self.deliveries.verify(delivery);d=self.deliveries.get(delivery)
        ident=uuid.uuid4().hex
        with self.db:
            self.db.execute('INSERT INTO sesiones_revision(id,entrega_id,revisor,inicio) VALUES(?,?,?,?)',(ident,delivery,self.s.operador,now()))
            self.db.execute("UPDATE entregas SET estado='En revisión' WHERE id=?",(delivery,))
            self.state(d['trabajo_id'],'Revisión en curso','En revisión','Revisar entrega '+str(d['numero']))
        return ident

    def observe(self,session,kind,description,responsible,document=None,version=None,page=None,location='',evidence='',blocking=True):
        self.ops.permit('observar')
        sessions=self.s.rows('SELECT * FROM sesiones_revision WHERE id=?',(session,))
        if not sessions or sessions[0]['fin']:raise ValueError('La sesión no está abierta.')
        if kind not in OBSERVATION_TYPES or not description.strip() or not responsible.strip():raise ValueError('Indica tipo, descripción y responsable de corregir.')
        delivery=sessions[0]['entrega_id'];manifest=self.deliveries.verify(delivery)
        if version and not document:raise ValueError('Selecciona también el documento de la versión.')
        if document:
            match=next((i for i in manifest['items'] if i['document_asset_id']==document),None)
            if not match or (version and version!=match['file_version_id']):raise ValueError('Documento/versión ajenos a la entrega revisada.')
            version=match['file_version_id']
            if page is not None:
                page=integer(page,1)
                if page>match['paginas']:raise ValueError('Página fuera del TIFF de esta entrega.')
        elif page is not None:raise ValueError('Una página requiere documento/version de esta entrega.')
        work=self.deliveries.get(delivery)['trabajo_id']
        with self.db:
            from .directory import Directory
            responsible_id=Directory(self.s).ensure('persona',responsible)
            ident=self.db.execute('INSERT INTO observaciones_revision(sesion_id,entrega_detectada,documento_id,version_id,pagina,ubicacion_fisica,tipo,descripcion,evidencia,creador,creado,responsable,bloqueante) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (session,delivery,document,version,page,location,kind,description,evidence,self.s.operador,now(),responsible,int(bool(blocking)))).lastrowid
            self.db.execute('UPDATE observaciones_revision SET responsable_id=? WHERE id=?',(responsible_id,ident))
            self.history(ident,'Abierta',description,delivery)
            self.db.execute('UPDATE validaciones SET vigente=0 WHERE trabajo_id=?',(work,))
            self.db.execute("UPDATE entregas SET estado='Con observaciones' WHERE id=?",(delivery,))
            self.state(work,'Correcciones solicitadas','Con observaciones','Observación '+str(ident)+': '+description)
        return ident

    def history(self,ident,state,response,delivery):
        self.db.execute('INSERT INTO observacion_historial(observacion_id,fecha,operador,estado,respuesta,entrega_id) VALUES(?,?,?,?,?,?)',(ident,now(),self.s.operador,state,response,delivery))

    def update_observation(self,ident,state,response,delivery=None):
        self.ops.permit('observar' if state in ('Validada','Anulada','Abierta') else 'corregir')
        rows=self.s.rows('SELECT * FROM observaciones_revision WHERE id=?',(ident,))
        if not rows or not response.strip():raise ValueError('Indica la observación y respuesta/evidencia.')
        old=rows[0];origin=self.deliveries.get(old['entrega_detectada']);work=origin['trabajo_id']
        transitions={'Abierta':['En corrección','Resuelta','Anulada'],'En corrección':['Resuelta','Anulada'],'Resuelta':['Validada','Abierta','Anulada'],'Validada':['Abierta'],'Anulada':['Abierta']}
        if state not in transitions.get(old['estado'],[]):raise ValueError('Transición de observación inválida.')
        if state=='Resuelta':
            if not delivery:raise ValueError('La respuesta debe señalar una nueva entrega corregida.')
            target=self.deliveries.get(delivery);self.deliveries.verify(delivery)
            if target['trabajo_id']!=work or target['numero']<=origin['numero']:raise ValueError('Debe ser una entrega posterior del mismo ciclo.')
        elif state=='Validada':
            delivery=old['entrega_resuelta']
            if not delivery:raise ValueError('Falta la entrega donde se corrigió.')
            self.deliveries.verify(delivery)
        elif state in ('Abierta','En corrección'):delivery=None
        with self.db:
            self.db.execute('UPDATE observaciones_revision SET estado=?,respuesta=?,entrega_resuelta=? WHERE id=?',(state,response,delivery,ident))
            self.history(ident,state,response,delivery)
            self.db.execute('UPDATE validaciones SET vigente=0 WHERE trabajo_id=?',(work,))
            if state in ('Abierta','En corrección'):
                self.state(work,'Correcciones en curso' if state=='En corrección' else 'Correcciones solicitadas','Con observaciones',response)
            else:
                pending=self.s.rows("SELECT o.id FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE e.trabajo_id=? AND o.estado IN ('Abierta','En corrección')",(work,))
                if not pending:self.state(work,'Revisión en curso','Corregido / reenviado',response)
            self.ops.event(work,'Observación '+str(ident)+': '+state,response)

    def approve(self,delivery,reason):
        self.ops.permit('aprobar')
        if not reason.strip():raise ValueError('Indica evidencia de la aprobación.')
        d=self.deliveries.get(delivery);work=d['trabajo_id'];self.deliveries.verify(delivery)
        latest=self.s.rows("SELECT id FROM entregas WHERE trabajo_id=? AND estado NOT IN ('Preparando','Incompleta') ORDER BY numero DESC LIMIT 1",(work,))
        if not latest or latest[0]['id']!=delivery:raise ValueError('Solo puede aprobarse la entrega más reciente del ciclo.')
        if not self.s.rows('SELECT id FROM sesiones_revision WHERE entrega_id=?',(delivery,)):raise ValueError('Abre la sesión de revisión de esta entrega antes de aprobar.')
        report=self.deliveries.validate(work,final=True,delivery=delivery)
        if report['resultado'] not in ('OK','OK con advertencias'):raise ValueError('Aprobación bloqueada: '+'; '.join(i['mensaje'] for i in report['problemas']))
        if content_hash(report['items'])!=d['inventario_hash']:raise ValueError('El inventario actual cambió. Genera y revisa una nueva entrega.')
        with self.db:
            self.db.execute("UPDATE entregas SET estado='Aprobada' WHERE id=?",(delivery,))
            self.db.execute("UPDATE sesiones_revision SET estado='Aprobada',fin=? WHERE entrega_id=? AND fin IS NULL",(now(),delivery))
            self.state(work,'Expediente cerrado','Aprobado',reason)
        return delivery
