import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from app.core import Store,ROOT
from app.migration_sql import CODING_1,CODING_2
from app.migrations import CORE_VERSION
from app.backup import sha256,create_backup,verify_backup
from app.coding import CodingService


class ModelMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'datos/digitalizacion.sqlite3';self.path.parent.mkdir()
        db=sqlite3.connect(str(self.path));db.executescript((ROOT/'app/schema.sql').read_text());db.executescript(CODING_1);db.executescript(CODING_2)
        db.execute('ALTER TABLE archivos_tiff ADD COLUMN activo INTEGER NOT NULL DEFAULT 1');db.execute("INSERT INTO meta VALUES('coding_schema_version','2')")
        db.execute("INSERT INTO personas VALUES('AAAA900101HYNBBB01','Persona inventada')")
        for ident in (1,2):db.execute('INSERT INTO folios(id,numero) VALUES(?,?)',(ident,'FICTICIO/'+str(ident)))
        for ident,folio,legajo in ((11,1,1),(12,2,1),(13,2,2)):
            db.execute("INSERT INTO trabajos(id,folio_id,curp,legajo,digitalizador,estado_desde,fisicos) VALUES(?,?,'AAAA900101HYNBBB01',?,'Operador histórico ficticio','2020-01-01',7)",(ident,folio,legajo))
        db.execute("INSERT INTO conteos(id,trabajo_id,cantidad,creado) VALUES(41,11,7,'2020-01-01')")
        paths=[]
        for folder,color in (('originales','white'),('revisiones','black'),('entrada','gray')):
            p=self.root/('datos/tiff/trabajo_11/'+folder+'/DP-01.tif');p.parent.mkdir(parents=True)
            im=Image.new('L',(20,30),color);im.save(p,compression='tiff_deflate');im.close();paths.append(p)
        original,revision,current=paths
        rel=lambda p:p.relative_to(self.root).as_posix().replace('/','\\')
        db.execute('INSERT INTO archivos_tiff(id,trabajo_id,ruta,original,hash_original,hash_actual,paginas,codigo,fecha_origen,creacion_origen,importado) VALUES(21,11,?,?,?,?,1,?,0,0,?)',
            (rel(current),rel(original),sha256(original),sha256(current),'DP-01','2020-01-01'))
        db.execute('INSERT INTO revisiones_tiff(id,archivo_id,ruta,fecha,operacion,hash) VALUES(31,21,?,?,?,?)',(rel(revision),'2020-01-01','Edición histórica',sha256(revision)))
        db.execute("INSERT INTO catalogos(tipo,codigo,carpeta,titulo) VALUES('documento','DP-01','PERSONALES','Prueba')")
        db.commit();db.close();self.hashes={p:sha256(p) for p in paths}
    def tearDown(self):self.temp.cleanup()
    def test_old_ids_rows_and_originals_are_preserved(self):
        s=Store(workspace=self.root)
        try:
            self.assertEqual([r['id'] for r in s.rows('SELECT id FROM trabajos ORDER BY id')],[11,12,13])
            self.assertEqual(len(s.rows('SELECT * FROM expedientes')),2)
            self.assertEqual(len(s.rows('SELECT * FROM trabajos WHERE conciliacion_pendiente=1')),2)
            self.assertEqual(s.one('conteos',41)['cantidad'],7)
            self.assertEqual(len(s.rows('SELECT * FROM versiones_archivo')),3)
            self.assertEqual(s.rows('SELECT * FROM archivos_tiff')[0]['id'],21)
            self.assertIsNone(s.rows('SELECT * FROM archivos_tiff')[0]['nombre_origen'])
            self.assertTrue(all(r['inicio'] is None for r in s.rows('SELECT * FROM asignaciones')))
            self.assertTrue(all(r['validacion']=='Pendiente' for r in s.rows('SELECT * FROM prestamo_items')))
            self.assertFalse(s.db.execute('PRAGMA foreign_key_check').fetchall());self.assertEqual(s.db.execute('PRAGMA foreign_keys').fetchone()[0],1)
            verify_backup(create_backup(s,self.root/'respaldos/entero'))
        finally:s.db.close()
        self.assertEqual(self.hashes,{p:sha256(p) for p in self.hashes})
    def test_repeated_migration_keeps_uuids_and_version_numbers(self):
        s=Store(workspace=self.root);before=s.rows('SELECT * FROM versiones_archivo');s.db.close()
        s=Store(workspace=self.root)
        try:
            self.assertEqual(before,s.rows('SELECT * FROM versiones_archivo'))
            self.assertEqual(s.rows("SELECT value FROM meta WHERE key='schema_version'")[0]['value'],str(CORE_VERSION))
            self.assertEqual(len(list(s.workspace.backups.glob('*.sqlite3'))),1)
        finally:s.db.close()
    def test_failure_after_table_rebuild_rolls_back_old_data_and_schema(self):
        from app import assets
        original=assets.migrate
        def fail(store):original(store);raise OSError('Corte simulado en migración de identidad')
        with patch.object(assets,'migrate',side_effect=fail):
            with self.assertRaises(OSError):Store(workspace=self.root)
        db=sqlite3.connect(str(self.path))
        self.assertEqual(db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],'1')
        self.assertEqual(db.execute('SELECT id FROM archivos_tiff').fetchone()[0],21)
        self.assertFalse(db.execute("SELECT name FROM sqlite_master WHERE name='expedientes'").fetchall());db.close()
        self.assertEqual(self.hashes,{p:sha256(p) for p in self.hashes})
        s=Store(workspace=self.root);s.db.close()
    def test_unrecognized_extra_column_stops_without_losing_it(self):
        db=sqlite3.connect(str(self.path));db.execute('ALTER TABLE archivos_tiff ADD COLUMN extra_local TEXT');db.execute("UPDATE archivos_tiff SET extra_local='Conservar'");db.commit();db.close()
        with self.assertRaisesRegex(ValueError,'desconocida'):Store(workspace=self.root)
        db=sqlite3.connect(str(self.path));self.assertEqual(db.execute('SELECT extra_local FROM archivos_tiff').fetchone()[0],'Conservar');db.close()
    def test_first_edit_after_migration_preserves_all_version_hashes(self):
        s=Store(workspace=self.root)
        try:
            coder=CodingService(s);before=coder.file(21);coder.save_edit(21,0,[('rotate',90)]);coder.assign(21,'DP-01')
            self.assertEqual(coder.file(21)['documento_id'],before['documento_id'])
            for v in s.rows('SELECT * FROM versiones_archivo'):
                self.assertEqual(sha256(s.workspace.path(v['ruta'])),v['sha256'])
            verify_backup(create_backup(s,self.root/'respaldos/despues-editar'))
        finally:s.db.close()

    def test_directory_migration_preserves_historical_names_and_ids(self):
        s=Store(workspace=self.root)
        try:
            staff=s.rows('SELECT * FROM directorio WHERE tipo="persona"')
            self.assertEqual(len(staff),1);self.assertEqual(staff[0]['nombre'],'Operador histórico ficticio')
            self.assertTrue(all(r['digitalizador_id']==staff[0]['id'] for r in s.rows('SELECT * FROM trabajos')))
            self.assertTrue(all(r['persona_id']==staff[0]['id'] and r['inicio'] is None for r in s.rows('SELECT * FROM asignaciones')))
            self.assertEqual([r['id'] for r in s.rows('SELECT id FROM trabajos ORDER BY id')],[11,12,13])
        finally:s.db.close()
        self.assertEqual(self.hashes,{p:sha256(p) for p in self.hashes})

    def test_directory_seed_failure_rolls_back_migration(self):
        from app import directory
        original=directory.seed
        def fail(store):original(store);raise OSError('Fallo simulado al migrar directorio')
        with patch.object(directory,'seed',side_effect=fail):
            with self.assertRaises(OSError):Store(workspace=self.root)
        db=sqlite3.connect(str(self.path))
        self.assertEqual(db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0],'1')
        self.assertFalse(db.execute("SELECT name FROM sqlite_master WHERE name='directorio'").fetchall());db.close()
        self.assertEqual(self.hashes,{p:sha256(p) for p in self.hashes})
