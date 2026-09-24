"""Regresiones de recuperación y traslado 0.4.1, exclusivamente sintéticas."""
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.backup import create_backup, restore_backup, sha256, verify_backup
from app.core import Store
from app.demo import create_demo
from app.update_recovery import restore_code, inspect_recovery, database_fingerprint
from actualizar import apply_update, inspect_release
import test_coding as coding
import test_update as updating


class MoveTests(unittest.TestCase):
    setUp=coding.CodingTests.setUp
    tearDown=coding.CodingTests.tearDown
    make=coding.CodingTests.make
    load=coding.CodingTests.load
    def test_source_unlink_failure_removes_only_new_link(self):
        ident=self.load();source=self.c.path(self.c.file(ident)['ruta']);target=source.with_name('DP-01.tif')
        unlink=Path.unlink
        def fail(path,*args,**kwargs):
            if path==source:raise PermissionError('origen bloqueado')
            return unlink(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail):
            with self.assertRaises(PermissionError):self.c.assign(ident,'DP-01')
        self.assertTrue(source.is_file());self.assertFalse(target.exists())
        self.assertFalse(self.s.rows("SELECT id FROM operaciones_tiff WHERE estado='Preparada'"))
        self.c.assign(ident,'DP-01')
    def test_failed_move_cleanup_remains_recoverable(self):
        ident=self.load();source=self.c.path(self.c.file(ident)['ruta']);target=source.with_name('DP-01.tif')
        unlink=Path.unlink
        def fail(path,*args,**kwargs):
            if path in (source,target):raise PermissionError('disco temporalmente bloqueado')
            return unlink(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail):
            with self.assertRaisesRegex(ValueError,'Recuperar'):self.c.assign(ident,'DP-01')
        self.assertTrue(os.path.samefile(str(source),str(target)))
        self.assertEqual(len(self.s.rows("SELECT id FROM operaciones_tiff WHERE estado='Preparada'")),1)
        with self.assertRaises(ValueError):self.c.assign(ident,'HL-01')
        self.assertEqual(self.c.recover(self.w),1);self.assertTrue(source.exists());self.assertFalse(target.exists())
        self.assertEqual(self.c.recover(self.w),0)
    def test_retirement_cleanup_failure_uses_same_recovery(self):
        ident=self.load();source=self.c.path(self.c.file(ident)['ruta']);unlink=Path.unlink
        def fail(path,*args,**kwargs):
            if path.suffix=='.tif':raise PermissionError('TIFF bloqueado')
            return unlink(path,*args,**kwargs)
        with patch.object(Path,'unlink',fail):
            with self.assertRaisesRegex(ValueError,'Recuperar'):self.c.exclude(ident,'Prueba')
        self.assertEqual(self.c.recover(self.w),1);self.assertEqual(self.c.file(ident)['activo'],1)
        self.assertTrue(source.exists())

    def test_recount_invalidates_report_until_reorganization(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.c.organize(self.w)
        self.s.add_count(self.w,4);self.s.confirm_count(self.w)
        self.assertIsNone(self.s.latest(self.w))
        self.c.organize(self.w)
        self.assertEqual(json.loads(self.s.latest(self.w)['payload'])['HOJAS_FISICAS'],14)
    def test_new_folio_cannot_rewrite_old_cycle_or_report(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.c.organize(self.w)
        folio=self.s.save_folio('NUEVO-FOLIO','')
        with self.assertRaises(ValueError):self.s.save_work(folio,'AAAA900101HYNBBB01','Prueba',1,ident=self.w,motivo='Reasignación')
        self.assertIsNotNone(self.s.latest(self.w))
        self.assertNotEqual(self.s.one('trabajos',self.w)['folio_id'],folio)
    def test_external_inventory_cannot_override_managed_files(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.c.organize(self.w)
        report=self.s.latest(self.w)
        with self.assertRaisesRegex(ValueError,'TIFF gestionados'):
            self.s.bind_execution(report['id'],self.w,'Legajo','Intento de vincular otro inventario')
        self.assertEqual(self.s.latest(self.w)['id'],report['id'])


class BackupManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.s=Store(workspace=self.root/'source');self.backup=create_backup(self.s,self.root/'backup')
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def change(self,entries):
        path=self.backup/'manifest.json';data=json.loads(path.read_text());data['files'].update(entries);path.write_text(json.dumps(data))
    def test_absolute_path_rejected_before_restore_creates_destination(self):
        self.change({str(self.backup/'datos/digitalizacion.sqlite3'):sha256(self.backup/'datos/digitalizacion.sqlite3')})
        with self.assertRaises(ValueError):restore_backup(self.backup,self.root/'rejected')
        self.assertFalse((self.root/'rejected').exists())
    def test_case_collision_rejected_before_copy(self):
        self.change({'DATOS/digitalizacion.sqlite3':sha256(self.backup/'datos/digitalizacion.sqlite3')})
        with self.assertRaises(ValueError):verify_backup(self.backup)
    def test_nonportable_or_reserved_names_rejected(self):
        original=(self.backup/'manifest.json').read_text()
        for name in ('datos/CON.txt','datos/a/../b.txt','datos/a.txt:extra','datos/archivo.','datos\\archivo.txt','datos/control\t.txt','main.py'):
            (self.backup/'manifest.json').write_text(original);self.change({name:'0'*64})
            with self.assertRaises(ValueError,msg=name):verify_backup(self.backup)
    @unittest.skipIf(os.name=='nt','Crear symlinks requiere permisos especiales en Windows')
    def test_symlink_inside_backup_also_rejected(self):
        (self.backup/'datos/alias.sqlite3').symlink_to(self.backup/'datos/digitalizacion.sqlite3')
        self.change({'datos/alias.sqlite3':sha256(self.backup/'datos/digitalizacion.sqlite3')})
        with self.assertRaises(ValueError):verify_backup(self.backup)
    @unittest.skipIf(os.name=='nt','Crear symlinks requiere permisos especiales en Windows')
    def test_backup_refuses_linked_source_directory(self):
        (self.s.workspace.root/'reportes').mkdir(exist_ok=True)
        (self.s.workspace.root/'datos/alias').symlink_to(self.s.workspace.root/'reportes',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'enlaces'):create_backup(self.s,self.root/'rejected')
        self.assertTrue((self.root/'rejected/INCOMPLETO.txt').is_file())
    def test_missing_manifest_reference_caught_before_restore(self):
        demo=create_demo(self.root/'demo');s=Store(workspace=demo)
        try:backup=create_backup(s,self.root/'demo-backup')
        finally:s.db.close()
        path=backup/'manifest.json';data=json.loads(path.read_text());name=next(n for n in data['files'] if '/originales/' in n)
        del data['files'][name];path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'omite'):restore_backup(backup,self.root/'rejected')
        self.assertFalse((self.root/'rejected').exists())


class CodeRecoveryTests(unittest.TestCase):
    setUp=updating.UpdateTests.setUp
    tearDown=updating.UpdateTests.tearDown
    write_manifest=updating.UpdateTests.write_manifest
    def test_completed_update_can_revert_without_changing_database(self):
        path=self.target/'datos/digitalizacion.sqlite3';before=sha256(path)
        recovery=apply_update(self.source,self.target);restore_code(recovery,self.target)
        for name in self.files:self.assertEqual((self.target/name).read_text(),'viejo '+name)
        self.assertEqual(sha256(path),before)
        self.assertFalse((self.target/'.actualizacion_pendiente.json').exists())
        restore_code(recovery,self.target)  # Repetir no perjudica el código ni los datos.
    def test_interrupted_update_recovery_and_added_file_removal(self):
        added='app/nuevo.py';(self.source/added).write_text('nuevo módulo')
        self.manifest['files'][added]=sha256(self.source/added);self.write_manifest()
        original=os.replace
        def stop(src,dst):
            result=original(src,dst)
            if 'codigo_nuevo' in str(src) and str(dst).endswith('nuevo.py'):raise KeyboardInterrupt('corte tras copia')
            return result
        before=sha256(self.target/'datos/digitalizacion.sqlite3')
        with patch('actualizar.os.replace',side_effect=stop):
            with self.assertRaises(KeyboardInterrupt):apply_update(self.source,self.target)
        pending=json.loads((self.target/'.actualizacion_pendiente.json').read_text());recovery=Path(pending['resguardo'])
        restore_code(recovery,self.target)
        for name in self.files:self.assertEqual((self.target/name).read_text(),'viejo '+name)
        self.assertFalse((self.target/added).exists());self.assertEqual(sha256(self.target/'datos/digitalizacion.sqlite3'),before)
    def test_captured_data_blocks_code_recovery(self):
        recovery=apply_update(self.source,self.target)
        s=Store(workspace=self.target);s.save_folio('CAPTURA-POSTERIOR','');s.db.close()
        before=sha256(self.target/'datos/digitalizacion.sqlite3')
        with self.assertRaisesRegex(ValueError,'datos cambiaron'):restore_code(recovery,self.target)
        self.assertEqual(sha256(self.target/'datos/digitalizacion.sqlite3'),before)
        self.assertEqual((self.target/'main.py').read_text(),'nuevo main.py')
    def test_wal_committed_data_also_blocks_recovery(self):
        db=sqlite3.connect(str(self.target/'datos/digitalizacion.sqlite3'));db.execute('PRAGMA journal_mode=WAL')
        try:
            recovery=apply_update(self.source,self.target)
            before=database_fingerprint(db)
            db.execute("INSERT INTO folios(numero) VALUES('NUEVO-EN-WAL')");db.commit()
            self.assertNotEqual(database_fingerprint(db),before)
            with self.assertRaisesRegex(ValueError,'datos cambiaron'):restore_code(recovery,self.target)
        finally:db.close()
    def test_changed_document_blocks_recovery(self):
        recovery=apply_update(self.source,self.target);p=self.target/'datos/conservar.txt';p.write_text('captura posterior')
        with self.assertRaisesRegex(ValueError,'datos cambiaron'):restore_code(recovery,self.target)
        self.assertEqual(p.read_text(),'captura posterior')
    def test_user_code_changes_are_not_overwritten(self):
        recovery=apply_update(self.source,self.target);p=self.target/'main.py';p.write_text('edición manual posterior')
        with self.assertRaisesRegex(ValueError,'modificado después'):restore_code(recovery,self.target)
        self.assertEqual(p.read_text(),'edición manual posterior')
    def test_damaged_old_code_blocks_recovery_before_changes(self):
        recovery=apply_update(self.source,self.target);(recovery/'codigo_antes/main.py').write_text('dañado')
        with self.assertRaises(ValueError):restore_code(recovery,self.target)
        self.assertEqual((self.target/'main.py').read_text(),'nuevo main.py')
    def test_interrupted_recovery_is_repeatable(self):
        recovery=apply_update(self.source,self.target);original=os.replace;count=[0]
        def stop(src,dst):
            result=original(src,dst)
            if 'codigo_restituir' in str(src):
                count[0]+=1
                if count[0]==2:raise KeyboardInterrupt('corte en recuperación')
            return result
        with patch('app.update_recovery.os.replace',side_effect=stop):
            with self.assertRaises(KeyboardInterrupt):restore_code(recovery,self.target)
        self.assertTrue((self.target/'.actualizacion_pendiente.json').is_file())
        restore_code(recovery,self.target)
        for name in self.files:self.assertEqual((self.target/name).read_text(),'viejo '+name)
    def test_release_manifest_invalid_hash_is_explained(self):
        self.manifest['files']['main.py']=12;self.write_manifest()
        with self.assertRaisesRegex(ValueError,'SHA-256'):inspect_release(self.source,self.target)
