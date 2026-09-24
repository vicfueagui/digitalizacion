"""Aceptación explícita de una selección; usa la identidad de la lista sin recaptura."""
from .core import curp,integer,now
from .operations import Operations
from .intake import create_draft


class Reception:
    def __init__(self,store,role='Responsable'):
        self.s=store;self.db=store.db;self.ops=Operations(store,role)

    def preview(self,folio,items,default_legajo=None):
        self.ops.permit('recepcion');f=self.s.one('folios',folio)
        if not f['activo']:raise ValueError('Reactiva el folio antes de aceptar expedientes.')
        ids=list(dict.fromkeys(integer(i,1) for i in items))
        if not ids:raise ValueError('Selecciona uno o varios expedientes de la lista.')
        default_legajo=integer(default_legajo,1,nullable=True);rows=[];identities=set()
        for ident in ids:
            found=self.s.rows('SELECT i.*,p.nombre FROM prestamo_items i LEFT JOIN personas p ON p.curp=i.curp_esperada WHERE i.id=?',(ident,))
            if not found or found[0]['folio_id']!=folio:raise ValueError('La selección contiene un elemento ajeno al folio.')
            row=found[0];leg=row['legajo_esperado'] or default_legajo;errors=[]
            try:person=curp(row['curp_esperada'])
            except ValueError:person=row['curp_esperada'];errors.append('Sin CURP esperada válida; usa Revisar diferencia.')
            if row['origen']=='No relacionado' or row['validacion'] in ('Discrepancia','Faltante'):
                errors.append('Requiere aclaración individual en Revisar diferencia.')
            if row['custodia'] not in ('Registrado','Recibido por Digitalización','Prestado a Digitalización'):
                errors.append('La custodia actual no permite aceptación rápida.')
            if leg is None:errors.append('Indica el legajo para los elementos que no lo tienen.')
            if leg is not None:
                identity=(person,leg)
                if identity in identities:errors.append('CURP/legajo repetido en la selección.')
                identities.add(identity)
                if self.s.rows('SELECT id FROM prestamo_items WHERE folio_id=? AND curp_esperada=? AND legajo_esperado=? AND id<>?',(folio,person,leg,ident)):
                    errors.append('Ya existe ese legajo en otro elemento; revisa antes de conciliar.')
            cycles=self.s.rows('SELECT id,activo,prestamo_item_id FROM trabajos WHERE folio_id=? AND curp=? AND legajo=?',(folio,person,leg))
            if any(not w['activo'] or w['prestamo_item_id']!=ident for w in cycles):
                errors.append('Existe un ciclo inactivo o asociado a otro elemento; requiere revisión.')
            rows.append(dict(row,legajo_propuesto=leg,legajo_nuevo=row['legajo_esperado'] is None,
                             resultado='Revisar' if errors else 'Ya aceptado' if row['validacion']=='Aceptado' else 'Listo para aceptar',
                             errores=errors))
        return rows

    def accept(self,folio,items,reason,confirmed=False,default_legajo=None):
        if not confirmed:raise ValueError('Confirma que cotejaste los físicos con la lista seleccionada.')
        if not reason.strip():raise ValueError('Falta la evidencia de recepción.')
        result={'aceptados':0,'ya_aceptados':0,'legajos_confirmados':0,'ciclos':[]}
        with self.db:
            rows=self.preview(folio,items,default_legajo)
            blocked=[r for r in rows if r['errores']]
            if blocked:raise ValueError('No se aceptó la selección: '+str(blocked[0]['curp_esperada'])+' · '+'; '.join(blocked[0]['errores']))
            for row in rows:
                ident=row['id'];person=row['curp_esperada'];leg=row['legajo_propuesto']
                if row['legajo_nuevo']:
                    master=self.ops.master(person,leg)
                    self.db.execute('UPDATE prestamo_items SET legajo_esperado=?,expediente_id=? WHERE id=?',(leg,master,ident))
                    self.db.execute("UPDATE pendientes SET estado='Revisado' WHERE tipo='Legajo de lista por confirmar' AND origen_id IN (SELECT origen_id FROM lista_registros WHERE prestamo_item_id=?)",(ident,))
                    self.s.audit('prestamo_items',ident,'confirmar legajo en recepción',row,{'legajo':leg},reason)
                    result['legajos_confirmados']+=1
                work=create_draft(self.s,ident)
                if work is None:raise ValueError('El elemento no tiene una identidad física confirmada.')
                if row['validacion']!='Aceptado':
                    self.ops._validate_item(ident,'Aceptado',person,leg,reason)
                    result['aceptados']+=1
                else:result['ya_aceptados']+=1
                # Solo acredita la fecha de este elemento; no inventa el acuse/recepción del folio completo.
                if row['validacion']!='Aceptado':
                    before=self.s.one('trabajos',work)
                    if not before['recibido']:
                        self.db.execute('UPDATE trabajos SET recibido=? WHERE id=?',(now()[:10],work))
                        self.s.audit('trabajos',work,'fecha de recepción individual',before,self.s.one('trabajos',work),reason)
                result['ciclos'].append(work)
            self.ops.receipt_status(folio)
        return result
