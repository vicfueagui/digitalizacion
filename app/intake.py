"""Importación diaria de listas nominales CSV/XLSX, con preflight y procedencia."""
import csv
import difflib
import hashlib
import html
import io
import json
import re
import uuid
from pathlib import Path
from .core import curp,date,integer,now,js
from .directory import Directory,normalized
from .importers import read_xlsx,pending

FIELDS={'curp':'CURP principal','curp2':'CURP de comprobación','nombre':'Nombre completo','folio':'Folio',
        'legajo':'Legajo','numero':'Consecutivo (No.)','integra':'Integra / responsable de lista',
        'sistema':'Sistema','solicitud':'Fecha de solicitud','trabajado':'Trabajo declarado','area':'Área de origen'}
ALIASES={'curp':['curp','curp o rfc','curp/rfc','rfc o curp','clave curp'],
         'curp2':['curp o rfc2','curp o rfc 2','curp2','curp de comprobacion'],
         'nombre':['apellido paterno materno nombre','apellidos y nombres','nombre completo','nombre del trabajador','nombre'],
         'folio':['folio','numero de folio','no folio','folio solicitud','folio de prestamo'],
         'legajo':['legajo','numero de legajo','no legajo'],
         'numero':['no','numero','consecutivo','n'],
         'integra':['integra','integro','integrado por','responsable de lista'],
         'sistema':['sistema','subsistema'], 'solicitud':['fecha solicitud','fecha de solicitud','fecha de la solicitud','f solicitud'],
         'trabajado':['trabajados','trabajado','estado de trabajo','estatus trabajado'],
         'area':['area','area de origen','area solicitante','departamento','area que entrega']}


def clean(value):return ' '.join(html.unescape(re.sub(r'<[^>]*>',' ',str(value if value is not None else ''))).split())
def header(value):return re.sub(r'[^a-z0-9]','',normalized(clean(value)))
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def infer_mapping(headers):
    result={};used=set()
    aliases={field:{header(a) for a in names} for field,names in ALIASES.items()}
    for field,choices in aliases.items():
        matches=[i for i,h in enumerate(headers) if header(h) in choices]
        if len(matches)==1:result[field]=matches[0];used.add(matches[0])
    # Variaciones ortográficas menores solo si hay una correspondencia inequívoca.
    for field,choices in aliases.items():
        if field in result:continue
        matches=[i for i,h in enumerate(headers) if i not in used and max((difflib.SequenceMatcher(None,header(h),a).ratio() for a in choices),default=0)>=.91]
        if len(matches)==1 and field not in ('curp','curp2','legajo','numero'):
            result[field]=matches[0];used.add(matches[0])
    return result


def read_tables(path):
    path=Path(path)
    if path.suffix.lower()=='.xlsx':
        import zipfile
        import xml.etree.ElementTree as ET
        try:return read_xlsx(path)
        except (zipfile.BadZipFile,ET.ParseError,KeyError,IndexError) as error:raise ValueError('El XLSX no se pudo leer: '+str(error))
    if path.suffix.lower() not in ('.csv','.tsv'):raise ValueError('Selecciona CSV o Excel .xlsx. Guarda los .xls antiguos como .xlsx o CSV.')
    data=path.read_bytes();text=None
    encodings=('utf-16',) if data.startswith((b'\xff\xfe',b'\xfe\xff')) else ('utf-8-sig','cp1252')
    for encoding in encodings:
        try:text=data.decode(encoding);break
        except UnicodeError:pass
    if text is None:raise ValueError('Codificación de CSV no reconocida; guarda como UTF-8.')
    if '\x00' in text:raise ValueError('CSV contiene bytes nulos; verifica su codificación.')
    try:delimiter=csv.Sniffer().sniff(text[:32768],delimiters=',;\t|').delimiter
    except csv.Error:delimiter=';' if text.count(';')>text.count(',') else ','
    reader=csv.reader(io.StringIO(text),delimiter=delimiter);rows=[]
    for values in reader:
        if any(clean(v) for v in values):rows.append((reader.line_num,values))
    return {'CSV':rows}


