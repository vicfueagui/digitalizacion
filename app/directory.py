"""Catálogos operativos reutilizables; nombres históricos permanecen como snapshots."""
import unicodedata
from .core import now

KINDS={'area':'Áreas','persona':'Personas / responsables','sistema':'Sistemas','ubicacion':'Ubicaciones físicas'}


def normalized(value):
    text=' '.join(str(value or '').split()).casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c))


class Directory:
    def __init__(self,store):self.s=store;self.db=store.db
    def get(self,ident):
        rows=self.s.rows('SELECT * FROM directorio WHERE id=?',(ident,))
        if not rows:raise ValueError('Registro del directorio inexistente.')
        return rows[0]
    def entries(self,kind,query='',inactive=False):
        if kind not in KINDS:raise ValueError('Tipo de directorio inválido.')
        return [r for r in self.s.rows('SELECT * FROM directorio WHERE tipo=? AND (activo=1 OR ?=1) ORDER BY nombre',(kind,int(inactive))) if normalized(query) in normalized(r['nombre']+' '+r['notas'])]
    def find(self,kind,name):
        rows=self.s.rows('SELECT d.* FROM directorio_alias a JOIN directorio d ON d.id=a.directorio_id WHERE a.tipo=? AND a.clave=?',(kind,normalized(name)))
        return rows[0] if rows else None
    def ensure(self,kind,name,allow_inactive=False):
        """Participa en la transacción del llamador; no confirma por su cuenta."""
        if kind not in KINDS:raise ValueError('Tipo de directorio inválido.')
        name=' '.join(str(name or '').split())
        if not name:return None
        found=self.find(kind,name)
        if found:
            if not found['activo'] and not allow_inactive:raise ValueError('Registro desactivado: '+found['nombre']+'. Reactívalo en Directorio para reutilizarlo.')
            return found['id']
        stamp=now();ident=self.db.execute('INSERT INTO directorio(tipo,nombre,clave,creado,actualizado) VALUES(?,?,?,?,?)',(kind,name,normalized(name),stamp,stamp)).lastrowid
        self.db.execute('INSERT INTO directorio_alias VALUES(?,?,?)',(kind,normalized(name),ident))
        self.s.audit('directorio',ident,'alta',None,self.get(ident),'Alta reutilizable desde captura operativa')
        return ident
    def save(self,kind,name,notes='',ident=None,reason='Alta de directorio'):
        name=' '.join(str(name or '').split())
        if not name or kind not in KINDS:raise ValueError('Indica tipo y nombre.')
        if not reason.strip():raise ValueError('Indica el motivo del cambio.')
        with self.db:
            before=self.get(ident) if ident else None;found=self.find(kind,name)
            if before and before['tipo']!=kind:raise ValueError('El tipo del registro es fijo.')
            if found and found['id']!=ident:raise ValueError('Ese nombre o un alias ya está registrado; utiliza o reactiva el existente.')
            if ident:
                self.db.execute('UPDATE directorio SET nombre=?,clave=?,notas=?,actualizado=? WHERE id=?',(name,normalized(name),notes,now(),ident))
                self.db.execute('INSERT OR IGNORE INTO directorio_alias VALUES(?,?,?)',(kind,normalized(name),ident))
            else:
                ident=self.ensure(kind,name);self.db.execute('UPDATE directorio SET notas=? WHERE id=?',(notes,ident))
            self.s.audit('directorio',ident,'guardar',before,self.get(ident),reason)
        return ident
    def toggle(self,ident,reason):
        with self.db:
            before=self.get(ident)
            self.db.execute('UPDATE directorio SET activo=?,actualizado=? WHERE id=?',(1-before['activo'],now(),ident))
            self.s.audit('directorio',ident,'baja/reactivación',before,self.get(ident),reason)


def seed(store):
    directory=Directory(store)
    fields={'folios':[('area_origen','area_id','area'),('entrega','entrega_id','persona'),('recibe','recibe_id','persona'),('responsable','responsable_id','persona')],
            'trabajos':[('digitalizador','digitalizador_id','persona')],'asignaciones':[('persona','persona_id','persona')],
            'prestamo_items':[('ubicacion_original','ubicacion_id','ubicacion'),('devolucion_recibe','devolucion_recibe_id','persona')],
            'observaciones_revision':[('responsable','responsable_id','persona')]}
    for table,columns in fields.items():
        for row in store.rows('SELECT * FROM '+table):
            for source,target,kind in columns:
                ident=directory.ensure(kind,row[source],allow_inactive=True)
                if ident:store.db.execute('UPDATE '+table+' SET '+target+'=? WHERE id=?',(ident,row['id']))
