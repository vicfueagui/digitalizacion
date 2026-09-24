"""Indicadores del ámbito visible. Solo metadatos; nunca lee los TIFF al dibujar."""
import datetime
import json
from pathlib import Path
from .core import STATES

STAGES=[('Por iniciar',STATES[:1],'#526c80'),('En digitalización',STATES[1:7],'#237c94'),
        ('En revisión',STATES[7:8],'#6960a5'),('En corrección',STATES[8:10],'#b56925'),
        ('Por aprobar',STATES[10:11],'#308080'),('Cerrados',STATES[11:],'#347657')]


def percentage(value,total):return round(value*100/total,1) if total else None


class Dashboard:
    def __init__(self,store):self.s=store
    def snapshot(self,works,filters=None):
        works=[dict(w) for w in works if w['activo']];total=len(works);ids={w['id'] for w in works}
        # Store.dashboard incluye comprobación de vigencia sobre los binarios. Este
        # panel informa metadatos registrados y reserva esa validación para 360.
        incidents=self.s.rows("SELECT trabajo_id,COUNT(*) AS n FROM incidencias WHERE estado='Abierta' GROUP BY trabajo_id")
        observations=self.s.rows("SELECT e.trabajo_id,COUNT(*) AS n FROM observaciones_revision o JOIN entregas e ON e.id=o.entrega_detectada WHERE o.estado IN ('Abierta','En corrección') GROUP BY e.trabajo_id")
        stale={r['trabajo_id'] for r in self.s.rows('SELECT trabajo_id FROM inventario_pendiente')}
        metrics={'Trabajos activos':total,'CURP distintas':len({w['curp'] for w in works}),
                 'Archivos TIFF':sum(w.get('total_tiff',0) for w in works),'Páginas conocidas':sum(w.get('total_paginas',0) for w in works),
                 'Hojas físicas confirmadas':sum(w['fisicos'] or 0 for w in works),'Sin conteo confirmado':sum(w['fisicos'] is None for w in works),
                 'Recepción pendiente':sum(w.get('recepcion')!='Aceptado' for w in works),
                 'Sin digitalizador asignado':sum(not w['digitalizador'].strip() for w in works),
                 'Cerrados':sum(w['estado']==STATES[-1] for w in works),
                 'Incidencias abiertas':sum(r['n'] for r in incidents if r['trabajo_id'] in ids),
                 'Observaciones abiertas':sum(r['n'] for r in observations if r['trabajo_id'] in ids),
                 'Inventarios desactualizados':len(stale & ids),
                 'Identidades con registros asociados':sum(w.get('registros',1)>1 for w in works)}
        metrics['Avance de cierre (%)']=percentage(metrics['Cerrados'],total)
        stages=[{'label':label,'value':sum(w['estado'] in states for w in works),'total':total,'color':color,
                 'ids':[w['id'] for w in works if w['estado'] in states]} for label,states,color in STAGES]
        for row in stages:row['percent']=percentage(row['value'],total)
        conditions=[('Recepción aceptada',lambda w:w.get('recepcion')=='Aceptado'),
                    ('Con responsable',lambda w:bool(w['digitalizador'].strip())),
                    ('Conteo confirmado',lambda w:w['fisicos'] is not None),
                    ('Con TIFF registrados',lambda w:w.get('total_tiff',0)>0),
                    ('Cierre registrado',lambda w:w['estado']==STATES[-1])]
        coverage=[]
        for label,condition in conditions:
            ids=[w['id'] for w in works if condition(w)]
            coverage.append({'label':label,'value':len(ids),'total':total,'percent':percentage(len(ids),total),'ids':ids,'color':'#267e78'})
        groups={}
        for field in ('folio','digitalizador'):
            grouped={}
            for w in works:
                name=w[field] or 'Sin asignar'
                row=grouped.setdefault(name,{'grupo':name,'expedientes':0,'tiff':0,'paginas':0,'aceptados':0,'cerrados':0,'ids':[]})
                row['expedientes']+=1;row['tiff']+=w.get('total_tiff',0);row['paginas']+=w.get('total_paginas',0)
                row['aceptados']+=w.get('recepcion')=='Aceptado';row['cerrados']+=w['estado']==STATES[-1];row['ids'].append(w['id'])
            groups[field]=[dict(row,cierre=percentage(row['cerrados'],row['expedientes'])) for name,row in sorted(grouped.items())]
        pending=self.s.db.execute('SELECT COUNT(*) FROM prestamo_items i JOIN folios f ON f.id=i.folio_id WHERE f.activo=1 AND NOT EXISTS(SELECT 1 FROM trabajos t WHERE t.prestamo_item_id=i.id)').fetchone()[0]
        return {'generado':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'filtros':dict(filters or {}),
                'metrica':metrics,'etapas':stages,'cobertura':coverage,'grupos':groups,'expedientes':works,
                'sin_ciclo_global':pending,'alcance':'Ciclos vigentes activos de la vista; sin sumar entregas ni ciclos históricos.',
                'advertencia':'Los estados y conteos son registrados; no sustituyen la validación del contenido en Expediente 360.'}

    def export(self,snapshot,destination):
        folder=Path(destination);folder.mkdir(parents=True,exist_ok=False)
        self.s.csv_write(folder/'indicadores.csv',[{'indicador':k,'valor':v} for k,v in snapshot['metrica'].items()])
        for key in ('etapas','cobertura'):
            self.s.csv_write(folder/(key+'.csv'),[{'indicador':r['label'],'cantidad':r['value'],'base':r['total'],'porcentaje':r['percent']} for r in snapshot[key]])
        for key,rows in snapshot['grupos'].items():
            self.s.csv_write(folder/('por_'+key+'.csv'),[{k:v for k,v in row.items() if k!='ids'} for row in rows])
        self.s.csv_write(folder/'expedientes.csv',snapshot['expedientes'])
        with (folder/'contexto.json').open('x',encoding='utf-8') as stream:
            json.dump({k:snapshot[k] for k in ('generado','filtros','alcance','advertencia','sin_ciclo_global')},stream,ensure_ascii=False,indent=2)
        return folder
