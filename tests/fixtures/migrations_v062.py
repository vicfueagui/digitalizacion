"""Migraciones transaccionales; nunca degrada versiones ni fusiona identidades."""
import sqlite3
from .workspace import CODE_ROOT
from .migration_sql import CODING_1, CODING_2

CORE_VERSION = 7
CODING_VERSION = 3


def statements(db, script):
    # executescript confirma transacciones implícitamente: evitarlo al migrar.
    statement = ''
    for line in script.splitlines(True):
        statement += line
        if sqlite3.complete_statement(statement):
            db.execute(statement)
            statement = ''
    if statement.strip():
        raise ValueError('Migración SQL incompleta.')


def version(db, key):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'").fetchone():
        return 0
    row = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
    try:
        result = int(row[0]) if row else 0
    except (ValueError, TypeError):
        raise ValueError('Versión de esquema inválida: ' + key)
    if result < 0:
        raise ValueError('Versión de esquema inválida: ' + key)
    return result


def migrate(store):
    db = store.db
    core = version(db, 'schema_version')
    coding = version(db, 'coding_schema_version')
    if core > CORE_VERSION or coding > CODING_VERSION:
        raise ValueError('Base creada por una versión futura. No se modificó su esquema; utiliza el programa correspondiente.')
    if core == CORE_VERSION and coding == CODING_VERSION:
        return
    if core or coding:
        store.backup()  # Snapshot SQLite consistente antes de cualquier DDL.
    # Reconstrucción documentada por SQLite para retirar la unicidad del hash.
    rebuild = core < 4
    if rebuild:db.execute('PRAGMA foreign_keys=OFF')
    db.execute('BEGIN IMMEDIATE')
    try:
        if core < 1:
            statements(db, (CODE_ROOT / 'app' / 'schema.sql').read_text(encoding='utf-8'))
        if core < 2:
            statements(db, '''CREATE TABLE IF NOT EXISTS expediente_preferido(curp TEXT NOT NULL,legajo INTEGER NOT NULL,trabajo_id INTEGER NOT NULL REFERENCES trabajos(id),PRIMARY KEY(curp,legajo));
CREATE TRIGGER IF NOT EXISTS no_nueva_identidad_duplicada BEFORE INSERT ON trabajos
WHEN EXISTS(SELECT 1 FROM trabajos WHERE UPPER(TRIM(curp))=UPPER(TRIM(NEW.curp)) AND legajo=NEW.legajo)
BEGIN SELECT RAISE(ABORT,'CURP y legajo ya registrados. Reutiliza el expediente existente.'); END;
CREATE TRIGGER IF NOT EXISTS identidad_fija BEFORE UPDATE OF curp,legajo ON trabajos
WHEN NEW.curp!=OLD.curp OR NEW.legajo!=OLD.legajo
BEGIN SELECT RAISE(ABORT,'La identidad CURP/legajo es fija.'); END;
CREATE TABLE IF NOT EXISTS inventario_pendiente(trabajo_id INTEGER PRIMARY KEY REFERENCES trabajos(id),motivo TEXT NOT NULL);
''')
        if coding < 1:
            statements(db, CODING_1)
        if coding < 2:
            # El SQL legado contiene dos sentencias en una línea.
            statements(db, CODING_2.replace(';', ';\n'))
            columns = {r[1] for r in db.execute('PRAGMA table_info(archivos_tiff)')}
            if 'activo' not in columns:
                db.execute('ALTER TABLE archivos_tiff ADD COLUMN activo INTEGER NOT NULL DEFAULT 1')
        if coding < 3:
            db.execute('''CREATE TABLE sustituciones_tiff(
                id INTEGER PRIMARY KEY,correccion_id INTEGER NOT NULL REFERENCES correcciones_tiff(id),
                nuevo_id INTEGER NOT NULL REFERENCES archivos_tiff(id),tipo TEXT NOT NULL,
                fase TEXT NOT NULL,motivo TEXT NOT NULL,creado TEXT NOT NULL,
                UNIQUE(correccion_id))''')
        if core < 3:
            statements(db, (CODE_ROOT / 'app' / 'operational_schema.sql').read_text(encoding='utf-8'))
            from .operational_migration import migrate as migrate_operational
            migrate_operational(store)
        if core < 4:
            columns=[r[1] for r in db.execute('PRAGMA table_info(archivos_tiff)')]
            expected=['id','trabajo_id','ruta','original','hash_original','hash_actual','paginas','codigo','fecha_origen','creacion_origen','importado','estado','activo']
            if set(columns)!=set(expected):raise ValueError('Extensión TIFF desconocida; migración detenida para conservar todos los campos.')
            extras=[r[0] for r in db.execute("SELECT sql FROM sqlite_master WHERE tbl_name='archivos_tiff' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db.execute('''CREATE TABLE archivos_tiff_nuevo(id INTEGER PRIMARY KEY,trabajo_id INTEGER NOT NULL REFERENCES trabajos(id),ruta TEXT NOT NULL UNIQUE,original TEXT NOT NULL,hash_original TEXT NOT NULL,hash_actual TEXT NOT NULL,paginas INTEGER NOT NULL,codigo TEXT,fecha_origen REAL NOT NULL,creacion_origen REAL NOT NULL,importado TEXT NOT NULL,estado TEXT NOT NULL DEFAULT 'Entrada',activo INTEGER NOT NULL DEFAULT 1)''')
            names=','.join(expected)
            db.execute('INSERT INTO archivos_tiff_nuevo('+names+') SELECT '+names+' FROM archivos_tiff')
            db.execute('DROP TABLE archivos_tiff')
            db.execute('ALTER TABLE archivos_tiff_nuevo RENAME TO archivos_tiff')
            for sql in extras:db.execute(sql)
            statements(db, (CODE_ROOT / 'app' / 'assets_schema.sql').read_text(encoding='utf-8'))
            from .assets import migrate as migrate_assets
            migrate_assets(store)
        if core < 5:
            statements(db, (CODE_ROOT / 'app' / 'delivery_schema.sql').read_text(encoding='utf-8'))
        if core < 6:
            statements(db, (CODE_ROOT / 'app' / 'legacy_schema.sql').read_text(encoding='utf-8'))
        if core < 7:
            statements(db, (CODE_ROOT / 'app' / 'intake_schema.sql').read_text(encoding='utf-8'))
            from .directory import seed
            seed(store)
        db.execute("INSERT OR REPLACE INTO meta VALUES('schema_version',?)", (str(CORE_VERSION),))
        db.execute("INSERT OR REPLACE INTO meta VALUES('coding_schema_version',?)", (str(CODING_VERSION),))
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Relaciones inconsistentes: migración cancelada. Conserva el respaldo para revisión.')
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        if rebuild:db.execute('PRAGMA foreign_keys=ON')
