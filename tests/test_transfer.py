import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.backup import sha256
from app.core import Store
from app.demo import create_demo
from app.integrity import read_summary
from app.transfer import export_migration,verify_package,restore_migration,verify_destination,compare_source,publish_folder,MANIFEST
from app.workspace import Workspace,CODE_ROOT
from app.migration_acceptance import activate,rehearse,launch


class TransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.base=Path(cls.temp.name).resolve()
        cls.ws=Workspace(create_demo(cls.base/'Usuario anterior á'))
        with sqlite3.connect(str(cls.ws.database)) as db:
            # Referencia activa absoluta portable al copiar. Auditoría libre permanece intacta.
            ident,relative=db.execute('SELECT id,ruta FROM archivos_tiff LIMIT 1').fetchone()
            db.execute('UPDATE archivos_tiff SET ruta=? WHERE id=?',(str(cls.ws.path(relative)),ident))
        cls.before=read_summary(cls.ws.database);cls.raw=sha256(cls.ws.database)
        cls.result=export_migration(cls.ws,CODE_ROOT,cls.base/'paquete',laboratory=True)
        cls.package=Path(cls.result['paquete']);cls.digest=cls.result['sha256_manifiesto']

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.case=tempfile.TemporaryDirectory(dir=str(self.base));self.addCleanup(self.case.cleanup);self.root=Path(self.case.name)

    def copied(self):
        path=self.root/'paquete';shutil.copytree(str(self.package),str(path));return path

    def restored(self):
        path=self.root/'Otra persona ñ espacio';restore_migration(self.package,path,self.digest);return path

    def test_export_unchanged_all_tables_and_source_comparison(self):
        self.assertEqual(sha256(self.ws.database),self.raw)
        self.assertEqual(read_summary(self.ws.database),self.before)
        self.assertEqual(compare_source(self.package,self.ws,self.digest)['diferencias'],[])
        m=verify_package(self.package,self.digest)
        self.assertNotEqual(m['base_portable'],self.before)  # ruta absoluta fue normalizada SOLO en copia
        self.assertTrue(m['solo_laboratorio'])
        self.assertFalse(any('.venv' in n or '__pycache__' in n for n in m['archivos']))

    def test_restore_other_root_preserves_history_and_blocks_store(self):
        root=self.restored();report=verify_destination(root)
        self.assertEqual(report['diferencias'],[])
        self.assertEqual(report['conclusion'],'MIGRACION VERIFICADA')
        with self.assertRaises(ValueError):Store(root/'workspace/datos/digitalizacion.sqlite3')
        for table in ('auditoria','revisiones_tiff','versiones_archivo','operaciones_tiff','expedientes','trabajos'):
            self.assertEqual(read_summary(root/'workspace/datos/digitalizacion.sqlite3')['tablas'][table],self.before['tablas'][table])

    def test_manifest_external_hash_required_to_detect_replaced_anchor(self):
        path=self.copied();manifest=path/MANIFEST
        data=json.loads(manifest.read_text());data['fecha']='alterada';manifest.write_text(json.dumps(data))
        (path/'migracion-manifest.sha256').write_text(sha256(manifest)+'  '+MANIFEST)
        with self.assertRaisesRegex(ValueError,'SHA-256'):verify_package(path,self.digest)

    def test_corrupt_file_rejected_before_target_created(self):
        path=self.copied();next((path/'respaldo/datos').rglob('*.tif')).write_bytes(b'otro')
        with self.assertRaises(ValueError):restore_migration(path,self.root/'destino',self.digest)
        self.assertFalse((self.root/'destino').exists())

    def test_unmanifested_file_rejected(self):
        path=self.copied();(path/'basura.txt').write_text('no')
        with self.assertRaises(ValueError):verify_package(path,self.digest)

    def test_pending_export_cannot_import(self):
        path=self.copied();(path/'INCOMPLETO.txt').write_text('interrupción')
        with self.assertRaisesRegex(ValueError,'incompleto'):verify_package(path,self.digest)

    def test_same_count_audit_mutation_blocks_destination(self):
        root=self.restored()
        with sqlite3.connect(str(root/'workspace/datos/digitalizacion.sqlite3')) as db:
            db.execute("UPDATE auditoria SET motivo='alteración' WHERE id=(SELECT MIN(id) FROM auditoria)")
        self.assertTrue(verify_destination(root)['diferencias'])
        with self.assertRaises(ValueError):activate(root,True)

    def test_missing_revision_blocks_destination(self):
        root=self.restored();ws=Workspace(root/'workspace')
        with sqlite3.connect(str(ws.database)) as db:relative=db.execute('SELECT ruta FROM revisiones_tiff LIMIT 1').fetchone()[0]
        ws.path(relative).unlink();self.assertTrue(verify_destination(root)['diferencias'])

    def test_repeat_restore_never_overwrites(self):
        root=self.restored();marker=root/'personal.txt';marker.write_text('preservar')
        with self.assertRaises(FileExistsError):restore_migration(self.package,root,self.digest)
        self.assertEqual(marker.read_text(),'preservar')

    def test_publication_never_replaces_even_empty_existing_directory(self):
        source=self.root/'en curso';source.mkdir();(source/'uno.txt').write_text('prueba')
        target=self.root/'existente';target.mkdir()
        with self.assertRaises(FileExistsError):publish_folder(source,target)
        self.assertTrue((source/'uno.txt').exists());self.assertEqual(list(target.iterdir()),[])

    def test_interrupted_publication_is_marked(self):
        source=self.root/'en curso';source.mkdir();(source/'uno.txt').write_text('prueba')
        with patch('app.transfer.os.rename',side_effect=OSError('interrupción')):
            with self.assertRaises(OSError):publish_folder(source,self.root/'parcial')
        self.assertTrue((self.root/'parcial/INCOMPLETO.txt').exists())

    def test_failed_destination_check_keeps_incomplete_and_never_publishes(self):
        with patch('app.transfer.verify_destination',return_value={'diferencias':['error forzado']}):
            with self.assertRaises(ValueError):restore_migration(self.package,self.root/'destino',self.digest)
        self.assertFalse((self.root/'destino').exists())
        self.assertTrue(any(p.exists() for p in self.root.glob('.*restauracion-*/INCOMPLETO.txt')))

    def test_activation_requires_rehearsal_and_confirmation(self):
        root=self.restored()
        with self.assertRaisesRegex(ValueError,'Confirma'):activate(root)
        with self.assertRaisesRegex(ValueError,'ensayo'):activate(root,True)
        self.assertTrue((root/'workspace/.restauracion_incompleta').exists())

    def test_activation_rechecks_changes_after_successful_rehearsal(self):
        root=self.restored();info={'python':'ficticio'}
        with patch('app.migration_acceptance.target_runtime',return_value=info),patch('app.migration_acceptance.subprocess.run') as run:
            run.return_value.returncode=0;rehearse(root)
            with sqlite3.connect(str(root/'workspace/datos/digitalizacion.sqlite3')) as db:db.execute("INSERT INTO folios(numero) VALUES('NUEVO')")
            with self.assertRaisesRegex(ValueError,'NO VERIFICADA'):activate(root,True)
        self.assertTrue((root/'workspace/.restauracion_incompleta').exists())

    def test_lab_acceptance_can_never_be_labeled_production(self):
        root=self.restored()
        with patch('app.migration_acceptance.target_runtime',return_value={'python':'ficticio'}),patch('app.migration_acceptance.subprocess.run') as run:
            run.return_value.returncode=0;rehearse(root);result=activate(root,True)
        self.assertEqual(result['estado'],'Laboratorio habilitado')
        self.assertFalse((root/'workspace/.restauracion_incompleta').exists())

    def test_failed_rehearsal_remains_blocked(self):
        root=self.restored()
        with patch('app.migration_acceptance.target_runtime',return_value={}),patch('app.migration_acceptance.subprocess.run') as run:
            run.return_value.returncode=1
            with self.assertRaisesRegex(ValueError,'ensayo falló'):rehearse(root)
        with self.assertRaises(ValueError):activate(root,True)

    def test_verification_of_missing_installation_creates_nothing(self):
        root=self.root/'inexistente'
        with self.assertRaises(ValueError):verify_destination(root)
        self.assertFalse(root.exists())

    def test_lab_cannot_be_enabled_after_moving_rehearsed_installation(self):
        root=self.restored()
        with patch('app.migration_acceptance.target_runtime',return_value={}),patch('app.migration_acceptance.subprocess.run') as run:
            run.return_value.returncode=0;rehearse(root)
            moved=self.root/'reubicada';root.rename(moved)
            with self.assertRaisesRegex(ValueError,'ubicación'):activate(moved,True)

    def test_source_commit_after_export_is_not_equivalent(self):
        ws=Workspace(self.root/'otra copia de origen')
        shutil.copytree(str(self.ws.root),str(ws.root))
        with sqlite3.connect(str(ws.database)) as db:
            db.execute('PRAGMA journal_mode=WAL');db.execute("INSERT INTO folios(numero) VALUES('POSTERIOR')");db.commit()
            self.assertTrue(compare_source(self.package,ws,self.digest)['diferencias'])

    def test_launch_equivalent_fallback_preserves_post_acceptance_captures(self):
        root=self.restored()
        info={'python':'3.8.10','ejecutable':'anterior'}
        with patch('app.migration_acceptance.target_runtime',return_value=info),patch('app.migration_acceptance.subprocess.run') as run:
            run.return_value.returncode=0;rehearse(root);activate(root,True)
        database=root/'workspace/datos/digitalizacion.sqlite3'
        with sqlite3.connect(str(database)) as db:db.execute("INSERT INTO folios(numero) VALUES('TRABAJO POSTERIOR')")
        before=sha256(database);chosen=self.root/'equivalente.exe';newinfo=dict(info,ejecutable=str(chosen))
        with patch('app.migration_acceptance.resolve',return_value=(chosen,newinfo,[{'motivo':'0 bytes'}])),patch('app.migration_acceptance.target_runtime',return_value=newinfo),patch('app.migration_acceptance.subprocess.call',return_value=0) as call:
            self.assertEqual(launch(root),0);self.assertEqual(call.call_args[0][0][0],str(chosen))
        self.assertEqual(sha256(database),before);self.assertTrue(list((root/'evidencia').glob('runtime-*.json')))

    @unittest.skipUnless(os.name=='nt','Requiere Windows: otra letra de unidad mediante SUBST')
    def test_other_drive_windows(self):
        import subprocess
        subst=str(Path(os.environ['SystemRoot'])/'System32/subst.exe')
        drive=next((letter+':' for letter in 'ZYXWVUTSRQP' if not Path(letter+':\\').exists()),None)
        if not drive:self.skipTest('No hay letra libre para SUBST')
        subprocess.run([subst,drive,str(self.root)],check=True)
        try:
            destination=Path(drive+'\\Persona nueva á');restore_migration(self.package,destination,self.digest)
            self.assertFalse(verify_destination(destination)['diferencias'])
        finally:subprocess.run([subst,drive,'/D'],check=True)
