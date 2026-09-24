import csv
import datetime as dt
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATES = ['Recibido', 'Conteo en curso', 'Conteo completado', 'Escaneo en curso',
          'Expediente escaneado', 'Codificación en curso', 'Expediente codificado',
          'Revisión en curso', 'Correcciones solicitadas', 'Correcciones en curso', 'Listo para aprobación', 'Expediente cerrado']
TASK_STATES = ['Pendiente', 'En curso', 'En espera', 'Bloqueada', 'Hecha']

def now():
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')

def integer(value, minimum=0, nullable=False):
    if value is None or str(value).strip() == '':
        if nullable:
            return None
        raise ValueError('Falta una cantidad entera.')
    if not re.fullmatch(r'\d+', str(value).strip()):
        raise ValueError('Utiliza un número entero sin decimales ni signos.')
    result = int(value)
    if result < minimum:
        raise ValueError('La cantidad mínima es {}.'.format(minimum))
    return result

def date(value):
    if value is None or value == '':
        return None
    if isinstance(value, (int, float)):
        return (dt.datetime(1899, 12, 30) + dt.timedelta(days=value)).date().isoformat()
    text = str(value).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S'):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError('Fecha inválida. Usa AAAA-MM-DD o DD/MM/AAAA.')

def curp(value):
    value = str(value or '').strip().upper()
    if not re.fullmatch(r'[A-Z][AEIOUX][A-Z]{2}\d{6}[HM][A-Z]{5}[A-Z0-9]\d', value):
        raise ValueError('CURP: revisa sus 18 caracteres y su estructura. No se consulta RENAPO.')
    return value

def js(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)

