"""Migración 7→8 con el migrador original 0.6.2, solo datos sintéticos."""
import importlib.util
import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from app.core import Store
from app.integrations import Integrations


class IntegrationMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'datos/digitalizacion.sqlite3'
        spec=importlib.util.spec_from_file_location('app.migrations_fixture',(Path(__file__).parent/'fixtures/migrations_v062.py'))
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        with patch('app.migrations.migrate',old.migrate):s=Store(workspace=self.root)
        with s.db:
            s.db.execute("INSERT INTO personas VALUES('AAAA900101HYNBBB01','Persona inventada')")
            s.db.execute("INSERT INTO folios(id,numero) VALUES(5,'MIGRACION-FICTICIA')")
            s.db.execute("INSERT INTO trabajos(id,folio_id,curp,legajo,fisicos,estado_desde) VALUES(17,5,'AAAA900101HYNBBB01',1,7,'2020-01-01')")
            s.db.execute("INSERT INTO conteos(id,trabajo_id,cantidad,creado) VALUES(41,17,7,'2020-01-01')")
            s.db.execute("INSERT INTO historial(id,trabajo_id,estado,inicio,motivo,operador) VALUES(51,17,'Recibido','2020-01-01','Fixture','Prueba')")
            from app.operational_migration import link_work
            link_work(s,17)
        self.before={t:s.rows('SELECT * FROM '+t) for t in ('trabajos','conteos','historial','prestamo_items','expedientes')};s.db.close()

    def tearDown(self):self.temp.cleanup()

    def test_ids_history_unknown_dates_preserved_reopening_idempotent(self):
        s=Store(workspace=self.root)
        try:
            for table,rows in self.before.items():
                current=s.rows('SELECT * FROM '+table)
                self.assertEqual(rows,[{k:r[k] for k in rows[0]} for r in current])
            integration=Integrations(s).current(17);self.assertIsNone(integration['recibido'])
            self.assertEqual(integration['fisicos'],7);self.assertIn('Migración técnica',integration['origen'])
            self.assertEqual(s.one('conteos',41)['integracion_id'],integration['id'])
            self.assertEqual(s.rows('PRAGMA foreign_key_check'),[])
        finally:s.db.close()
        s=Store(workspace=self.root)
        try:self.assertEqual(len(Integrations(s).list(17)),1)
        finally:s.db.close()

    def test_interrupted_migration_retains_schema_and_ids(self):
        from app.integrations import migrate
        def fail(store):migrate(store);raise OSError('Fallo sintético después de asociar filas')
        with patch('app.integrations.migrate',fail):
            with self.assertRaises(OSError):Store(workspace=self.root)
        db=sqlite3.connect(str(self.path))
        try:
            self.assertEqual(db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],'7')
            self.assertEqual(db.execute('SELECT id,cantidad FROM conteos').fetchall(),[(41,7)])
            self.assertFalse(db.execute("SELECT name FROM sqlite_master WHERE name='integraciones'").fetchall())
            self.assertNotIn('integracion_actual_id',[r[1] for r in db.execute('PRAGMA table_info(trabajos)')])
        finally:db.close()
        self.assertTrue(list((self.root/'respaldos').glob('*.sqlite3')))
