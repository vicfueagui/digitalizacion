"""Lectura de fuentes. Nunca escribe sobre el XLSX ni sobre el CSV original."""
import csv
import hashlib
import io
import json
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from .core import curp, date, integer, now, js

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def read_xlsx(path):
    # Lector deliberadamente acotado: valores y caché de fórmulas, no recalcula Excel.
    result={}
    with zipfile.ZipFile(str(path)) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            strings=[''.join(x.itertext()) for x in root.findall('s:si',NS)]
        links={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        book=ET.fromstring(z.read('xl/workbook.xml'))
        props=book.find('s:workbookPr',NS)
        if props is not None and props.get('date1904') in ('1','true'):
            raise ValueError('Este lector requiere el calendario Excel 1900, usado por tu archivo.')
        for sheet in book.findall('s:sheets/s:sheet',NS):
            rel=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target=links[rel]
            target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            rows=[]
            for row in ET.fromstring(z.read(target)).findall('s:sheetData/s:row',NS):
                cells={}
                for cell in row.findall('s:c',NS):
                    letters=re.match('[A-Z]+',cell.attrib['r'])[0];n=0
                    for char in letters:n=n*26+ord(char)-64
                    kind=cell.get('t');v=cell.find('s:v',NS);value=v.text if v is not None else None
                    if kind=='s' and value is not None:value=strings[int(value)]
                    elif kind=='inlineStr':value=''.join(cell.find('s:is',NS).itertext())
                    elif kind not in ('str','e') and value is not None:
                        try:
                            value=float(value);value=int(value) if value.is_integer() else value
                        except ValueError:pass
                    cells[n-1]=value
                if any(v is not None for v in cells.values()):
                    rows.append((int(row.attrib['r']),[cells.get(i) for i in range(max(cells)+1)]))
            result[sheet.attrib['name']]=rows
    return result

def records(rows, header_row):
    headers=next((r for n,r in rows if n==header_row),[])
    return [(n,dict(zip(headers,values+[None]*max(0,len(headers)-len(values))))) for n,values in rows if n>header_row]

def source(store,path):
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    found=store.rows('SELECT id FROM fuentes WHERE hash=?',(digest,))
    if found:return None
    return store.db.execute('INSERT INTO fuentes(hash,nombre,fecha) VALUES(?,?,?)',(digest,Path(path).name,now())).lastrowid

def raw(store,src,sheet,n,data):
    return store.db.execute('INSERT INTO origen(fuente_id,hoja,fila,contenido) VALUES(?,?,?,?)',(src,sheet,n,js(data))).lastrowid

def pending(store,origin,kind,message):
    store.db.execute('INSERT INTO pendientes(origen_id,tipo,detalle) VALUES(?,?,?)',(origin,kind,message))

def import_excel(store,path):
    sheets=read_xlsx(path)
    if not {'bd','f833','cat_datos','cont','incid','cat_incid'}.issubset(sheets):
        raise ValueError('Faltan hojas esperadas. No se importó el archivo.')
    if store.rows('SELECT id FROM trabajos LIMIT 1'):
        raise ValueError('La importación inicial de Excel requiere una base sin trabajos. No sobrescribe la operación diaria. Usa una base de prueba separada para reimportar.')
    report={'trabajos':0,'catalogos':0,'bloques':0,'incidencias':0,'tareas':0}
    with store.db:
        src=source(store,path)
        if src is None:return {'mensaje':'Este archivo ya fue importado.'}
        origins={}
        for sheet,rows in sheets.items():
            for n,data in rows:origins[(sheet,n)]=raw(store,src,sheet,n,data)
        # f833 proporciona explícitamente año y número; fecha solicitud no equivale a recepción.
        folio_numbers=set(str(r.get('folio') or '').strip() for _,r in records(sheets['f833'],1))-{''}
        fmap={}
        for num in sorted(folio_numbers):
            fid=store.db.execute('INSERT INTO folios(numero) VALUES(?)',(num,)).lastrowid
            fmap[num]=fid
        def folio_id(value):
            text=str(value or '').strip()
            matches=[num for num in fmap if num==text or ('/' not in text and num.split('/')[0]==text)]
            if len(matches)==1:return fmap[matches[0]]
            raise ValueError('Folio ambiguo o sin año: '+text)
        def make_work(fid,person,name,legajo,operator='',received=None,physical=None,outside=0,folders=0,notes=''):
            existing=store.rows('SELECT id FROM trabajos WHERE folio_id=? AND UPPER(TRIM(curp))=? AND legajo=?',(fid,person,legajo))
            if existing:return existing[0]['id'],False
            store.db.execute('INSERT OR IGNORE INTO personas(curp,nombre) VALUES(?,?)',(person,str(name or '').strip()))
            stamp=now()
            tid=store.db.execute('INSERT INTO trabajos(folio_id,curp,legajo,digitalizador,estado_desde,recibido,fisicos,fuera_broche,carpetas,notas) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (fid,person,legajo,operator or '',stamp,received,physical,outside,folders,notes)).lastrowid
            store.db.execute('INSERT INTO historial(trabajo_id,estado,inicio,motivo,operador) VALUES(?,?,?,?,?)',(tid,'Recibido',stamp,'Alta técnica por importación; fechas históricas conservadas en origen',store.operador))
            from .operational_migration import link_work
            link_work(store,tid,legacy=True)
            report['trabajos']+=1
            return tid,True
        for n,r in records(sheets['bd'],1):
            if not r.get('Curp'):continue
            oid=origins[('bd',n)]
            try:
                person=curp(r['Curp']);fid=folio_id(r.get('Folio'));leg=integer(r.get('legajo'),1)
                physical=integer(r.get('No_fisicos'),nullable=True);outside=integer(r.get('f_broche') or 0)
                folders=integer(r.get('carpetas') or 0)
                if folders not in (0,1) or (physical is not None and outside>physical):raise ValueError('Cantidades físicas o carpetas inconsistentes.')
                tid,created=make_work(fid,person,r.get('Nombre'),leg,r.get('Digitalizador'),date(r.get('F_recibido')),physical,outside,folders,str(r.get('Observaciones') or ''))
                if created:
                    store.db.execute('UPDATE trabajos SET digitales_declarados=? WHERE id=?',(integer(r.get('No_digitales'),nullable=True),tid))
                if not created:pending(store,oid,'Duplicado bd','Misma identidad CURP/legajo (puede tener otro folio); no se sobrescribió.')
                for col in ('Fecha_fisicos','Fecha_digitales','Fecha codificado','C_folder'):
                    if r.get(col) is not None:
                        pending(store,oid,'Hito histórico', '{} / trabajo {}: {}={}. Verificar estado actual; no se inventan horas de inicio/fin.'.format(person,tid,col,date(r[col])))
            except (ValueError,TypeError) as e:pending(store,oid,'bd por revisar',str(e))
        for n,r in records(sheets['f833'],1):
            oid=origins[('f833',n)]
            try:
                person=curp(r.get('CURP O RFC'));fid=folio_id(r.get('folio'))
                existing=store.rows('SELECT id FROM trabajos WHERE folio_id=? AND curp=?',(fid,person))
                if not existing:
                    pending(store,oid,'Legajo por confirmar','{} / folio {}: f833 no especifica legajo. No se creó expediente ni recepción; confirmar la lista física.'.format(person,fid))
            except ValueError as e:pending(store,oid,'f833 por revisar',str(e))
        for sheet,kind,head in [('cat_datos','documento',3),('cat_incid','incidencia',1)]:
            for n,r in records(sheets[sheet],head):
                oid=origins[(sheet,n)]
                code=str(r.get('CONCAT') or '') if kind=='documento' else str(r.get('INCIDENCIA') or '')
                code=code.strip().upper()
                if not code:continue
                if kind=='documento' and not re.fullmatch(r'(DP|FP|HL)-\d{1,3}',code):
                    pending(store,oid,'Código inválido',code);continue
                if kind=='documento':
                    prefix,num=code.split('-');code=prefix+'-'+num.zfill(2)
                exists=store.rows('SELECT id FROM catalogos WHERE tipo=? AND codigo=?',(kind,code))
                if exists:
                    pending(store,oid,'Catálogo duplicado',code+'; se conserva la primera entrada y esta fila original.');continue
                title=str(r.get('DOCUMENTO') or code) if kind=='documento' else code
                store.db.execute('INSERT INTO catalogos(tipo,codigo,carpeta,titulo,descripcion,accion) VALUES(?,?,?,?,?,?)',
                    (kind,code,str(r.get('ORDEN') or ''),title,str(r.get('DESCRIPCION') or r.get('PROBLEMA') or ''),str(r.get('ACCION') or '')))
                report['catalogos']+=1
        for n,r in records(sheets['cont'],1):
            oid=origins[('cont',n)]
            try:
                person=curp(r.get('CURP'));leg=integer(r.get('Legajo'),1)
                matches=store.rows('SELECT * FROM trabajos WHERE UPPER(TRIM(curp))=? AND legajo=?',(person,leg))
                if len(matches)!=1:raise ValueError('Conteo sin folio: no hay un trabajo único coincidente.')
                tid=matches[0]['id']
                if store.rows('SELECT id FROM conteos WHERE trabajo_id=?',(tid,)):raise ValueError('Existe otro conteo para este trabajo; no se sumó de nuevo.')
                blocks=[integer(r['DIV'+str(i)],1) for i in range(1,51) if r.get('DIV'+str(i)) not in (None,'',0)]
                for value in blocks:
                    store.db.execute('INSERT INTO conteos(trabajo_id,cantidad,nota,creado) VALUES(?,?,?,?)',(tid,value,'Importado de cont; fecha original desconocida',now()));report['bloques']+=1
                if blocks and sum(blocks)!=matches[0]['fisicos']:
                    pending(store,oid,'Diferencia de conteo','Trabajo {}: bloques={}, bd={}. No se sobrescribió bd.'.format(tid,sum(blocks),matches[0]['fisicos']))
            except ValueError as e:pending(store,oid,'Conteo por revisar',str(e))
        for n,r in records(sheets['incid'],2):
            oid=origins[('incid',n)]
            try:
                person=curp(r.get('CURP'));matches=store.rows('SELECT id FROM trabajos WHERE curp=?',(person,))
                if len(matches)!=1:raise ValueError('Incidencia sin folio/legajo: no hay trabajo único.')
                code=str(r.get('INCIDENCIA') or 'SIN_CATALOGO')
                cat=store.rows("SELECT id FROM catalogos WHERE tipo='incidencia' AND codigo=?",(code,))
                store.db.execute('INSERT INTO incidencias(trabajo_id,catalogo_id,codigo_snapshot,documento,problema,accion,creado) VALUES(?,?,?,?,?,?,?)',
                    (matches[0]['id'],cat[0]['id'] if cat else None,code,str(r.get('DOCUMENTO') or ''),str(r.get('PROBLEMA') or code),str(r.get('ACCION') or ''),now()))
                report['incidencias']+=1
            except ValueError as e:pending(store,oid,'Incidencia por revisar',str(e))
        states={0:'Pendiente',2:'En curso',4:'Hecha',6:'En espera',8:'Bloqueada'}
        for n,values in sheets.get('kanban',[]):
            if n<2:continue
            for col,state in states.items():
                if col<len(values) and values[col]:
                    title=str(values[col]);person=title.split()[0]
                    match=store.rows('SELECT id FROM trabajos WHERE curp=?',(person,))
                    store.db.execute('INSERT INTO tareas(titulo,estado,trabajo_id,notas) VALUES(?,?,?,?)',(title,state,match[0]['id'] if len(match)==1 else None,'Importado de kanban; no modifica el estado documental.'))
                    report['tareas']+=1
        pending(store,None,'Recepción de folio','Confirma fecha real de recepción de cada folio. Fecha solicitud y F_recibido del expediente no se usaron como fecha de recepción del folio.')
        pending(store,None,'reg_dig preservado','No se aplicó reg_dig: importar CSV original por separado para validar sus 66 columnas. Todos los valores de la hoja se conservaron en origen.')
        from .directory import seed
        seed(store)
        store.audit('fuentes',src,'importar Excel',None,report,'Importación inicial; originales preservados')
    return report

TEXT_COLS={'VERSION_BAT','VERSION_REGLA','FECHA','HORA','CURP','DIGITALIZADOR','ESTADO_CONTEO_PAGINAS','RESULTADO','RUTA_EXPEDIENTE','APUNTE_FOLDER'}

def parse_csv(path):
    data=Path(path).read_bytes()
    try:text=data.decode('utf-8-sig')
    except UnicodeDecodeError:text=data.decode('cp1252')
    lines=text.splitlines()
    if not lines:raise ValueError('CSV vacío.')
    wrapped=lines[0].endswith('APUNTE_FOLDER,,')
    if wrapped:
        # Archivo adjunto: exportado con separador coma sobre otro CSV de punto y coma.
        normalized=[';'.join(next(csv.reader([lines[0]],delimiter=';'))).rstrip(',')]
        normalized += [','.join(next(csv.reader([line],delimiter=','))) for line in lines[1:] if line.strip()]
        rows=list(csv.reader(normalized,delimiter=';',strict=True))
    else:
        rows=list(csv.reader(io.StringIO(text),delimiter=';',strict=True))
    headers=rows[0]
    required={'CURP','FECHA','HORA','TOTAL_DIGITALES_TIFF','TOTAL_PAG_DIGITALES_CONOCIDAS','INV_TOTAL_ARCHIVOS_CARPETAS','APUNTE_FOLDER'}
    if len(headers)!=66 or not required.issubset(headers) or len(set(headers))!=66:
        raise ValueError('Se esperaban las 66 columnas del reporte detallado v3.0/v3.1, separadas con punto y coma.')
    return headers,rows[1:],wrapped

def validate_metrics(p):
    curp(p['CURP']);date(p['FECHA'])
    import datetime
    datetime.datetime.strptime(p['HORA'],'%H:%M:%S')
    if p['VERSION_BAT'] not in ('3.0','3.1') or p['VERSION_REGLA']!='1P_INDIVIDUAL_2P_MULTI':
        raise ValueError('Versión o regla de conteo no reconocida.')
    for key in p:
        if key not in TEXT_COLS:p[key]=integer(p[key])
    for prefix in ('MOV_P','MOV_F','MOV_TOTAL','INV_P','INV_F','INV_TOTAL'):
        total_key=prefix+('_ARCHIVOS_CARPETAS' if prefix=='INV_TOTAL' else '_ARCHIVOS')
        page_key=prefix+('_PAG_CARPETAS' if prefix=='INV_TOTAL' else '_PAG_TOTAL')
        if p[total_key]!=sum(p[prefix+'_'+k] for k in ('INDIVIDUALES','MULTI','NO_CLASIFICADOS')):raise ValueError(prefix+': archivos no cuadran.')
        if p[page_key]!=p[prefix+'_PAG_INDIVIDUALES']+p[prefix+'_PAG_MULTI']:raise ValueError(prefix+': páginas no cuadran.')
        if p[prefix+'_PAG_INDIVIDUALES']!=p[prefix+'_INDIVIDUALES'] or p[prefix+'_PAG_MULTI']<2*p[prefix+'_MULTI']:raise ValueError(prefix+': regla individual/multi inconsistente.')
    for group in ('MOV','INV'):
        for metric in ('INDIVIDUALES','MULTI','NO_CLASIFICADOS','PAG_INDIVIDUALES','PAG_MULTI'):
            if p[group+'_TOTAL_'+metric]!=p[group+'_P_'+metric]+p[group+'_F_'+metric]:raise ValueError('Total por carpetas inconsistente.')
    if p['TOTAL_DIGITALES_TIFF']!=p['INV_TOTAL_ARCHIVOS_CARPETAS']+p['TIFF_RAIZ_CURP']:raise ValueError('Total de archivos inconsistente.')
    if p['TOTAL_PAG_DIGITALES_CONOCIDAS']!=p['INV_TOTAL_PAG_CARPETAS']+p['PAG_CONOCIDAS_RAIZ']:raise ValueError('Total de páginas inconsistente.')
    if p['ESTADO_CONTEO_PAGINAS'] not in ('COMPLETO','PARCIAL'):raise ValueError('Estado de conteo desconocido.')
    if p['ESTADO_CONTEO_PAGINAS']=='COMPLETO' and (p['INV_TOTAL_NO_CLASIFICADOS'] or p['TIFF_NO_LEGIBLES_RAIZ']):raise ValueError('Conteo completo con archivos ilegibles.')
    if p['RESULTADO'] not in ('OK','REVISAR'):raise ValueError('Resultado desconocido.')
    if p['RESULTADO']=='OK' and any(p[k] for k in ('CONFLICTOS','ERRORES_MOVIMIENTO','ERRORES_LECTURA_TIFF','TIFF_SUELTOS_ESCANER','TIFF_NO_ESPERADOS_CURP','TIFF_RAIZ_CURP')):raise ValueError('Resultado OK con errores registrados.')

def import_csv(store,path):
    headers,rows,wrapped=parse_csv(path)
    report={'ejecuciones':0,'duplicadas':0,'rechazadas':0,'envoltura_csv_corregida':wrapped}
    with store.db:
        src=source(store,path)
        if src is None:return {'mensaje':'Este archivo ya fue importado; sin duplicar reportes.'}
        for n,values in enumerate(rows,2):
            if not values:continue
            oid=raw(store,src,'CSV',n,values)
            if len(values)!=len(headers):
                pending(store,oid,'CSV rechazado','La fila tiene {} columnas; se esperaban 66.'.format(len(values)));report['rechazadas']+=1;continue
            payload=dict(zip(headers,values))
            try:
                validate_metrics(payload)
                stamp=date(payload['FECHA'])+'T'+payload['HORA']
                digest=hashlib.sha256(js(payload).encode('utf-8')).hexdigest()
                if store.rows('SELECT id FROM ejecuciones WHERE huella=?',(digest,)):
                    report['duplicadas']+=1;continue
                store.db.execute('INSERT INTO ejecuciones(huella,origen_id,curp,fecha,payload,observacion) VALUES(?,?,?,?,?,?)',
                    (digest,oid,curp(payload['CURP']),stamp,js(payload),'Sin folio/legajo en fuente. Confirmar alcance antes de vincular.'))
                report['ejecuciones']+=1
            except (ValueError,KeyError) as e:
                pending(store,oid,'CSV rechazado',str(e));report['rechazadas']+=1
        store.audit('fuentes',src,'importar CSV',None,report,'Se conserva cada ejecución; no se suman inventarios históricos')
    return report
