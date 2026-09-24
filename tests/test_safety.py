import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import Store, ROOT
from app.workspace import Workspace
from app.backup import create_backup, verify_backup, restore_backup, backup_existing, sha256
from app.coding import CodingService, render_page, combined_operations
from app.demo import create_demo
import test_coding as fixtures
import test_domain as domain


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
    def tearDown(self):self.temp.cleanup()
    def test_relative_workspace_independent_of_current_directory(self):
        old=Path.cwd()
        try:
            os.chdir(self.root)
            self.assertEqual(Workspace('demos/prueba').root,ROOT/'demos'/'prueba')
        finally:os.chdir(old)
    def test_db_uses_its_own_root(self):
        s=Store(self.root/'aislada'/'test.sqlite3')
        try:
            self.assertEqual(CodingService(s).root,self.root/'aislada')
            self.assertIn(self.root,s.backup().parents)
        finally:s.db.close()
    def test_demo_refuses_existing_destination(self):
        (self.root/'sentinel').write_bytes(b'conservar')
        with self.assertRaises(FileExistsError):create_demo(self.root)
        self.assertEqual((self.root/'sentinel').read_bytes(),b'conservar')
    def test_two_demos_are_isolated_and_backup_restores_files(self):
        a=create_demo(self.root/'a');b=create_demo(self.root/'b')
        s=Store(workspace=a)
        try:
            backup=create_backup(s,self.root/'backup')
            restored=restore_backup(backup,self.root/'restored')
            original_files={p.relative_to(a).as_posix():sha256(p) for p in (a/'datos'/'tiff').rglob('*') if p.is_file()}
            for name,expected in original_files.items():self.assertEqual(sha256(restored/name),expected)
            self.assertTrue((b/'datos'/'digitalizacion.sqlite3').is_file())
        finally:s.db.close()
    def test_backup_wal_and_corruption_refused(self):
        s=Store(workspace=self.root/'live')
        try:
            s.db.execute('PRAGMA journal_mode=WAL')
            s.save_folio('WAL/2026','')
            out=create_backup(s,self.root/'backup')
            self.assertEqual(len(verify_backup(out)['files']),1)
            target=restore_backup(out,self.root/'restore')
            db=sqlite3.connect(str(target/'datos'/'digitalizacion.sqlite3'))
            self.assertEqual(db.execute('SELECT numero FROM folios').fetchone()[0],'WAL/2026');db.close()
            with self.assertRaises(FileExistsError):restore_backup(out,target)
            (out/'datos'/'digitalizacion.sqlite3').write_bytes(b'damaged')
            with self.assertRaises(ValueError):restore_backup(out,self.root/'rejected')
            self.assertFalse((self.root/'rejected').exists())
        finally:s.db.close()
    def test_simultaneous_store_refused_and_lock_released(self):
        s=Store(workspace=self.root)
        with self.assertRaises(ValueError):Store(workspace=self.root)
        s.db.close()
        other=Store(workspace=self.root);other.db.close()

    def test_sqlite_sidecars_excluded_before_resolving_locked_paths(self):
        from app.manifests import plain_path
        s=Store(workspace=self.root/'live')
        try:
            s.db.execute('PRAGMA journal_mode=WAL');s.save_folio('WAL-SIN-RESOLVER','')
            (s.workspace.root/'datos/otra.sqlite3-journal').write_bytes(b'journal excluido')
            document=s.workspace.root/'datos/evidencia.txt';document.write_bytes(b'conservar')
            visited=[]
            def guarded(root,name):
                visited.append(name)
                if name.endswith(('-wal','-shm','-journal')):raise PermissionError('Windows bloquea el auxiliar SQLite')
                return plain_path(root,name)
            with patch('app.backup.plain_path',side_effect=guarded):out=create_backup(s,self.root/'backup')
            self.assertFalse(any(n.endswith(('-wal','-shm','-journal')) for n in visited))
            self.assertIn('datos/evidencia.txt',visited)
            self.assertEqual((out/'datos/evidencia.txt').read_bytes(),b'conservar')
            with sqlite3.connect(str(out/'datos/digitalizacion.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT numero FROM folios').fetchone()[0],'WAL-SIN-RESOLVER')
            self.assertEqual(set(verify_backup(out)['files']),{'datos/digitalizacion.sqlite3','datos/evidencia.txt'})
        finally:s.db.close()

    def test_permission_error_on_included_file_still_stops_backup(self):
        from app.manifests import plain_path
        s=Store(workspace=self.root/'live')
        try:
            (s.workspace.root/'datos/evidencia.txt').write_bytes(b'conservar')
            def guarded(root,name):
                if name=='datos/evidencia.txt':raise PermissionError('Archivo incluido inaccesible')
                return plain_path(root,name)
            with patch('app.backup.plain_path',side_effect=guarded):
                with self.assertRaises(PermissionError):create_backup(s,self.root/'incompleto')
            self.assertTrue((self.root/'incompleto/INCOMPLETO.txt').exists())
        finally:s.db.close()
    def test_legacy_backup_does_not_migrate(self):
        dbpath=self.root/'datos'/'digitalizacion.sqlite3';dbpath.parent.mkdir()
        db=sqlite3.connect(str(dbpath));db.executescript((ROOT/'app'/'schema.sql').read_text());db.close()
        before=sha256(dbpath)
        out=backup_existing(Workspace(self.root),self.root/'respaldos'/'antes')
        self.assertEqual(sha256(dbpath),before);verify_backup(out)
    def test_paths_windows_accents_traversal_absolute(self):
        ws=Workspace(self.root)
        self.assertEqual(ws.path(r'datos\tiff\José Pérez.tif'),self.root/'datos'/'tiff'/'José Pérez.tif')
        for name in ('../escape','datos/../../escape',str(self.root.parent/'escape')):
            with self.assertRaises(ValueError):ws.path(name)
        if os.name!='nt':
            with self.assertRaises(ValueError):ws.path(r'C:\Oficina\datos\uno.tif')
    @unittest.skipIf(os.name=='nt','Crear symlinks en Windows requiere permisos especiales; comprobar manualmente junctions')
    def test_symlink_escape_refused(self):
        (self.root/'datos').symlink_to(self.root.parent,target_is_directory=True)
        with self.assertRaises(ValueError):Workspace(self.root).path('datos/ajeno.tif')

    @unittest.skipIf(os.name=='nt','Symlink requiere privilegios en Windows')
    def test_database_symlink_cannot_write_outside_workspace(self):
        outside=self.root/'outside';outside.mkdir()
        workspace=self.root/'workspace';workspace.mkdir()
        (workspace/'datos').symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):Store(workspace=workspace)
        self.assertEqual(list(outside.iterdir()),[])

    def test_diagnostic_does_not_create_workspace(self):
        import main
        from contextlib import redirect_stdout
        import io
        target=self.root/'no-creado'
        with redirect_stdout(io.StringIO()):main.diagnostic(Workspace(target))
        self.assertFalse(target.exists())

    def test_full_backup_rejects_missing_original(self):
        root=create_demo(self.root/'demo')
        s=Store(workspace=root)
        try:
            row=s.rows('SELECT original FROM archivos_tiff LIMIT 1')[0]
            s.workspace.path(row['original']).unlink()
            with self.assertRaises(ValueError):create_backup(s,self.root/'incompleto')
            with self.assertRaises(ValueError):verify_backup(self.root/'incompleto')
        finally:s.db.close()

    def test_interrupted_restore_cannot_be_opened(self):
        s=Store(workspace=self.root/'source')
        try:backup=create_backup(s,self.root/'backup')
        finally:s.db.close()
        with patch('app.backup.shutil.copy2',side_effect=OSError('copia interrumpida')):
            with self.assertRaises(OSError):restore_backup(backup,self.root/'partial')
        with self.assertRaises(ValueError):Store(workspace=self.root/'partial')


class MigrationTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'test.sqlite3'
    def tearDown(self):self.temp.cleanup()
    def legacy(self):
        db=sqlite3.connect(str(self.path));db.executescript((ROOT/'app'/'schema.sql').read_text());db.close()
    def test_upgrade_repeated_preserves_versions_and_data(self):
        self.legacy();s=Store(self.path);s.save_folio('PRESERVADO','');s.db.close()
        s=Store(self.path)
        try:
            CodingService(s);CodingService(s)
            self.assertEqual(s.rows("SELECT value FROM meta WHERE key='coding_schema_version'")[0]['value'],'3')
            self.assertEqual(s.rows('SELECT numero FROM folios')[0]['numero'],'PRESERVADO')
            self.assertEqual(len(list((self.path.parent/'respaldos').glob('*.sqlite3'))),1)
        finally:s.db.close()
    def test_future_schema_rejected_without_database_write(self):
        self.legacy();db=sqlite3.connect(str(self.path));db.execute("UPDATE meta SET value='99' WHERE key='schema_version'");db.commit();db.close()
        before=sha256(self.path)
        with self.assertRaises(ValueError):Store(self.path)
        self.assertEqual(sha256(self.path),before)
    def test_failed_migration_rolls_back_ddl(self):
        from app import migrations
        self.legacy();original=migrations.statements
        def fail(db,script):
            original(db,script)
            if 'expediente_preferido' in script:raise OSError('disco lleno simulado')
        with patch.object(migrations,'statements',side_effect=fail):
            with self.assertRaises(OSError):Store(self.path)
        db=sqlite3.connect(str(self.path))
        self.assertEqual(db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],'1')
        self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='expediente_preferido'").fetchone());db.close()
        s=Store(self.path);s.db.close()


