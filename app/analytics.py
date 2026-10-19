"""Cubo local de metadatos: inventario por recepción o eventos de importación.

No suma snapshots de entregas ni atribuye al mes actual recepciones desconocidas.
"""
import datetime as dt
import json
from pathlib import Path
from .core import now,date

PERIODS=('Año','Mes','Semana ISO','Día')
DIMENSIONS=('Folio','Digitalizador','Etapa actual')
SOURCES=('Inventario por recepción','Ingresos TIFF')


def day(value):
    if not value:return None
    try:
        parsed=dt.datetime.fromisoformat(value)
        return parsed.astimezone().date() if parsed.tzinfo else parsed.date()
    except (ValueError,TypeError):return None


def bucket(value,period):
    if value is None:return 'Sin fecha'
    if period=='Año':return str(value.year)
    if period=='Mes':return value.strftime('%Y-%m')
    if period=='Semana ISO':
        year,week,_=value.isocalendar();return '{}-S{:02d}'.format(year,week)
    if period=='Día':return value.isoformat()
    raise ValueError('Periodo desconocido')


class Cube:
    def __init__(self,store):self.s=store

    def snapshot(self,works,period='Mes',dimension='Folio',source=SOURCES[0],start='',end='',folio=''):
        if period not in PERIODS or dimension not in DIMENSIONS or source not in SOURCES:raise ValueError('Configuración del cubo no válida.')
        first=date(start);last=date(end)
        if first and last and first>last:raise ValueError('La fecha inicial supera a la final.')
        scope={r['id']:r for r in works if r['activo']}
        from .directory import normalized
        placeholders=','.join('?' for _ in scope) or 'NULL'
        integrations={r['id']:r for r in self.s.rows('SELECT i.*,f.numero AS folio FROM integraciones i JOIN folios f ON f.id=i.folio_id WHERE i.trabajo_id IN ('+placeholders+')',tuple(scope))
                      if not folio or normalized(folio) in normalized(r['folio'])}
        facts=[]
        if source==SOURCES[0]:
            grouped_files={r['integracion_id']:r for r in self.s.rows('SELECT integracion_id,COUNT(*) AS tiff,SUM(paginas) AS paginas FROM archivos_tiff WHERE activo=1 AND trabajo_id IN ('+placeholders+') GROUP BY integracion_id',tuple(scope))}
            for row in integrations.values():
                active=grouped_files.get(row['id'],{'tiff':0,'paginas':0})
                facts.append(dict(row,fecha=row['recibido'],hojas=row['fisicos'] or 0,pendientes=int(row['fisicos'] is None),
                                  tiff=active['tiff'],paginas=active['paginas'],nuevas=int(row['numero']>0)))
        else:
            files=self.s.rows('SELECT id,integracion_ingreso_id,paginas,importado FROM archivos_tiff a WHERE trabajo_id IN ('+placeholders+') AND NOT EXISTS(SELECT 1 FROM procedencia_paginas p WHERE p.archivo_id=a.id)',tuple(scope))
            for file in files:
                row=integrations.get(file['integracion_ingreso_id'])
                if row:facts.append(dict(row,fecha=file['importado'],hojas=0,pendientes=0,tiff=1,paginas=file['paginas'],nuevas=0,archivo_id=file['id']))
        groups={};unknown=0;excluded_unknown=0
        for fact in facts:
            stamp=day(fact['fecha'])
            if stamp is None:
                unknown+=1
                if first or last:excluded_unknown+=1;continue
            elif (first and stamp.isoformat()<first) or (last and stamp.isoformat()>last):continue
            work=scope[fact['trabajo_id']]
            dimension_value=fact['folio'] if dimension=='Folio' else fact['digitalizador'] or 'Sin asignar' if dimension=='Digitalizador' else work['estado']
            key=(bucket(stamp,period),dimension_value)
            row=groups.setdefault(key,dict(periodo=key[0],grupo=key[1],hojas=0,pendientes=0,tiff=0,paginas=0,integraciones=0,ids=set(),lotes=set()))
            for field in ('hojas','pendientes','tiff','paginas'):row[field]+=fact[field]
            row['integraciones']+=fact['nuevas'];row['ids'].add(work['id']);row['lotes'].add(fact['id'])
        rows=[]
        for index,(_,r) in enumerate(sorted(groups.items())):
            rows.append(dict(r,id=index,expedientes=len(r['ids']),ids=sorted(r['ids']),lotes=sorted(r['lotes'])))
        totals={k:sum(r[k] for r in rows) for k in ('hojas','pendientes','tiff','paginas','integraciones')}
        totals['expedientes_distintos']=len({i for r in rows for i in r['ids']})
        if source==SOURCES[1]:
            # No confundir una medida ajena a este hecho con un cero observado.
            for key in ('hojas','pendientes','integraciones'):
                totals[key]=None
                for row in rows:row[key]=None
        return dict(generado=now(),zona=dt.datetime.now().astimezone().tzname(),fuente=source,periodo=period,dimension=dimension,
                    desde=first,hasta=last,sin_fecha=unknown,sin_fecha_excluidos=excluded_unknown,filas=rows,totales=totals,
                    alcance='Ciclos vigentes activos seleccionados. La etapa es la actual; un expediente puede aparecer en varios periodos.',
                    advertencia='Ingresos TIFF incluye importaciones luego retiradas; no acredita fecha física de escaneo. Hojas y conteos solo aplican a Inventario por recepción.')

    def export(self,snapshot,path):
        path=Path(path);path.mkdir(parents=True,exist_ok=False)
        self.s.csv_write(path/'cubo.csv',[{k:v for k,v in r.items() if k not in ('ids','lotes')} for r in snapshot['filas']])
        (path/'contexto.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
        return path
