import json
from pathlib import Path
import shutil
import tempfile
import unittest
import uuid
from unittest.mock import patch

from app.backup import sha256
from app.demo import create_demo
from app.update_recovery import data_fingerprint
from app.workspace import Workspace
from webapp.transition import prepare, activate


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.gettempdir()).parent / ('transicion-' + uuid.uuid4().hex[:8])
        self.root.mkdir()
        self.target = self.root / 'oficina-ficticia'
        create_demo(self.target)
        (self.target / 'main.py').write_text('# Aplicacion anterior ficticia\n', encoding='utf-8')
        (self.target / 'INICIAR.bat').write_text('@echo acceso anterior ficticio\n', encoding='utf-8')
        self.source = self.root / 'paquete'
        self.source.mkdir()
        code = Path(__file__).resolve().parent.parent
        files = ['main.py', 'app/core.py', 'app/schema.sql', 'app/workspace.py', 'app/migrations.py', 'iniciar_web.py']
        for name in files:
            out = self.source / name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(code / name), str(out))
        (self.source / 'INICIAR.bat').write_text('@echo acceso web ficticio\n', encoding='utf-8')
        files.append('INICIAR.bat')
        (self.source / 'release-manifest.json').write_text(json.dumps({
            'format': 1, 'version': '0.8.0rc1', 'files': {n: sha256(self.source / n) for n in files}}), encoding='utf-8')
        self.recovery = self.root / 'resguardo-privado'

    def test_prepare_then_activate_preserves_data_and_gates_startup(self):
        before = data_fingerprint(Workspace(self.target))
        plan = prepare(self.source, self.target, self.recovery)
        self.assertTrue(plan['copy_validation']['unchanged'])
        self.assertGreater(plan['copy_validation']['pages_decoded'], 0)
        self.assertEqual(data_fingerprint(Workspace(self.target)), before)
        self.assertIn('anterior', (self.target / 'INICIAR.bat').read_text())
        result = activate(self.recovery)
        self.assertEqual(data_fingerprint(Workspace(self.target)), before)
        self.assertIn('Activada', result['state'])
        previous = Path(result['updater_recovery']) / 'codigo_antes' / 'INICIAR.bat'
        self.assertIn('anterior', previous.read_text())
        from iniciar_web import checked_workspace
        with patch('iniciar_web.CODE', self.target):
            self.assertEqual(checked_workspace(self.target, operational=True), self.target)
            (self.target / 'INICIAR.bat').write_text('Cambio no validado', encoding='utf-8')
            with self.assertRaises(ValueError): checked_workspace(self.target, operational=True)
        with self.assertRaises(ValueError): activate(self.recovery)

    def test_capture_after_copy_blocks_activation_and_private_paths_are_excluded(self):
        prepare(self.source, self.target, self.recovery)
        from app.core import Store
        store = Store(workspace=self.target)
        try: store.save_folio('CAPTURA-FICTICIA-POSTERIOR', '')
        finally: store.db.close()
        with self.assertRaises(ValueError): activate(self.recovery)
        self.assertIn('anterior', (self.target / 'INICIAR.bat').read_text())
        self.assertFalse((self.target / '.web').exists())
        from app.release import allowed
        for path in ('.web/config.json', 'webapp/static/datos.sqlite3', 'webapp/templates/.env', 'webapp/static/vendor/credenciales.json'):
            self.assertFalse(allowed(path))
        with self.assertRaises(ValueError): prepare(self.source, self.target, self.target / 'resguardo')

    def test_actual_package_contains_only_allowed_code_and_guides(self):
        from tools.crear_paquete_web import build
        from app.release import allowed
        out = self.root / 'paquete-completo'
        result = build(out)
        from app import VERSION
        self.assertEqual(result['version'], VERSION)
        self.assertIn('webapp/migrations/0001_deskpreferences.py', result['files'])
        self.assertIn('webapp/static/desk.js', result['files'])
        for name, expected in result['files'].items():
            self.assertTrue(allowed(name))
            self.assertEqual(sha256(out / name), expected)
        self.assertIn('webapp/static/vendor/htmx.min.js', result['files'])
        self.assertIn('webapp/transition.py', result['files'])
        self.assertIn('--operacion', (out / 'INICIAR.bat').read_text())
        self.assertFalse((out / '.web').exists())
        with self.assertRaises(FileExistsError): build(out)

    def test_old_schema_is_rejected_before_any_migration(self):
        import sqlite3
        from webapp.transition import validate_copy
        ws = Workspace(self.target)
        with sqlite3.connect(ws.database) as db:
            db.execute("UPDATE meta SET value='3' WHERE key='coding_schema_version'")
            db.execute('DROP TABLE procedencia_paginas')
        before = data_fingerprint(ws)
        with self.assertRaisesRegex(ValueError, 'migración específica'):
            validate_copy(self.target)
        self.assertEqual(data_fingerprint(ws), before)