class FileSafetyTests(unittest.TestCase):
    setUp=fixtures.CodingTests.setUp
    tearDown=fixtures.CodingTests.tearDown
    make=fixtures.CodingTests.make
    load=fixtures.CodingTests.load
    def test_hl100_catalog_assign_organize(self):
        self.s.save_catalog('documento','HL-100','FEDERAL','Historia sintética')
        ident=self.load();self.c.assign(ident,'HL-100');self.c.organize(self.w)
        self.assertEqual(self.c.file(ident)['codigo'],'HL-100')
        self.assertEqual(next(c for c in self.c.catalog() if c['codigo']=='HL-100')['numero'],100)
    def test_old_letter_limit_does_not_limit_numeric_catalog(self):
        self.s.save_catalog('documento','HL-100','FEDERAL','Documento de prueba')
        with patch('app.coding.SHORTCUTS',[]):
            self.assertTrue(any(c['codigo']=='HL-100' for c in self.c.catalog()))

    def test_rescan_export_contains_physical_identity(self):
        ident=self.load();self.c.assign(ident,'DP-01')
        self.c.mark_correction(ident,1,'Sin número físico registrado','Borrosa')
        row=self.c.corrections(self.w)[0]
        self.assertEqual((row['curp'],row['legajo'],row['codigo']),('AAAA900101HYNBBB01',1,'DP-01'))
        self.assertEqual(row['ubicacion'],'Sin número físico registrado')

    def test_report_failure_keeps_inventory_stale(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.c.organize(self.w)
        with patch.object(self.s,'csv_write',side_effect=OSError('disco lleno')):
            with self.assertRaises(OSError):self.c.organize(self.w)
        self.assertIsNone(self.s.latest(self.w));self.assertEqual(self.s.one('trabajos',self.w)['carpetas'],0)
        self.c.organize(self.w);self.assertIsNotNone(self.s.latest(self.w))
    def test_catalog_change_invalidates_existing_inventory(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.c.organize(self.w)
        self.s.save_catalog('documento','DP-01','FEDERAL','Acta',ident=self.dp)
        self.assertIsNone(self.s.latest(self.w))
        self.c.organize(self.w);self.assertIn('FEDERAL',self.c.file(ident)['ruta'])
        self.s.toggle('catalogos',self.dp,'Prueba');self.assertIsNone(self.s.latest(self.w))
    def test_import_interruption_recovers_without_removing_source(self):
        source=self.make();before=sha256(source)
        with patch.object(self.s,'audit',side_effect=OSError('fallo simulado')):
            result=self.c.import_files(self.w,[source])
        self.assertTrue(result['errores']);self.assertEqual(self.c.files(self.w),[])
        self.assertEqual(self.c.recover(self.w),1);self.assertEqual(sha256(source),before)
        self.assertEqual(len(list((self.c.work_dir(self.w)/'recuperados').glob('*.tif'))),2)
    def test_import_abrupt_interruption_recover(self):
        source=self.make();original=self.c.copy_new
        count=[0]
        def interrupted(src,target):
            original(src,target);count[0]+=1
            if count[0]==2:raise KeyboardInterrupt('cierre simulado')
        with patch.object(self.c,'copy_new',side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):self.c.import_files(self.w,[source])
        self.assertEqual(self.c.recover(self.w),1);self.assertEqual(self.c.files(self.w),[])
    def test_no_overwrite_on_case_collision_or_concurrent_target(self):
        ident=self.load();row=self.c.file(ident);src=self.c.path(row['ruta']);target=src.with_name('DP-01.tif')
        target.write_bytes(b'ajeno')
        with self.assertRaises(ValueError):self.c.move_file(src,target)
        with self.assertRaises(FileExistsError):self.c.copy_new(src,target)
        self.assertEqual(target.read_bytes(),b'ajeno');self.assertTrue(src.exists())
    def test_organize_abrupt_interruption_recovers_move(self):
        ident=self.load();self.c.assign(ident,'DP-01');row=self.c.file(ident)
        original=self.c.move_file
        def stop(a,b):original(a,b);raise KeyboardInterrupt('cierre inesperado')
        with patch.object(self.c,'move_file',side_effect=stop):
            with self.assertRaises(KeyboardInterrupt):self.c.organize(self.w)
        self.assertIsNone(self.s.latest(self.w))
        self.assertEqual(self.c.recover(self.w),1);self.assertTrue(self.c.path(row['ruta']).exists())
    def test_hardlink_interruption_cleans_only_own_link(self):
        ident=self.load();row=self.c.file(ident);src=self.c.path(row['ruta']);target=src.with_name('DP-01.tif')
        self.c.log(self.w,ident,'renombrar',{'antes':row['ruta'],'despues':self.c.relative(target)})
        os.link(str(src),str(target))
        self.c.recover(self.w);self.assertTrue(src.exists());self.assertFalse(target.exists())
    def test_page_replacement_resumes_after_edit_without_reediting(self):
        old=self.load(self.make('multi.tif',3));new=self.load(self.make('single.tif'))
        cid=self.c.mark_correction(old,2,'Sin folio físico registrado','Prueba')
        with patch.object(self.c,'exclude',side_effect=OSError('fallo en retiro')):
            with self.assertRaises(OSError):self.c.replace_scanned_page(cid,new,'Revisada')
        self.assertEqual(len(self.s.rows('SELECT * FROM revisiones_tiff')),1)
        self.assertIsNone(self.s.latest(self.w));self.c.recover(self.w)
        self.assertEqual(len(self.s.rows('SELECT * FROM revisiones_tiff')),1)
        self.assertEqual(self.c.corrections(self.w)[0]['estado'],'Página sustituida')
        self.assertEqual(self.c.file(new)['activo'],0)
    def test_complete_replacement_resumes_after_retirement(self):
        old=self.load(self.make('old.tif',2));new=self.load(self.make('new.tif',3))
        # Crear segundo TIFF de dos páginas con píxeles diferentes.
        self.c.save_edit(new,0,[('rotate',90)])
        self.c.exclude(new,'Fixture auxiliar')
        p=self.make('new2.tif',2)
        from PIL import Image
        with Image.open(p) as im:
            images=[]
            for i in range(im.n_frames):im.seek(i);frame=im.copy();frame.putpixel((0,0),0);images.append(frame)
        images[0].save(p,save_all=True,append_images=images[1:])
        for im in images:im.close()
        new=self.load(p);cid=self.c.mark_correction(old,1,'Separador A','Prueba')
        original=self.s.audit
        def failure(entity,*args):
            if entity=='correcciones_tiff':raise OSError('fallo al resolver')
            return original(entity,*args)
        with patch.object(self.s,'audit',side_effect=failure):
            with self.assertRaises(OSError):self.c.replace_correction(cid,new,'Verificado')
        self.assertEqual(self.c.file(old)['activo'],0)
        self.c.recover(self.w);self.assertEqual(self.c.corrections(self.w)[0]['estado'],'Sustituida')
    def test_unreadable_tiff_not_counted_as_zero(self):
        p=self.input/'bad.tif';p.write_bytes(b'not tiff')
        r=self.c.import_files(self.w,[p]);self.assertTrue(r['errores']);self.assertEqual(r['importados'],0)
    def test_rotation_preview_combines_angles_from_source(self):
        self.assertAlmostEqual(combined_operations([('rotate',.2),('rotate',.2)])[0][1],.4)
        p=self.make();a=render_page(p,0,[('rotate',.2),('rotate',-.2)]);b=render_page(p,0)
        self.assertEqual(a.tobytes(),b.tobytes());a.close();b.close()


class IdentitySafetyTests(unittest.TestCase):
    setUp=domain.DomainTests.setUp
    tearDown=domain.DomainTests.tearDown
    def test_filter_never_changes_principal_or_hides_relations(self):
        f2=self.s.save_folio('SEGUNDO','');self.s.db.execute('DROP TRIGGER IF EXISTS no_nueva_identidad_duplicada')
        with self.s.db:
            second=self.s.db.execute('INSERT INTO trabajos(folio_id,curp,legajo,estado_desde) VALUES(?,?,?,?)',(f2,domain.A,1,'2026-09-21')).lastrowid
        self.s.add_count(second,7);self.s.prefer(second,'Registro operativo verificado')
        row=self.s.works(folio='TEST/2026')[0]
        self.assertEqual(row['id'],second);self.assertEqual(row['registros'],2)
        self.assertEqual(len(self.s.duplicate_diagnostics()),2)
        self.assertEqual(self.s.count_total(second),7)
    def test_lowercase_normalization_and_legajo_validation(self):
        with self.assertRaises(ValueError):self.s.save_work(self.f,' '+domain.A.lower()+' ','Otra',1)
        for value in (0,-1,'1.5',''):
            with self.assertRaises(ValueError):self.s.save_work(self.f,domain.A,'Otra',value)