def detect_header(rows):
    for number,values in rows[:40]:
        mapping=infer_mapping(values)
        if 'curp' in mapping and ('folio' in mapping or 'nombre' in mapping):return number
    return rows[0][0] if rows else 1


def create_draft(store,item):
    """Alta técnica, sin acreditar recepción/avance. Transacción del llamador."""
    row=store.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0]
    if not row['legajo_esperado'] or not row['expediente_id']:return None
    found=store.rows('SELECT id FROM trabajos WHERE folio_id=? AND curp=? AND legajo=?',(row['folio_id'],row['curp_esperada'],row['legajo_esperado']))
    if found:return found[0]['id']
    stamp=now();ident=store.db.execute("INSERT INTO trabajos(folio_id,curp,legajo,estado_desde,expediente_id,prestamo_item_id,procedencia) VALUES(?,?,?,?,?,?,'Lista de préstamo')",
        (row['folio_id'],row['curp_esperada'],row['legajo_esperado'],stamp,row['expediente_id'],item)).lastrowid
    reason='Alta técnica de lista; recepción física pendiente de comprobar'
    store.db.execute('INSERT INTO historial(trabajo_id,estado,inicio,motivo,operador) VALUES(?,?,?,?,?)',(ident,'Recibido',stamp,reason,store.operador))
    store.db.execute('INSERT OR REPLACE INTO expediente_preferido VALUES(?,?,?)',(row['curp_esperada'],row['legajo_esperado'],ident))
    store.audit('trabajos',ident,'alta desde lista',None,store.one('trabajos',ident),reason)
    return ident


def confirm_legajo(store,item,legajo,reason):
    from .operations import Operations
    legajo=integer(legajo,1)
    if not reason.strip():raise ValueError('Indica cómo confirmaste el legajo.')
    with store.db:
        row=store.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0]
        if row['legajo_esperado'] is not None:raise ValueError('Este elemento ya tiene legajo. No se cambia su identidad.')
        if store.rows('SELECT id FROM prestamo_items WHERE folio_id=? AND curp_esperada=? AND legajo_esperado=?',(row['folio_id'],row['curp_esperada'],legajo)):
            raise ValueError('El folio ya contiene ese CURP/legajo. Revisa la lista duplicada; no se fusionó ni borró evidencia.')
        master=Operations(store).master(row['curp_esperada'],legajo)
        store.db.execute('UPDATE prestamo_items SET legajo_esperado=?,expediente_id=? WHERE id=?',(legajo,master,item))
        work=create_draft(store,item)
        store.db.execute("UPDATE pendientes SET estado='Revisado' WHERE tipo='Legajo de lista por confirmar' AND origen_id IN (SELECT origen_id FROM lista_registros WHERE prestamo_item_id=?)",(item,))
        store.audit('prestamo_items',item,'confirmar legajo',row,store.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0],reason)
        Operations(store).event(work,'Legajo de lista confirmado',reason,item)
    return work


def register_legajos(store,item,numbers,reason):
    """Desglosa una CURP de lista en varios físicos, conservando el primer item."""
    from .operations import Operations
    values=[integer(v.strip(),1) for v in str(numbers).split(',') if v.strip()]
    if not values or len(values)!=len(set(values)):raise ValueError('Indica legajos diferentes separados por comas, por ejemplo 1,2,3.')
    if not reason.strip():raise ValueError('Registra la evidencia del desglose físico.')
    with store.db:
        row=store.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0]
        if not row['curp_esperada']:raise ValueError('Confirma primero el expediente recibido fuera de lista.')
        ops=Operations(store);works=[];first=True
        for legajo in values:
            existing=store.rows('SELECT * FROM prestamo_items WHERE folio_id=? AND curp_esperada=? AND legajo_esperado=?',(row['folio_id'],row['curp_esperada'],legajo))
            if existing:
                work=create_draft(store,existing[0]['id'])
                if work:works.append(work)
                continue
            master=ops.master(row['curp_esperada'],legajo)
            if row['legajo_esperado'] is None and first:
                target=item;store.db.execute('UPDATE prestamo_items SET legajo_esperado=?,expediente_id=? WHERE id=?',(legajo,master,target))
                store.db.execute("UPDATE pendientes SET estado='Revisado' WHERE tipo='Legajo de lista por confirmar' AND origen_id IN (SELECT origen_id FROM lista_registros WHERE prestamo_item_id=?)",(item,))
                first=False
            else:
                fields=['ubicacion_original','ubicacion_id','integra_id','sistema_id','integra_declarado','sistema_declarado','fecha_solicitud','trabajado_declarado','numero_lista']
                target=store.db.execute('INSERT INTO prestamo_items(folio_id,expediente_id,curp_esperada,legajo_esperado,origen,lista_padre_id,'+','.join(fields)+') VALUES('+','.join('?' for _ in range(6+len(fields)))+')',
                    (row['folio_id'],master,row['curp_esperada'],legajo,'Desglose del elemento '+str(item),row['lista_padre_id'] or item)+tuple(row[k] for k in fields)).lastrowid
            work=create_draft(store,target);works.append(work)
            ops.event(work,'Legajo registrado desde CURP de lista',reason+' / elemento de origen '+str(item),target)
        ops.receipt_status(row['folio_id'])
        store.audit('prestamo_items',item,'desglose en legajos',row,{'legajos':values,'ciclos':works},reason)
    return works