class Store:
    def __init__(self, path=None, operador='Operador local', workspace=None):
        from .workspace import Workspace, WorkspaceLock, Connection
        from .migrations import migrate
        self.workspace = Workspace(workspace, path)
        if any((self.workspace.root/name).exists() for name in ('.restauracion_incompleta','.actualizacion_pendiente.json')):
            raise ValueError('Hay una restauración o actualización interrumpida. Conserva la carpeta y consulta docs/RESPALDOS.md antes de abrirla.')
        self.path = self.workspace.database
        self.operador = operador
        lock = WorkspaceLock(self.workspace.root)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(str(self.path), timeout=10, factory=Connection)
            self.db.workspace_lock = lock
            self.db.row_factory = sqlite3.Row
            self.db.execute('PRAGMA foreign_keys=ON')
            migrate(self)
        except BaseException:
            if hasattr(self, 'db'): self.db.close()
            else: lock.close()
            raise

    def rows(self, sql, args=()):
        return [dict(r) for r in self.db.execute(sql, args)]

    def one(self, table, ident):
        if table not in ('folios','trabajos','catalogos','conteos','incidencias','ejecuciones','tareas','pendientes'):
            raise ValueError('Tabla inválida')
        rows = self.rows('SELECT * FROM {} WHERE id=?'.format(table), (ident,))
        if not rows:
            raise ValueError('No existe el registro seleccionado.')
        return rows[0]

    def audit(self, entity, ident, action, before, after, reason):
        if not reason.strip():
            raise ValueError('Indica el motivo del cambio.')
        self.db.execute('INSERT INTO auditoria(fecha,operador,entidad,registro,accion,antes,despues,motivo) VALUES(?,?,?,?,?,?,?,?)',
                        (now(),self.operador,entity,str(ident),action,js(before),js(after),reason))

    def save_folio(self, numero, fecha, responsable='', ident=None, motivo='Alta de folio'):
        numero = numero.strip()
        if not numero:
            raise ValueError('Falta el número de folio (ejemplo: 833/2026).')
        fecha = date(fecha)
        with self.db:
            before = self.one('folios',ident) if ident else None
            from .directory import Directory
            responsible_id=Directory(self).ensure('persona',responsable,allow_inactive=bool(before and before['responsable']==responsable))
            if ident:
                self.db.execute('UPDATE folios SET numero=?,fecha_recepcion=?,responsable=? WHERE id=?', (numero,fecha,responsable,ident))
            else:
                ident = self.db.execute('INSERT INTO folios(numero,fecha_recepcion,responsable) VALUES(?,?,?)',(numero,fecha,responsable)).lastrowid
            self.db.execute('UPDATE folios SET responsable_id=? WHERE id=?',(responsible_id,ident))
            self.audit('folios',ident,'guardar',before,self.one('folios',ident),motivo)
        return ident

    def save_work(self, folio_id, person, nombre, legajo, digitalizador='', recibido='', fuera_broche=0, carpetas=0, notas='', ident=None, motivo='Alta de trabajo'):
        person, legajo = curp(person), integer(legajo,1)
        fuera_broche, carpetas = integer(fuera_broche), integer(carpetas)
        if carpetas not in (0,1):
            raise ValueError('Carpetas solamente admite 0 o 1.')
        recibido = date(recibido)
        if ident is None:
            existing=self.rows('SELECT id FROM trabajos WHERE folio_id=? AND UPPER(TRIM(curp))=? AND legajo=?',(folio_id,person,legajo))
            if existing:raise ValueError('Ese expediente ya tiene un ciclo en este folio (ID {}). Abre el ciclo existente.'.format(existing[0]['id']))
        with self.db:
            before = self.one('trabajos',ident) if ident else None
            from .directory import Directory
            digitalizer_id=Directory(self).ensure('persona',digitalizador,allow_inactive=bool(before and before['digitalizador']==digitalizador))
            if before and (before['curp'],before['legajo']) != (person,legajo):
                raise ValueError('La identidad CURP/legajo es fija. El cambio de folio se registra en la bitácora.')
            if before and before['folio_id'] != folio_id:
                raise ValueError('El folio es el contexto histórico del ciclo. Crea un nuevo ciclo en el nuevo folio; conserva este registro.')
            if before and before['fisicos'] is not None and fuera_broche > before['fisicos']:
                raise ValueError('Fuera del broche no puede superar el total físico.')
            old_person = self.rows('SELECT * FROM personas WHERE curp=?',(person,))
            if old_person:
                if old_person[0]['nombre'] != nombre.strip():
                    self.audit('personas',person,'nombre',old_person[0],{'nombre':nombre.strip()},motivo)
                self.db.execute('UPDATE personas SET nombre=? WHERE curp=?',(nombre.strip(),person))
            else:
                self.db.execute('INSERT INTO personas VALUES(?,?)',(person,nombre.strip()))
            values = (digitalizador,recibido,fuera_broche,carpetas,notas)
            if ident:
                self.db.execute('UPDATE trabajos SET digitalizador=?,recibido=?,fuera_broche=?,carpetas=?,notas=?,folio_id=? WHERE id=?',values+(folio_id,ident))
                if before['folio_id']!=folio_id and self.latest(ident):
                    self.invalidate_inventory(ident,'Cambió el folio: regenerar el reporte')
            else:
                stamp = now()
                ident = self.db.execute('INSERT INTO trabajos(folio_id,curp,legajo,digitalizador,recibido,fuera_broche,carpetas,notas,estado_desde) VALUES(?,?,?,?,?,?,?,?,?)',
                    (folio_id,person,legajo)+values+(stamp,)).lastrowid
                self.db.execute('INSERT INTO historial(trabajo_id,estado,inicio,motivo,operador) VALUES(?,?,?,?,?)',(ident,STATES[0],stamp,motivo,self.operador))
                from .operational_migration import link_work
                link_work(self,ident)
                self.db.execute('INSERT OR REPLACE INTO expediente_preferido VALUES(?,?,?)',(person,legajo,ident))
            if before and before['digitalizador']!=digitalizador:
                stamp=now()
                self.db.execute("UPDATE asignaciones SET fin=? WHERE trabajo_id=? AND rol='Digitalizador' AND fin IS NULL",(stamp,ident))
                if digitalizador:
                    self.db.execute('INSERT INTO asignaciones(trabajo_id,persona,rol,inicio,registrado,operador,motivo,origen) VALUES(?,?,?,?,?,?,?,?)',
                                    (ident,digitalizador,'Digitalizador',stamp,stamp,self.operador,motivo,'Declarada'))
            self.db.execute('UPDATE trabajos SET digitalizador_id=? WHERE id=?',(digitalizer_id,ident))
            self.db.execute("UPDATE asignaciones SET persona_id=? WHERE trabajo_id=? AND rol='Digitalizador' AND persona=? AND persona_id IS NULL",(digitalizer_id,ident,digitalizador))
            self.audit('trabajos',ident,'guardar',before,self.one('trabajos',ident),motivo)
        return ident

    def works(self, texto='', folio='', estado='', desde='', hasta='', digitalizador='', activos=True,partial=False):
        # Elegir el principal sobre TODA la identidad antes de aplicar filtros.
        rows=self.rows('''SELECT t.*,f.numero AS folio,p.nombre,f.area_origen,pi.validacion AS recepcion,
            pi.custodia,COALESCE(a.total_tiff,0) AS total_tiff,COALESCE(a.total_paginas,0) AS total_paginas
            FROM trabajos t JOIN folios f ON f.id=t.folio_id JOIN personas p ON p.curp=t.curp
            LEFT JOIN prestamo_items pi ON pi.id=t.prestamo_item_id
            LEFT JOIN (SELECT trabajo_id,COUNT(*) AS total_tiff,SUM(paginas) AS total_paginas FROM archivos_tiff WHERE activo=1 GROUP BY trabajo_id) a ON a.trabajo_id=t.id ORDER BY t.id''')
        groups={}
        for row in rows:groups.setdefault((row['curp'].strip().upper(),row['legajo']),[]).append(row)
        preferences={(r['curp'],r['legajo']):r['trabajo_id'] for r in self.rows('SELECT * FROM expediente_preferido')}
        result=[]
        for key,records in groups.items():
            chosen=next((r for r in records if r['id']==preferences.get(key) and r['activo']),next((r for r in records if r['activo']),records[0]))
            if activos and not chosen['activo']:continue
            from .directory import normalized
            if texto and normalized(texto) not in normalized(chosen['curp']+' '+chosen['nombre']):continue
            # Folio encuentra también asignaciones históricas sin cambiar el principal.
            if folio and not any(normalized(folio) in normalized(r['folio']) if partial else r['folio']==folio for r in records):continue
            if estado and chosen['estado']!=estado:continue
            if digitalizador and not (normalized(digitalizador) in normalized(chosen['digitalizador']) if partial else chosen['digitalizador']==digitalizador):continue
            if desde and (not chosen['recibido'] or chosen['recibido']<date(desde)):continue
            if hasta and (not chosen['recibido'] or chosen['recibido']>date(hasta)):continue
            chosen=dict(chosen);chosen['registros']=len(records);chosen['ids_asociados']=','.join(str(r['id']) for r in records)
            chosen['folios_asociados']=' / '.join(dict.fromkeys(r['folio'] for r in records))
            result.append(chosen)
        return sorted(result,key=lambda r:(r['curp'],r['legajo']))

    def duplicate_diagnostics(self):
        result=[]
        for work in self.works(activos=False):
            if work['registros']<2:continue
            related_rows=self.associated(work['id'])
            if not any(r['conciliacion_pendiente'] or not r['expediente_id'] for r in related_rows):continue
            for related in related_rows:
                row=dict(related,principal=related['id']==work['id'])
                for table in ('conteos','incidencias','historial','ejecuciones','archivos_tiff'):
                    row[table]=self.db.execute('SELECT COUNT(*) FROM '+table+' WHERE trabajo_id=?',(related['id'],)).fetchone()[0]
                result.append(row)
        return result

    def associated(self,ident):
        row=self.one('trabajos',ident)
        return self.rows('SELECT t.*,f.numero AS folio FROM trabajos t JOIN folios f ON f.id=t.folio_id WHERE UPPER(TRIM(t.curp))=? AND t.legajo=? ORDER BY t.id',(row['curp'].strip().upper(),row['legajo']))

    def prefer(self,ident,reason):
        row=self.one('trabajos',ident)
        if not row['activo']:raise ValueError('Reactiva primero el registro elegido.')
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO expediente_preferido VALUES(?,?,?)',(row['curp'].strip().upper(),row['legajo'],ident))
            self.audit('expediente_preferido',ident,'elegir registro operativo',None,row,reason)

    def change_state(self, ident, state, reason):
        if state not in STATES:
            raise ValueError('Estado inválido.')
        with self.db:
            before = self.one('trabajos',ident)
            if not before['activo']:
                raise ValueError('Primero reactiva el trabajo.')
            old = STATES.index(before['estado']); new = STATES.index(state)
            if old == new:
                raise ValueError('El expediente ya está en ese estado.')
            if new > old+1:
                raise ValueError('Avanza una etapa a la vez para conservar la trazabilidad.')
            if new >= 2 and before['fisicos'] is None:
                raise ValueError('Confirma primero el conteo físico.')
            if state == 'Expediente cerrado':
                raise ValueError('El cierre requiere aprobar una entrega exacta desde Revisión del responsable.')
            if before['estado']=='Expediente cerrado':
                self.invalidate_inventory(ident,'Reapertura del ciclo aprobada con motivo')
            stamp = now()
            self.db.execute('UPDATE historial SET fin=? WHERE trabajo_id=? AND fin IS NULL',(stamp,ident))
            self.db.execute('INSERT INTO historial(trabajo_id,estado,inicio,motivo,operador) VALUES(?,?,?,?,?)',(ident,state,stamp,reason,self.operador))
            self.db.execute('UPDATE trabajos SET estado=?,estado_desde=? WHERE id=?',(state,stamp,ident))
            self.audit('trabajos',ident,'estado',before,self.one('trabajos',ident),reason)

    def add_count(self, ident, cantidad, nota=''):
        cantidad=integer(cantidad,1)
        with self.db:
            self.check_count_open(ident)
            rowid=self.db.execute('INSERT INTO conteos(trabajo_id,cantidad,nota,creado) VALUES(?,?,?,?)',(ident,cantidad,nota,now())).lastrowid
            self.audit('conteos',rowid,'alta',None,self.one('conteos',rowid),'Captura de bloque')
        return rowid

    def check_count_open(self, ident):
        work=self.one('trabajos',ident)
        if not work['activo'] or STATES.index(work['estado'])>1:
            raise ValueError('Para modificar bloques, el trabajo debe estar activo y en Recibido o Conteo en curso. Reabre con motivo.')

    def edit_count(self, ident, cantidad, motivo, remove=False):
        with self.db:
            old=self.one('conteos',ident); self.check_count_open(old['trabajo_id'])
            cantidad=integer(cantidad,1)
            self.db.execute('UPDATE conteos SET cantidad=?,activo=? WHERE id=?',(cantidad,0 if remove else 1,ident))
            self.audit('conteos',ident,'anular' if remove else 'corregir',old,self.one('conteos',ident),motivo)

    def count_total(self, ident):
        return self.db.execute('SELECT SUM(cantidad) FROM conteos WHERE trabajo_id=? AND activo=1',(ident,)).fetchone()[0]

    def confirm_count(self, ident):
        with self.db:
            self.check_count_open(ident)
            before=self.one('trabajos',ident); total=self.count_total(ident)
            if total is None:
                raise ValueError('Captura al menos un bloque antes de confirmar.')
            if before['fuera_broche']>total:
                raise ValueError('Las hojas fuera del broche superan el conteo.')
            self.db.execute('UPDATE trabajos SET fisicos=? WHERE id=?',(total,ident))
            if before['fisicos']!=total and self.rows('SELECT id FROM ejecuciones WHERE trabajo_id=? LIMIT 1',(ident,)):
                self.invalidate_inventory(ident,'Cambió el conteo físico: regenerar el reporte')
            self.audit('trabajos',ident,'confirmar conteo',before,self.one('trabajos',ident),'Suma de bloques activos; incluye hojas fuera del broche')
        return total

    def save_catalog(self, tipo, codigo, carpeta, titulo, descripcion='', accion='', ident=None, motivo='Alta de catálogo'):
        codigo=codigo.strip().upper(); titulo=titulo.strip()
        if tipo not in ('documento','incidencia') or not codigo or not titulo:
            raise ValueError('Completa tipo, código y título.')
        if tipo=='documento':
            match=re.fullmatch(r'(DP|FP|HL)-(\d{1,3})',codigo)
            if not match or not 1<=int(match[2])<=999 or carpeta not in ('PERSONALES','FEDERAL'):
                raise ValueError('Código: DP-01, FP-01 o HL-100 (1 a 999). Carpeta: PERSONALES o FEDERAL.')
            codigo=match[1]+'-'+match[2].zfill(2)
        with self.db:
            before=self.one('catalogos',ident) if ident else None
            if ident and (before['tipo']!=tipo or before['codigo']!=codigo):
                raise ValueError('El código es fijo: desactiva el anterior y crea uno nuevo.')
            vals=(tipo,codigo,carpeta,titulo,descripcion,accion)
            if ident:
                self.db.execute('UPDATE catalogos SET tipo=?,codigo=?,carpeta=?,titulo=?,descripcion=?,accion=? WHERE id=?',vals+(ident,))
            else:
                ident=self.db.execute('INSERT INTO catalogos(tipo,codigo,carpeta,titulo,descripcion,accion) VALUES(?,?,?,?,?,?)',vals).lastrowid
            if before and tipo=='documento' and before['carpeta']!=carpeta:
                self.invalidate_catalog(codigo)
            self.audit('catalogos',ident,'guardar',before,self.one('catalogos',ident),motivo)
        return ident

    def invalidate_catalog(self, code):
        for row in self.rows('SELECT DISTINCT trabajo_id FROM archivos_tiff WHERE codigo=? AND activo=1',(code,)):
            ident=row['trabajo_id']
            self.db.execute('INSERT OR REPLACE INTO inventario_pendiente VALUES(?,?)',(ident,'Cambió el catálogo: volver a organizar'))
            self.db.execute('UPDATE ejecuciones SET valido=0 WHERE trabajo_id=?',(ident,))
            self.db.execute('UPDATE trabajos SET carpetas=0 WHERE id=?',(ident,))

    def save_incident(self, work, catalog, documento, problema, accion='', estado='Abierta', ident=None, motivo='Registro de incidencia'):
        if not problema.strip() or estado not in ('Abierta','Resuelta','Anulada'):
            raise ValueError('Falta el problema o el estado es inválido.')
        with self.db:
            target=self.one('trabajos',work)
            if not target['activo'] or target['estado']==STATES[-1]:
                raise ValueError('Reactiva o reabre el expediente antes de cambiar incidencias.')
            before=self.one('incidencias',ident) if ident else None
            cat=self.one('catalogos',catalog) if catalog else None
            if cat and (cat['tipo']!='incidencia' or (not cat['activo'] and not (before and before['catalogo_id']==cat['id']))):
                raise ValueError('Selecciona una incidencia activa del catálogo.')
            vals=(work,catalog,cat['codigo'] if cat else 'SIN_CATALOGO',documento,problema,accion,estado,now() if estado=='Resuelta' else None)
            if ident:
                self.db.execute('UPDATE incidencias SET trabajo_id=?,catalogo_id=?,codigo_snapshot=?,documento=?,problema=?,accion=?,estado=?,resuelto=? WHERE id=?',vals+(ident,))
            else:
                ident=self.db.execute('INSERT INTO incidencias(trabajo_id,catalogo_id,codigo_snapshot,documento,problema,accion,estado,resuelto,creado) VALUES(?,?,?,?,?,?,?,?,?)',vals+(now(),)).lastrowid
            self.audit('incidencias',ident,'guardar',before,self.one('incidencias',ident),motivo)
        return ident

    def toggle(self, table, ident, reason):
        if table not in ('trabajos','catalogos','tareas','folios'):
            raise ValueError('No se permite eliminar ese registro.')
        with self.db:
            before=self.one(table,ident)
            if table=='folios' and self.rows('SELECT id FROM trabajos WHERE folio_id=? AND activo=1',(ident,)):
                raise ValueError('El folio contiene trabajos activos.')
            self.db.execute('UPDATE '+table+' SET activo=? WHERE id=?',(1-before['activo'],ident))
            if table=='catalogos' and before['tipo']=='documento':self.invalidate_catalog(before['codigo'])
            self.audit(table,ident,'activar/desactivar',before,self.one(table,ident),reason)

    def bind_execution(self, ident, work, scope, reason):
        if scope not in ('Legajo','CURP completa','Sin asignar'):
            raise ValueError('Ámbito inválido.')
        with self.db:
            before=self.one('ejecuciones',ident)
            if not before['valido']:
                raise ValueError('Este reporte contiene errores de métricas y no puede vincularse.')
            if scope!='Sin asignar':
                target=self.one('trabajos',work)
                if target['curp']!=before['curp']:
                    raise ValueError('La CURP del reporte no coincide.')
                if scope=='Legajo':
                    if self.rows('SELECT id FROM archivos_tiff WHERE trabajo_id=? LIMIT 1',(work,)) or self.rows("SELECT id FROM operaciones_tiff WHERE trabajo_id=? AND estado='Preparada'",(work,)):
                        raise ValueError('Este expediente tiene TIFF gestionados o una operación pendiente. Usa Organizar para generar su inventario.')
                    payload=json.loads(before['payload'])
                    if target['fisicos'] is not None and payload.get('HOJAS_FISICAS')!=target['fisicos']:
                        raise ValueError('El reporte no coincide con el conteo físico confirmado. Revisa la fuente antes de vincularlo.')
                    self.db.execute('DELETE FROM inventario_pendiente WHERE trabajo_id=?',(work,))
            else:
                work=None
            self.db.execute('UPDATE ejecuciones SET trabajo_id=?,ambito=? WHERE id=?',(work,scope,ident))
            self.audit('ejecuciones',ident,'vincular',before,self.one('ejecuciones',ident),reason)

    def invalidate_inventory(self, work, reason):
        self.db.execute('UPDATE validaciones SET vigente=0 WHERE trabajo_id=?',(work,))
        self.db.execute("UPDATE trabajos SET calidad='No revisado' WHERE id=? AND calidad='Aprobado'",(work,))
        self.db.execute('INSERT OR REPLACE INTO inventario_pendiente VALUES(?,?)',(work,reason))
        self.db.execute("UPDATE ejecuciones SET valido=0,observacion=observacion || ' | ' || ? WHERE trabajo_id=? AND valido=1",(reason,work))
        self.db.execute('UPDATE trabajos SET carpetas=0 WHERE id=?',(work,))

    def latest(self, ident):
        if self.rows('SELECT 1 FROM inventario_pendiente WHERE trabajo_id=?',(ident,)):return None
        if self.rows("SELECT 1 FROM operaciones_tiff WHERE trabajo_id=? AND estado='Preparada'",(ident,)):return None
        if self.rows('SELECT id FROM validaciones WHERE trabajo_id=? LIMIT 1',(ident,)):
            from .delivery import Deliveries
            if Deliveries(self).current_validation(ident) is None:return None
        rows=self.rows("SELECT * FROM ejecuciones WHERE trabajo_id=? AND ambito='Legajo' AND valido=1 ORDER BY fecha DESC,id DESC LIMIT 1",(ident,))
        return rows[0] if rows else None

    def save_task(self, titulo, estado='Pendiente', work=None, notas='', ident=None, motivo='Guardar tarea'):
        if not titulo.strip() or estado not in TASK_STATES:
            raise ValueError('Revisa título y estado de la tarea.')
        with self.db:
            old=self.one('tareas',ident) if ident else None
            vals=(titulo,estado,work,notas)
            if ident:
                self.db.execute('UPDATE tareas SET titulo=?,estado=?,trabajo_id=?,notas=? WHERE id=?',vals+(ident,))
            else:
                ident=self.db.execute('INSERT INTO tareas(titulo,estado,trabajo_id,notas) VALUES(?,?,?,?)',vals).lastrowid
            self.audit('tareas',ident,'guardar',old,self.one('tareas',ident),motivo)
        return ident

    def dashboard(self, works):
        result={'Trabajos activos':len(works),'CURP distintas':len(set(w['curp'] for w in works)),
                'Cerrados':sum(w['estado']==STATES[-1] for w in works),'Hojas físicas confirmadas':sum(w['fisicos'] or 0 for w in works),
                'Sin conteo confirmado':sum(w['fisicos'] is None for w in works),'Con inventario vinculado':0,
                'Archivos TIFF':0,'Páginas conocidas':0,'TIFF declarados en reportes legados':0,'Inventarios parciales':0,'Incidencias abiertas':0,'Inventarios desactualizados':0}
        for w in works:
            active_files=self.rows('SELECT paginas FROM archivos_tiff WHERE trabajo_id=? AND activo=1',(w['id'],))
            result['Archivos TIFF']+=len(active_files)
            result['Páginas conocidas']+=sum(r['paginas'] for r in active_files)
            if self.rows('SELECT 1 FROM inventario_pendiente WHERE trabajo_id=?',(w['id'],)):result['Inventarios desactualizados']+=1
            result['Incidencias abiertas']+=self.db.execute("SELECT COUNT(*) FROM incidencias WHERE trabajo_id=? AND estado='Abierta'",(w['id'],)).fetchone()[0]
            e=self.latest(w['id'])
            if e:
                p=json.loads(e['payload']); result['Con inventario vinculado']+=1
                if not self.rows('SELECT id FROM archivos_tiff WHERE trabajo_id=? LIMIT 1',(w['id'],)):
                    result['TIFF declarados en reportes legados']+=int(p['TOTAL_DIGITALES_TIFF'])
                result['Inventarios parciales']+=p['ESTADO_CONTEO_PAGINAS']!='COMPLETO'
        result['Identidades con registros asociados']=sum(w.get('registros',1)>1 for w in works)
        result['Avance de cierre (%)']=round(100*result['Cerrados']/len(works),1) if works else None
        return result

    def backup(self, full=False):
        if full:
            from .backup import create_backup
            return create_backup(self)
        dest=self.workspace.backups/('digitalizacion_'+dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.sqlite3')
        dest.parent.mkdir(exist_ok=True)
        from .backup import snapshot
        snapshot(self.db,dest)
        return dest

    def export(self, works, folder):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
        details=[]
        for w in works:
            row=dict(w);e=self.latest(w['id'])
            if e:
                row.update(json.loads(e['payload']))
            details.append(row)
        self.csv_write(folder/'trabajos.csv',details)
        self.csv_write(folder/'indicadores.csv',[{'indicador':k,'valor':v} for k,v in self.dashboard(works).items()])
        self.csv_write(folder/'historial.csv',self.rows('SELECT * FROM historial'))
        self.csv_write(folder/'incidencias.csv',self.rows('SELECT * FROM incidencias'))
        self.csv_write(folder/'catalogos.csv',self.rows('SELECT * FROM catalogos'))
        self.csv_write(folder/'ejecuciones.csv',self.rows('SELECT * FROM ejecuciones'))
        self.csv_write(folder/'pendientes.csv',self.rows('SELECT * FROM pendientes'))
        self.csv_write(folder/'auditoria.csv',self.rows('SELECT * FROM auditoria'))
        from .reporting import Reporting
        Reporting(self).export_datasets(folder)
        return folder

    @staticmethod
    def csv_write(path, rows):
        fields=list(dict.fromkeys(k for row in rows for k in row)) or ['sin_registros']
        with open(str(path),'w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fields,delimiter=';');writer.writeheader()
            for row in rows:
                writer.writerow({k:("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v) for k,v in row.items()})
