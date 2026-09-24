"""Entrada de escritorio y herramientas locales. Diagnóstico de solo lectura."""
import argparse
import getpass
import sqlite3
import sys
from app.workspace import Workspace, absolute
from app import VERSION


def diagnostic(workspace):
    import platform
    from app.migrations import CORE_VERSION, CODING_VERSION
    print('Sistema:', platform.system(), platform.release(), platform.machine())
    print('Python:', sys.version.split()[0], '| SQLite:', sqlite3.sqlite_version)
    try:
        import tkinter
        print('Tk importable:', tkinter.TkVersion, '(prueba de ventana: python -m tkinter)')
    except ImportError:
        print('Tkinter no disponible; requiere intérprete con Tcl/Tk.')
    try:
        import PIL
        from PIL import features
        print('Pillow:', PIL.__version__, '| libtiff:', features.check('libtiff'))
    except ImportError:
        print('Pillow no instalado; consulta docs/LAPTOP.md o docs/WINDOWS7.md.')
    print('Espacio:', workspace.root)
    print('Base:', workspace.database)
    if not workspace.database.exists():
        print('Base inexistente. No se creó ninguna carpeta ni base.')
        return
    db = sqlite3.connect(workspace.database.as_uri() + '?mode=ro', uri=True)
    try:
        print('Integridad:', db.execute('PRAGMA integrity_check').fetchone()[0])
        print('Errores de relaciones:', len(db.execute('PRAGMA foreign_key_check').fetchall()))
        versions = dict(db.execute("SELECT key,value FROM meta WHERE key IN ('schema_version','coding_schema_version')"))
        print('Esquema actual:', versions, '| soportado:', CORE_VERSION, CODING_VERSION)
        duplicates = db.execute('SELECT COUNT(*) FROM (SELECT 1 FROM trabajos GROUP BY UPPER(TRIM(curp)),legajo HAVING COUNT(*)>1)').fetchone()[0]
        print('Identidades con varios registros/ciclos:', duplicates, '(no implica duplicación del maestro)')
        if 'conciliacion_pendiente' in {r[1] for r in db.execute('PRAGMA table_info(trabajos)')}:
            print('Ciclos históricos pendientes de conciliación:',db.execute('SELECT COUNT(*) FROM trabajos WHERE conciliacion_pendiente=1').fetchone()[0])
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Digitalización local '+VERSION)
    paths = parser.add_mutually_exclusive_group()
    paths.add_argument('--workspace', help='Raíz de todos los datos; rutas relativas al código')
    paths.add_argument('--db', help='Base alternativa; TIFF y respaldos se aíslan junto a ella')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--crear-demo', metavar='DESTINO_NUEVO')
    actions.add_argument('--diagnostico', action='store_true')
    actions.add_argument('--importar-excel')
    actions.add_argument('--importar-csv')
    actions.add_argument('--respaldar', metavar='DESTINO_NUEVO')
    actions.add_argument('--verificar-respaldo', metavar='RESPALDO')
    actions.add_argument('--verificar-entrega', metavar='CARPETA_ENTREGA',help='Solo lectura; comprueba manifest, TIFF y ausencia de residuos')
    parser.add_argument('--manifest-hash',help='Huella esperada al verificar una entrega recibida')
    actions.add_argument('--restaurar', metavar='RESPALDO')
    actions.add_argument('--duplicados', action='store_true', help='Exportar relaciones de duplicados sin fusionarlos')
    parser.add_argument('--destino', help='Espacio NUEVO para --restaurar')
    args = parser.parse_args()
    if sys.version_info < (3, 8): parser.error('Se requiere Python 3.8 o superior.')
    if args.crear_demo:
        from app.demo import create_demo
        print('Demo creada:', create_demo(args.crear_demo)); return
    if args.verificar_respaldo:
        from app.backup import verify_backup
        result = verify_backup(absolute(args.verificar_respaldo))
        print('Respaldo íntegro:', len(result['files']), 'archivos verificados'); return
    if args.verificar_entrega:
        from app.delivery import verify_folder,content_hash
        result=verify_folder(absolute(args.verificar_entrega),args.manifest_hash)
        print('Entrega íntegra:',len(result['items']),'TIFF. Manifest hash:',content_hash(result));return
    if args.restaurar:
        if not args.destino: parser.error('--restaurar requiere --destino con una carpeta que no exista.')
        from app.backup import restore_backup
        print('Restaurado en:', restore_backup(absolute(args.restaurar), args.destino)); return
    ws = Workspace(args.workspace, args.db)
    if args.diagnostico:
        diagnostic(ws); return
    if args.respaldar:
        from app.backup import backup_existing
        print('Respaldo completo:', backup_existing(ws, absolute(args.respaldar))); return
    if not args.workspace and not args.db and not ws.database.exists():
        parser.error('Elige --workspace RUTA o crea una demo con --crear-demo RUTA_NUEVA. No se creó una base productiva.')
    from app.core import Store
    store = Store(args.db, getpass.getuser(), workspace=args.workspace)
    try:
        if args.importar_excel or args.importar_csv:
            from app.importers import import_excel, import_csv
            store.backup()
            if args.importar_excel: print(import_excel(store, absolute(args.importar_excel)))
            if args.importar_csv: print(import_csv(store, absolute(args.importar_csv)))
        elif args.duplicados:
            path = ws.reports / 'diagnostico_duplicados.csv'
            path.parent.mkdir(parents=True, exist_ok=True)
            store.csv_write(path, store.duplicate_diagnostics()); print(path)
        else:
            from app.ui import App
            App(store).mainloop()
    finally:
        store.db.close()


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, sqlite3.Error) as error:
        print('No se completó la operación:', error, file=sys.stderr)
        sys.exit(1)