class LoanLists:
    def __init__(self,store):self.s=store;self.db=store.db
    def preview(self,path,sheet=None,header_row=None,mapping=None,default_folio='',default_legajo=None,area=''):
        path=Path(path).resolve();source_hash=digest(path);tables=read_tables(path)
        if not tables:raise ValueError('No hay hojas con datos.')
        sheet=sheet or next(iter(tables))
        if sheet not in tables:raise ValueError('Selecciona una hoja existente.')
        rows=tables[sheet];header_row=header_row or detect_header(rows)
        headers=next((values for n,values in rows if n==header_row),None)
        if headers is None:raise ValueError('Fila de encabezados inexistente.')
        mapping=infer_mapping(headers) if mapping is None else {k:v for k,v in mapping.items() if v is not None}
        if any(k not in FIELDS or not isinstance(v,int) or isinstance(v,bool) or not 0<=v<len(headers) for k,v in mapping.items()):raise ValueError('Mapeo de columnas inválido.')
        if len(set(mapping.values()))!=len(mapping):raise ValueError('Una columna no puede representar dos campos distintos.')
        if 'curp' not in mapping:raise ValueError('Asocia la columna CURP principal.')
        if 'folio' not in mapping and not default_folio.strip():raise ValueError('Asocia Folio o indica el folio de toda la lista.')
        default_legajo=integer(default_legajo,1,nullable=True);result=[]
        for number,values in rows:
            if number<=header_row or not any(clean(v) for v in values):continue
            raw_values={key:values[index] if index<len(values) else None for key,index in mapping.items()}
            data={key:clean(value) for key,value in raw_values.items()};errors=[];warnings=[]
            data['folio']=data.get('folio') or default_folio.strip()
            data['area']=data.get('area') or area.strip()
            try:data['curp']=curp(data.get('curp'))
            except ValueError:errors.append('CURP principal inválida o RFC sin CURP; conservar para aclaración.')
            other=clean(data.get('curp2')).upper()
            if other and other!=data.get('curp'):errors.append('Las dos columnas CURP no coinciden; no se eligió una automáticamente.')
            if not data['folio']:errors.append('Falta folio.')
            try:data['legajo']=integer(data.get('legajo') or default_legajo,1,nullable=True)
            except ValueError as error:errors.append('Legajo: '+str(error));data['legajo']=None
            if data.get('legajo') is None:warnings.append('Legajo pendiente: No. es un consecutivo, no legajo.')
            elif not clean(raw_values.get('legajo')):warnings.append('Legajo aplicado por opción explícita de importación: '+str(default_legajo))
            try:data['solicitud']=date(raw_values.get('solicitud'))
            except (ValueError,OverflowError) as error:errors.append('Fecha de solicitud: '+str(error));data['solicitud']=None
            result.append({'fila':number,'datos':data,'errores':errors,'advertencias':warnings,'valores':values})
        if not result:raise ValueError('No hay registros después del encabezado.')
        config={'sheet':sheet,'header_row':header_row,'mapping':mapping,'default_folio':default_folio,'default_legajo':default_legajo,'area':area}
        if digest(path)!=source_hash:raise ValueError('El archivo cambió durante el análisis. Analízalo nuevamente.')
        return {'path':str(path),'sha256':source_hash,'hojas':list(tables),'encabezados':headers,'config':config,'filas':result,
                'validas':sum(not r['errores'] for r in result),'por_revisar':sum(bool(r['errores']) for r in result),'sin_legajo':sum(not r['errores'] and r['datos']['legajo'] is None for r in result)}

    def commit(self,plan):
        from .operations import Operations
        if digest(plan['path'])!=plan['sha256']:raise ValueError('El archivo cambió después de la vista previa. Analízalo nuevamente.')
        expected_hash=plan['sha256'];plan=self.preview(plan['path'],**plan['config'])
        if plan['sha256']!=expected_hash:raise ValueError('El archivo cambió después de la vista previa. Analízalo nuevamente.')
        config_hash=hashlib.sha256(js(plan['config']).encode('utf-8')).hexdigest();source_hash=plan['sha256'];sheet=plan['config']['sheet']
        duplicate=self.s.rows('SELECT l.resultado FROM listas_importadas l JOIN fuentes f ON f.id=l.fuente_id WHERE f.hash=? AND l.hoja=? AND l.config_hash=?',(source_hash,sheet,config_hash))
        if duplicate:return dict(json.loads(duplicate[0]['resultado']),ya_importado=True)
        self.s.backup()
        report={'folios_nuevos':0,'elementos_nuevos':0,'ciclos_nuevos':0,'duplicados':0,'por_revisar':0,'sin_legajo':0,'ya_importado':False}
        directory=Directory(self.s);ops=Operations(self.s);batch=uuid.uuid4().hex
        with self.db:
            sources=self.s.rows('SELECT id FROM fuentes WHERE hash=?',(source_hash,))
            source=sources[0]['id'] if sources else self.db.execute('INSERT INTO fuentes(hash,nombre,fecha) VALUES(?,?,?)',(source_hash,Path(plan['path']).name,now())).lastrowid
            self.db.execute('INSERT INTO listas_importadas VALUES(?,?,?,?,?,?,?)',(batch,source,sheet,config_hash,now(),self.s.operador,'{}'))
            for row in plan['filas']:
                origins=self.s.rows('SELECT id FROM origen WHERE fuente_id=? AND hoja=? AND fila=?',(source,sheet,row['fila']))
                origin=origins[0]['id'] if origins else self.db.execute('INSERT INTO origen(fuente_id,hoja,fila,contenido) VALUES(?,?,?,?)',(source,sheet,row['fila'],js({'encabezados':plan['encabezados'],'valores':row['valores']}))).lastrowid
                data=row['datos'];errors=list(row['errores']);folio=None;item=None;work=None;state='Por revisar';detail='; '.join(errors)
                if not errors:
                    folios=self.s.rows('SELECT * FROM folios WHERE numero=?',(data['folio'],))
                    if folios and not folios[0]['activo']:errors.append('Folio desactivado; revisa o reactívalo antes de importar.')
                    # Nunca crear una segunda identidad pendiente si ya existen legajos definidos para esa lista.
                    if folios and data['legajo'] is None and self.s.rows('SELECT id FROM prestamo_items WHERE folio_id=? AND curp_esperada=? AND legajo_esperado IS NOT NULL',(folios[0]['id'],data['curp'])):
                        errors.append('Este CURP ya tiene legajo(s) en el folio. Indica el legajo para conciliar la fila.')
                    for kind,value in [('area',data.get('area')),('persona',data.get('integra')),('sistema',data.get('sistema'))]:
                        found=directory.find(kind,value)
                        if found and not found['activo']:errors.append('Directorio desactivado: '+found['nombre'])
                if errors:
                    detail='; '.join(errors);pending(self.s,origin,'Lista de folio por revisar',detail);report['por_revisar']+=1
                else:
                    if folios:folio=folios[0]['id']
                    else:
                        folio=self.db.execute('INSERT INTO folios(numero) VALUES(?)',(data['folio'],)).lastrowid;report['folios_nuevos']+=1
                        self.s.audit('folios',folio,'alta desde lista',None,self.s.one('folios',folio),'La fecha de solicitud no acredita recepción física')
                    area_id=directory.ensure('area',data.get('area'))
                    if area_id:
                        current=self.s.one('folios',folio)
                        if not current['area_origen']:self.db.execute('UPDATE folios SET area_origen=?,area_id=? WHERE id=?',(data['area'],area_id,folio))
                        elif normalized(current['area_origen'])!=normalized(data['area']):pending(self.s,origin,'Área de lista por revisar','El área de la lista difiere del folio existente; se conservó el área anterior.')
                    self.db.execute('INSERT OR IGNORE INTO personas(curp,nombre) VALUES(?,?)',(data['curp'],data.get('nombre','')))
                    previous=self.s.rows('SELECT nombre FROM personas WHERE curp=?',(data['curp'],))[0]['nombre']
                    if previous and data.get('nombre') and normalized(previous)!=normalized(data['nombre']):pending(self.s,origin,'Nombre de lista por revisar','Nombre distinto para una CURP existente; se conservó el anterior.')
                    elif not previous and data.get('nombre'):self.db.execute('UPDATE personas SET nombre=? WHERE curp=?',(data['nombre'],data['curp']))
                    items=self.s.rows('SELECT * FROM prestamo_items WHERE folio_id=? AND curp_esperada=? AND legajo_esperado IS ?',(folio,data['curp'],data['legajo']))
                    unknown=self.s.rows('SELECT * FROM prestamo_items WHERE folio_id=? AND curp_esperada=? AND legajo_esperado IS NULL',(folio,data['curp']))
                    if not items and unknown and data['legajo'] is not None:
                        # Requiere confirmación individual; no asociar silenciosamente a otro elemento.
                        detail='Hay un elemento previo sin legajo. Registra sus legajos en Recepción / préstamo. Esta fila se conserva para conciliación; repetir el mismo archivo no vuelve a procesarla.'
                        pending(self.s,origin,'Lista de folio por revisar',detail);report['por_revisar']+=1
                    elif items:
                        item=items[0]['id'];state='Ya registrado';detail='Se conserva el elemento existente sin sobrescribir recepción, custodia ni metadatos.';report['duplicados']+=1
                    else:
                        master=ops.master(data['curp'],data['legajo']) if data['legajo'] is not None else None
                        item=self.db.execute("INSERT INTO prestamo_items(folio_id,expediente_id,curp_esperada,legajo_esperado,origen,integra_id,sistema_id,integra_declarado,sistema_declarado,fecha_solicitud,trabajado_declarado,numero_lista) VALUES(?,?,?,?,'Lista importada',?,?,?,?,?,?,?)",
                            (folio,master,data['curp'],data['legajo'],directory.ensure('persona',data.get('integra')),directory.ensure('sistema',data.get('sistema')),data.get('integra',''),data.get('sistema',''),data.get('solicitud'),data.get('trabajado',''),data.get('numero',''))).lastrowid
                        work=create_draft(self.s,item);report['elementos_nuevos']+=1;report['ciclos_nuevos']+=int(work is not None)
                        state='Registrado';detail='Recepción pendiente; estado de trabajo conservado como declaración de la lista.'
                        ops.event(work,'Importación de lista',detail,item);ops.receipt_status(folio)
                    if item and data['legajo'] is None:
                        report['sin_legajo']+=1;pending(self.s,origin,'Legajo de lista por confirmar','Elemento '+str(item)+': confirma legajo en Recepción / préstamo; no se dedujo de No.')
                self.db.execute('INSERT INTO lista_registros(lista_id,origen_id,folio_id,prestamo_item_id,trabajo_id,resultado,detalle) VALUES(?,?,?,?,?,?,?)',(batch,origin,folio,item,work,state,detail))
            report['lista_id']=batch
            self.db.execute('UPDATE listas_importadas SET resultado=? WHERE id=?',(js(report),batch))
            self.s.audit('listas_importadas',batch,'importar lista',None,report,'Importación confirmada desde vista previa; originales preservados')
        return report
