"""Expediente 360, Kanban derivado y hechos exportables sin sumar entregas."""
import datetime as dt
import html
import json
import uuid
from .core import now
from .delivery import Deliveries
from .operations import KANBAN


class Reporting:
    def __init__(self,store):self.s=store

    def card(self,work):
        w=self.s.one('trabajos',work);folio=self.s.one('folios',w['folio_id'])
        item=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(w['prestamo_item_id'],))
        custody=item[0]['custodia'] if item else 'Pendiente de conciliación'
        observations=self.s.rows("SELECT o.* FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE e.trabajo_id=? AND o.estado IN ('Abierta','En corrección')",(work,))
        corrections=self.s.rows("SELECT c.id FROM correcciones_tiff c JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=? AND c.estado='Pendiente'",(work,))
        files=self.s.rows('SELECT paginas FROM archivos_tiff WHERE trabajo_id=? AND activo=1',(work,))
        validation=Deliveries(self.s).current_validation(work)
        state=w['estado']
        if observations or state.startswith('Correcciones') or corrections:column=KANBAN[3]
        elif state in ('Listo para aprobación','Expediente cerrado'):column=KANBAN[4]
        elif state=='Revisión en curso':column=KANBAN[2]
        elif state=='Recibido':column=KANBAN[0]
        else:column=KANBAN[1]
        if state=='Expediente cerrado' and validation is None:
            column=KANBAN[2];w=dict(w,calidad='Validación obsoleta; revisar aprobación histórica')
        assignments=self.s.rows("SELECT persona FROM asignaciones WHERE trabajo_id=? AND fin IS NULL AND rol IN ('Revisor','Responsable')",(work,))
        elapsed=None
        if w['procedencia']=='Registrado' or self.s.rows('SELECT id FROM eventos_operativos WHERE trabajo_id=?',(work,)):
            try:
                start=dt.datetime.fromisoformat(w['estado_desde'])
                if start.tzinfo:elapsed=max(0,round((dt.datetime.now().astimezone()-start).total_seconds()/3600,2))
            except ValueError:pass
        return dict(w,folio=folio['numero'],custodia=custody,columna=column,observaciones=len(observations),reescaneos=len(corrections),
                    tiff_activos=len(files),paginas=sum(r['paginas'] for r in files),validacion=validation['resultado'] if validation else 'Sin vigencia',
                    responsable=' / '.join(r['persona'] for r in assignments),horas_etapa=elapsed)

    def cards(self,**filters):
        result=[]
        # Una tarjeta por ciclo vigente seleccionado del maestro; el historial conserva los demás.
        for work in self.s.works():
            row=self.card(work['id'])
            if any(value and str(value).casefold() not in str(row.get(key,'')).casefold() for key,value in filters.items() if key!='con_observaciones'):continue
            if filters.get('con_observaciones')=='Sí' and not row['observaciones']:continue
            if filters.get('con_observaciones')=='No' and row['observaciones']:continue
            result.append(row)
        return result

    def summary(self,work):
        w=self.s.one('trabajos',work);master=w['expediente_id'];folio=self.s.one('folios',w['folio_id'])
        name=self.s.rows('SELECT nombre FROM personas WHERE curp=?',(w['curp'],))
        item=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(w['prestamo_item_id'],))
        assignments=self.s.rows('SELECT * FROM asignaciones WHERE trabajo_id=? ORDER BY id',(work,))
        inventory=Deliveries(self.s).inventory(work);validation=Deliveries(self.s).current_validation(work)
        deliveries=self.s.rows('SELECT id,numero,creado,operador,estado,manifest_hash,inventario_hash,ruta FROM entregas WHERE trabajo_id=? ORDER BY numero',(work,))
        published=[d for d in deliveries if d['estado'] not in ('Preparando','Incompleta')]
        changes=None
        if published:
            try:changes=Deliveries(self.s).diff(published[-2]['id'] if len(published)>1 else None,published[-1]['id'])
            except (ValueError,OSError) as error:changes={'error':str(error)}
        digital=dict(inventory['totales']);digital['procedencia']='Derivado del inventario activo; consultar validación'
        if not self.s.rows('SELECT id FROM archivos_tiff WHERE trabajo_id=?',(work,)) and not self.s.rows('SELECT id FROM validaciones WHERE trabajo_id=?',(work,)):
            digital={k:None for k in digital};digital['procedencia']='Sin inventario registrado; no equivale a cero digitalizado'
        card=self.card(work)
        observations=self.s.rows('SELECT o.* FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE e.trabajo_id=? ORDER BY o.id',(work,))
        events=self.s.rows('SELECT fecha,operador,evento,motivo FROM eventos_operativos WHERE trabajo_id=? OR prestamo_item_id=? ORDER BY fecha,id',(work,w['prestamo_item_id']))
        events+=self.s.rows('''SELECT fecha,operador,accion AS evento,motivo FROM auditoria WHERE
            (entidad='trabajos' AND registro=?) OR (entidad='folios' AND registro=?) OR
            (entidad='archivos_tiff' AND registro IN (SELECT CAST(id AS TEXT) FROM archivos_tiff WHERE trabajo_id=?)) OR
            (entidad='conteos' AND registro IN (SELECT CAST(id AS TEXT) FROM conteos WHERE trabajo_id=?)) OR
            (entidad='incidencias' AND registro IN (SELECT CAST(id AS TEXT) FROM incidencias WHERE trabajo_id=?))''',(str(work),str(w['folio_id']),work,work,work))
        events.sort(key=lambda e:e['fecha'])
        return {'Identificación':{'CURP':w['curp'],'Nombre':name[0]['nombre'] if name else '', 'Legajo':w['legajo'],'ID expediente':master,'Ciclo actual':work,'Folio actual':folio['numero']},
                'Legajos de la misma CURP':self.s.rows('SELECT e.id,e.legajo FROM expedientes e WHERE e.curp=? ORDER BY e.legajo',(w['curp'],)),
                'Lista de origen':self.s.rows('SELECT l.creado,l.hoja,f.nombre AS archivo,r.resultado,r.detalle,o.fila,o.contenido FROM lista_registros r JOIN listas_importadas l ON l.id=r.lista_id JOIN fuentes f ON f.id=l.fuente_id JOIN origen o ON o.id=r.origen_id WHERE r.prestamo_item_id=? OR r.prestamo_item_id=(SELECT lista_padre_id FROM prestamo_items WHERE id=?)',(w['prestamo_item_id'],w['prestamo_item_id'])),
                'Ciclos históricos':self.s.associated(work),'Custodia física':dict(item[0],area_origen=folio['area_origen'],entrega=folio['entrega'],recibe=folio['recibe'],recepcion_at=folio['recepcion_at'],acuse=folio['acuse']) if item else {'estado':'Pendiente de conciliación'},
                'Asignaciones':assignments,'Proceso':{'Estado':w['estado'],'Calidad':card['calidad'],'Kanban':card['columna'],'Inicio registrado':w['estado_desde'],'Horas en etapa con cobertura':card['horas_etapa'],'Procedencia':w['procedencia'],'Conciliación pendiente':bool(w['conciliacion_pendiente'])},
                'Conteo físico':{'Hojas confirmadas':w['fisicos'],'Fuera del broche (ya incluidas)':w['fuera_broche'],'Bloques':self.s.rows('SELECT * FROM conteos WHERE trabajo_id=?',(work,))},
                'Digital vigente':digital,'Dato legado declarado':{'No_digitales':w['digitales_declarados'],'Uso':'Conciliación; no determina TIFF vigentes'},
                'Validación':{'Resultado actual':inventory['resultado'],'Última validación vigente':validation,'Problemas':inventory['problemas']},
                'Entregas':deliveries,'Cambios de última entrega':changes,'Observaciones':observations,
                'Reescaneos':self.s.rows('SELECT c.* FROM correcciones_tiff c JOIN archivos_tiff a ON a.id=c.archivo_id WHERE a.trabajo_id=?',(work,)),
                'Revisiones':self.s.rows('SELECT r.* FROM sesiones_revision r JOIN entregas e ON e.id=r.entrega_id WHERE e.trabajo_id=?',(work,)),
                'Importaciones históricas':self.s.rows('SELECT * FROM importaciones_legado WHERE trabajo_id=? ORDER BY fecha',(work,)),
                'Incidencias':self.s.rows('SELECT * FROM incidencias WHERE trabajo_id=?',(work,)),
                'Historial de etapas':self.s.rows('SELECT * FROM historial WHERE trabajo_id=? ORDER BY id',(work,)),
                'Línea de tiempo':events}

    def export_summary(self,work):
        data=self.summary(work);out=self.s.workspace.reports/('expediente360_'+str(work)+'_'+uuid.uuid4().hex+'.html');out.parent.mkdir(parents=True,exist_ok=True)
        def render(value):
            if value is None:return '<em>Sin dato confirmado</em>'
            if isinstance(value,dict):return '<table>'+''.join('<tr><th>'+html.escape(str(k))+'</th><td>'+render(v)+'</td></tr>' for k,v in value.items())+'</table>'
            if isinstance(value,list):return ''.join('<div class="registro">'+render(v)+'</div>' for v in value) or '<em>Sin registros</em>'
            return html.escape(str(value))
        content='<html lang="es"><meta charset="utf-8"><title>Expediente 360</title><style>body{font:14px sans-serif;max-width:1100px;margin:25px auto}table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border:1px solid #ccc;text-align:left;padding:6px;vertical-align:top;overflow-wrap:anywhere}th{width:25%}.registro{margin:10px 0}h2{page-break-after:avoid}@media print{body{font-size:11px}}</style><h1>Expediente 360</h1><p>Generado '+html.escape(now())+' · '+html.escape(self.s.operador)+'</p>'
        content+=''.join('<h2>'+html.escape(k)+'</h2>'+render(v) for k,v in data.items())+'</html>'
        with out.open('x',encoding='utf-8') as f:f.write(content)
        return out

    def facts(self):
        works=self.s.works();ids=[w['id'] for w in works];files=[]
        for ident in ids:files+=self.s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=? AND activo=1',(ident,))
        received=self.s.rows('SELECT id,recepcion_at FROM folios WHERE recepcion_at IS NOT NULL')
        loans=self.s.rows("SELECT id FROM prestamo_items WHERE custodia IN ('Recibido por Digitalización','Prestado a Digitalización','En devolución','Incidencia de custodia')")
        approvals=self.s.rows("SELECT trabajo_id,MIN(numero) AS primera_aprobada FROM entregas WHERE estado='Aprobada' GROUP BY trabajo_id")
        corrected={r['trabajo_id'] for r in self.s.rows('SELECT DISTINCT e.trabajo_id FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada')}
        durations={};coverage=0
        for h in self.s.rows('SELECT * FROM historial WHERE fin IS NOT NULL'):
            if 'Alta técnica' in h['motivo']:continue
            try:
                start=dt.datetime.fromisoformat(h['inicio']);end=dt.datetime.fromisoformat(h['fin'])
                if not start.tzinfo or not end.tzinfo or end<start:continue
                hours=(end-start).total_seconds()/3600;durations.setdefault(h['estado'],[]).append(hours);coverage+=1
            except ValueError:continue
        hashes={}
        for f in files:hashes[f['hash_actual']]=hashes.get(f['hash_actual'],0)+1
        total_cycles=self.s.db.execute('SELECT COUNT(*) FROM trabajos').fetchone()[0]
        per_operator={};per_stage={};differences=[]
        for w in works:
            active=[f for f in files if f['trabajo_id']==w['id']];operator=w['digitalizador'] or 'Sin asignar'
            p=per_operator.setdefault(operator,{'ciclos':0,'tiff':0,'paginas':0});p['ciclos']+=1;p['tiff']+=len(active);p['paginas']+=sum(f['paginas'] for f in active)
            per_stage[w['estado']]=per_stage.get(w['estado'],0)+1
            differences.append({'trabajo_id':w['id'],'declarados':w['digitales_declarados'],'activos':len(active),'diferencia':len(active)-w['digitales_declarados'] if w['digitales_declarados'] is not None else None})
        return {'folios_con_recepcion_confirmada':len(received),'folios_por_periodo':received,'prestamos_abiertos':len(loans),'por_digitalizador':per_operator,'por_etapa':per_stage,
                'observaciones_por_codigo':self.s.rows('SELECT i.codigo,COUNT(*) AS cantidad FROM observaciones_revision o JOIN entrega_items i ON i.entrega_id=o.entrega_detectada AND i.version_id=o.version_id GROUP BY i.codigo'),
                'observaciones_por_entrega':self.s.rows('SELECT entrega_detectada,COUNT(*) AS cantidad FROM observaciones_revision GROUP BY entrega_detectada'),
                'diferencias_legado':differences,
                'ciclos_vigentes':len(works),'tiff_activos':len(files),'paginas_registradas':sum(f['paginas'] for f in files),
                'requieren_correccion':len(corrected),'porcentaje_ciclos_con_observaciones':round(100*len(corrected)/total_cycles,2) if total_cycles else None,
                'aprobados_primer_intento':sum(r['primera_aprobada']==1 for r in approvals),'aprobados_entrega_posterior':sum(r['primera_aprobada']>1 for r in approvals),
                'grupos_duplicados_exactos':sum(n>1 for n in hashes.values()),'reescaneos':self.s.db.execute('SELECT COUNT(*) FROM correcciones_tiff').fetchone()[0],
                'importaciones_historicas':self.s.rows('SELECT estado,COUNT(*) AS cantidad FROM importaciones_legado GROUP BY estado'),
                'promedio_horas_etapa':{k:round(sum(v)/len(v),2) for k,v in durations.items()},'intervalos_con_fechas_confiables':coverage,
                'intervalos_totales':self.s.db.execute('SELECT COUNT(*) FROM historial').fetchone()[0],
                'cobertura':'Los tiempos sin inicio/fin confiables no se estiman; conteos digitales desde archivos activos, sin sumar entregas.'}

    def export_datasets(self,folder):
        tables=('expedientes','folios','personas','prestamo_items','asignaciones','eventos_operativos','documentos_logicos','versiones_archivo','entregas','entrega_items','validaciones','sesiones_revision','observaciones_revision','observacion_historial','importaciones_legado','importacion_items','directorio','directorio_alias','listas_importadas','lista_registros','fuentes','origen')
        for table in tables:self.s.csv_write(folder/(table+'.csv'),self.s.rows('SELECT * FROM '+table))
        with (folder/'hechos_operativos.json').open('x',encoding='utf-8') as f:json.dump(self.facts(),f,ensure_ascii=False,indent=2)
