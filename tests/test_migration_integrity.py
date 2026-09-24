import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.backup import backup_existing,create_backup,inventory_files,sha256,verify_backup
from app.core import Store
from app.demo import create_demo
from app.portability import active_relative,history_relative
from app.update_recovery import data_fingerprint,database_fingerprint
from app.workspace import Workspace


class HistoricalSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.ws=Workspace(create_demo(self.root/'origen con acentos á'))

    def test_locked_wal_and_shm_never_resolved_but_commits_are_fingerprinted(self):
        db=sqlite3.connect(str(self.ws.database));db.execute('PRAGMA journal_mode=WAL')
        self.addCleanup(db.close)
        initial=data_fingerprint(self.ws)
        db.execute("INSERT INTO folios(numero) VALUES('CONFIRMADO-EN-WAL')");db.commit()
        real=Path.resolve
        for suffix in ('-wal','-shm','-journal'):
            def locked(path,*args,**kwargs):
                if path.name=='digitalizacion.sqlite3'+suffix:raise PermissionError('WinError 32 simulado')
                return real(path,*args,**kwargs)
            with patch.object(Path,'resolve',locked):
                current=data_fingerprint(self.ws)
                out=backup_existing(self.ws,self.root/('respaldo'+suffix))
                verify_backup(out)
            self.assertNotEqual(initial['database'],current['database'])
            with sqlite3.connect(str(out/'datos/digitalizacion.sqlite3')) as copied:
                self.assertEqual(copied.execute("SELECT COUNT(*) FROM folios WHERE numero='CONFIRMADO-EN-WAL'").fetchone()[0],1)
        self.assertEqual(database_fingerprint(db),current['database'])

    def historical(self):
        db=sqlite3.connect(str(self.ws.database))
        ident,work,relative=db.execute('SELECT id,trabajo_id,ruta FROM archivos_tiff ORDER BY id LIMIT 1').fetchone()
        old=r'C:\Users\usuario-anterior\Archivo histórico'
        path=old+'\\'+relative.replace('/','\\')
        detail=json.dumps({'source':path,'target':path,'destino':path,'nota':'No reescribir historia libre'})
        op=db.execute("INSERT INTO operaciones_tiff(fecha,trabajo_id,archivo_id,tipo,estado,detalle) VALUES('2026-01-01',?,?,'organizar','Completada',?)",(work,ident,detail)).lastrowid
        db.commit();db.close()
        return op,old,detail,relative

    def test_absolute_history_is_not_an_active_reference(self):
        op,old,detail,relative=self.historical();before=sha256(self.ws.database)
        out=backup_existing(self.ws,self.root/'copia')
        self.assertEqual(sha256(self.ws.database),before)
        with sqlite3.connect(str(out/'datos/digitalizacion.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT detalle FROM operaciones_tiff WHERE id=?',(op,)).fetchone()[0],detail)
        verify_backup(out)

    def test_evidenced_history_normalized_only_in_snapshot(self):
        op,old,detail,relative=self.historical();before=sha256(self.ws.database)
        db=sqlite3.connect(self.ws.database.as_uri()+'?mode=ro',uri=True)
        from types import SimpleNamespace
        changes=[]
        try:out=create_backup(SimpleNamespace(db=db,path=self.ws.database,workspace=self.ws),self.root/'portable',historical_roots=[old],changes=changes)
        finally:db.close()
        self.assertEqual(sha256(self.ws.database),before)
        self.assertTrue(any(c['tabla']=='operaciones_tiff' and c['id']==op for c in changes))
        with sqlite3.connect(str(out/'datos/digitalizacion.sqlite3')) as db:
            value=json.loads(db.execute('SELECT detalle FROM operaciones_tiff WHERE id=?',(op,)).fetchone()[0])
            self.assertEqual(value['target'],relative)
            self.assertEqual(value['nota'],'No reescribir historia libre')
        verify_backup(out)

    def test_unproven_root_not_guessed_from_datos_substring(self):
        op,old,detail,relative=self.historical()
        db=sqlite3.connect(str(self.ws.database))
        from app.portability import evidenced_history_roots
        try:
            with self.assertRaisesRegex(ValueError,'inequívoca'):
                evidenced_history_roots(db,self.ws,[r'D:\otra carpeta'])
            self.assertEqual(history_relative(old+'\\datos\\ajeno.tif',[r'C:\Users\otro']),old+'\\datos\\ajeno.tif')
        finally:db.close()

    def test_active_external_and_traversal_still_rejected(self):
        for value in ('../escape.tif','datos/../escape.tif',r'D:\otro usuario\datos\uno.tif',str(self.root/'otro.tif')):
            with self.assertRaises(ValueError):active_relative(self.ws,value)
        with self.assertRaises(ValueError):history_relative(r'C:\historia\datos\..\escape.tif',[])

    @unittest.skipIf(os.name=='nt','Symlinks requieren privilegios; junctions tienen comprobación nativa separada')
    def test_active_internal_symlink_rejected(self):
        original=next((self.ws.root/'datos').rglob('*.tif'))
        link=self.ws.root/'datos/enlace.tif';link.symlink_to(original)
        with self.assertRaisesRegex(ValueError,'enlaces'):active_relative(self.ws,'datos/enlace.tif')


