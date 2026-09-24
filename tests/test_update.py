import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.backup import sha256
from app.core import Store
from actualizar import inspect_release, apply_update


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.source=self.root/'paquete';self.target=self.root/'oficina'
        self.source.mkdir();self.target.mkdir()
        self.files=['main.py','app/core.py','app/schema.sql','app/workspace.py','app/migrations.py']
        for name in self.files:
            p=self.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('nuevo '+name)
            p=self.target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('viejo '+name)
        self.manifest={'format':1,'version':'0.4','files':{n:sha256(self.source/n) for n in self.files}}
        self.write_manifest()
        s=Store(workspace=self.target);s.save_folio('CONSERVAR','');s.db.close()
        (self.target/'python_ruta.txt').write_text('ruta local')
        (self.target/'datos'/'conservar.txt').write_text('datos locales')
    def tearDown(self):self.temp.cleanup()
    def write_manifest(self):(self.source/'release-manifest.json').write_text(json.dumps(self.manifest))
    def test_readonly_check_then_update_preserves_operational_bytes(self):
        database=self.target/'datos'/'digitalizacion.sqlite3';before=sha256(database)
        inspect_release(self.source,self.target)
        self.assertEqual((self.target/'main.py').read_text(),'viejo main.py')
        recovery=apply_update(self.source,self.target)
        self.assertEqual(sha256(database),before)
        self.assertEqual((self.target/'datos'/'conservar.txt').read_text(),'datos locales')
        self.assertEqual((self.target/'python_ruta.txt').read_text(),'ruta local')
        self.assertEqual((self.target/'main.py').read_text(),'nuevo main.py')
        self.assertTrue((recovery/'datos_antes'/'manifest.json').is_file())
    def test_data_in_package_rejected_before_writes(self):
        self.manifest['files']['datos/digitalizacion.sqlite3']=sha256(self.target/'datos'/'digitalizacion.sqlite3')
        self.write_manifest()
        with self.assertRaises(ValueError):apply_update(self.source,self.target)
        self.assertEqual((self.target/'main.py').read_text(),'viejo main.py')
    def test_partial_code_failure_rolls_back(self):
        import os
        original=os.replace;count=[0]
        def fail(src,dst):
            if 'codigo_nuevo' in str(src):
                count[0]+=1
                if count[0]==3:raise OSError('disco lleno simulado')
            return original(src,dst)
        with patch('actualizar.os.replace',side_effect=fail):
            with self.assertRaises(OSError):apply_update(self.source,self.target)
        for name in self.files:self.assertEqual((self.target/name).read_text(),'viejo '+name)
    def test_modified_package_refused(self):
        (self.source/'main.py').write_text('alterado')
        with self.assertRaises(ValueError):apply_update(self.source,self.target)

    def test_abrupt_update_leaves_marker_and_blocks_open(self):
        import os
        original=os.replace;count=[0]
        def stop(src,dst):
            if 'codigo_nuevo' in str(src):
                count[0]+=1
                if count[0]==3:raise KeyboardInterrupt('corte simulado')
            return original(src,dst)
        with patch('actualizar.os.replace',side_effect=stop):
            with self.assertRaises(KeyboardInterrupt):apply_update(self.source,self.target)
        self.assertTrue((self.target/'.actualizacion_pendiente.json').is_file())
        with self.assertRaises(ValueError):Store(workspace=self.target)
        with self.assertRaises(ValueError):inspect_release(self.source,self.target)