class InventoryRecoveryTests(unittest.TestCase):
    setUp=HistoricalSafetyTests.setUp

    def test_corrupt_sqlite_yields_report_without_repair(self):
        from app.integrity import diagnose,save_report
        self.ws.database.write_bytes(b'BASE DANADA FICTICIA')
        before=sha256(self.ws.database);report=diagnose(self.ws)
        self.assertFalse(report['correcto']);self.assertEqual(report['problemas'][0]['tipo'],'sqlite_o_estructura_invalida')
        save_report(report,self.root/'informe de error')
        self.assertEqual(sha256(self.ws.database),before)

    def test_diagnostic_reports_all_tables_without_altering_source(self):
        from app.integrity import diagnose
        before=data_fingerprint(self.ws)
        report=diagnose(self.ws,Path(__file__).resolve().parent.parent)
        self.assertTrue(report['correcto'],report['problemas'])
        self.assertEqual(report['tiff']['referencias'],report['tiff']['correctas'])
        for table in ('auditoria','operaciones_tiff','revisiones_tiff','versiones_archivo','entrega_items','expedientes','trabajos'):
            self.assertIn(table,report['resumen_base']['tablas'])
        self.assertEqual(report['resumen_base']['tablas']['trabajos']['filas'],3)
        self.assertEqual(data_fingerprint(self.ws),before)

    def test_missing_current_detected_even_when_original_is_intact(self):
        from app.integrity import diagnose
        with sqlite3.connect(str(self.ws.database)) as db:
            ident,path=db.execute('SELECT id,ruta FROM archivos_tiff ORDER BY id LIMIT 1').fetchone()
        self.ws.path(path).unlink()
        report=diagnose(self.ws)
        self.assertFalse(report['correcto'])
        self.assertIn({'tipo':'faltante','tabla':'archivos_tiff','id':ident,'campo':'ruta'},report['problemas'])
        self.assertFalse(any(i['campo']=='original' for i in report['problemas']))

    def test_altered_hash_original_and_revision_are_all_detected(self):
        from app.integrity import diagnose
        with sqlite3.connect(str(self.ws.database)) as db:
            current,original=db.execute('SELECT ruta,original FROM archivos_tiff ORDER BY id LIMIT 1').fetchone()
            revision=db.execute('SELECT ruta FROM revisiones_tiff LIMIT 1').fetchone()[0]
        # TIFF legible pero bytes distintos, sin sustituir hashes de SQLite.
        from PIL import Image
        for relative in (current,original,revision):
            path=self.ws.path(relative)
            with Image.new('L',(9,13),77) as image:image.save(str(path),format='TIFF')
        report=diagnose(self.ws)
        self.assertFalse(report['correcto'])
        fields={(i['tabla'],i['campo']) for i in report['problemas'] if i['tipo']=='hash_incorrecto'}
        self.assertTrue({('archivos_tiff','ruta'),('archivos_tiff','original'),('revisiones_tiff','ruta')}<=fields)

    def test_reconstructs_exact_hash_from_revision_rotation_without_repair(self):
        from app.tiff_recovery import reconstruct_candidate
        with sqlite3.connect(str(self.ws.database)) as db:
            row=db.execute('SELECT id,ruta,hash_actual,hash_original FROM archivos_tiff WHERE hash_actual!=hash_original LIMIT 1').fetchone()
            self.assertIsNotNone(row)
            ident,relative,expected,original=row
            revision=db.execute('SELECT id FROM revisiones_tiff WHERE archivo_id=? ORDER BY id DESC',(ident,)).fetchone()[0]
            operation=db.execute("SELECT id FROM operaciones_tiff WHERE archivo_id=? AND tipo='editar' ORDER BY id DESC",(ident,)).fetchone()[0]
        self.ws.path(relative).unlink();before=data_fingerprint(self.ws)
        result=reconstruct_candidate(self.ws,ident,revision,operation,self.root/'candidato externo')
        self.assertEqual(result['sha256'],expected);self.assertNotEqual(expected,original)
        self.assertEqual(sha256(self.root/'candidato externo/candidato.tif'),expected)
        self.assertFalse(self.ws.path(relative).exists())
        self.assertEqual(data_fingerprint(self.ws),before)

    def test_reconstruction_refuses_unrelated_operation_and_modified_revision(self):
        from app.tiff_recovery import reconstruct_candidate
        with sqlite3.connect(str(self.ws.database)) as db:
            revision,ident,path=db.execute('SELECT id,archivo_id,ruta FROM revisiones_tiff LIMIT 1').fetchone()
            operation=db.execute("SELECT id FROM operaciones_tiff WHERE archivo_id=? AND tipo='editar' LIMIT 1",(ident,)).fetchone()[0]
        with self.assertRaises(ValueError):reconstruct_candidate(self.ws,ident,revision,999999,self.root/'sin evidencia')
        self.ws.path(path).write_bytes(b'alterado')
        with self.assertRaisesRegex(ValueError,'revisión'):reconstruct_candidate(self.ws,ident,revision,operation,self.root/'sin evidencia')
        self.assertFalse((self.root/'sin evidencia').exists())

    def test_fingerprint_detects_equal_count_but_changed_audit(self):
        from app.integrity import read_summary
        before=read_summary(self.ws.database)
        with sqlite3.connect(str(self.ws.database)) as db:db.execute("UPDATE auditoria SET motivo='Cambio no autorizado' WHERE id=(SELECT MIN(id) FROM auditoria)")
        after=read_summary(self.ws.database)
        self.assertEqual(before['tablas']['auditoria']['filas'],after['tablas']['auditoria']['filas'])
        self.assertNotEqual(before['sha256_logico'],after['sha256_logico'])
