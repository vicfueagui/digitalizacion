"""Barreras del asistente; el motor de respaldo/retorno conserva su suite propia."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from app import VERSION
from app.backup import sha256
from app.core import Store
from asistente_actualizacion import UpdateSession, validate_profile


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root/'paquete nuevo'
        self.target = self.root/'proyecto diario'
        self.source.mkdir(); self.target.mkdir()
        self.files = {}
        for name in ('main.py','app/core.py','app/schema.sql','app/workspace.py','app/migrations.py'):
            path = self.source/name; path.parent.mkdir(exist_ok=True)
            path.write_text('# código de prueba\n',encoding='utf-8'); self.files[name] = sha256(path)
        self.manifest = self.source/'release-manifest.json'
        self.manifest.write_text(json.dumps({'format':1,'version':VERSION,'files':self.files}),encoding='utf-8')
        (self.target/'main.py').write_text('# código anterior\n',encoding='utf-8')
        store = Store(workspace=self.target); store.save_folio('FICTICIO/2026',''); store.db.close()
        self.database = self.target/'datos/digitalizacion.sqlite3'
        self.before = sha256(self.database)
        self.session = UpdateSession(self.source,windows=False)
        self.session.choose(self.target)
        self.profile = dict(python='3.8.10',bits=64,implementation='CPython',python_bits=64,implementacion='CPython',pillow='9.5.0',libtiff=True,tk=8.6,tcl='8.6.12')

    def inspect(self):
        result = subprocess.CompletedProcess([],0,json.dumps(self.profile),'')
        with patch('asistente_actualizacion.subprocess.run',return_value=result):self.session.inspect()

    def fake_rehearsal(self, correct=True, version=VERSION, profile=True, code=0):
        def run(command,**kwargs):
            target = Path(command[command.index('--destino')+1]); target.mkdir(parents=True)
            (target/'resultado.json').write_text(json.dumps({'comprobaciones_automaticas_correctas':correct,
                'entorno':{'version_aplicacion':version},'perfil_windows7_coincide':profile}),encoding='utf-8')
            self.assertNotIn(str(self.target),command)
            self.assertIn('--ventanas',command)
            return subprocess.CompletedProcess(command,code,'resultado sintético')
        return run

    def test_inspection_is_read_only_and_requires_independent_package(self):
        self.inspect(); self.assertEqual(sha256(self.database),self.before)
        self.assertFalse((self.target/'.actualizacion_pendiente.json').exists())
        self.session.choose(self.source)
        with self.assertRaises(ValueError):self.session.inspect()
        self.assertIsNone(self.session.signature)

    def test_cannot_apply_without_check_rehearsal_and_confirmation(self):
        with patch('asistente_actualizacion.subprocess.run') as process:
            with self.assertRaises(ValueError):self.session.apply(True)
            with self.assertRaises(ValueError):self.session.rehearse(self.root/'pruebas')
            process.assert_not_called()
        self.inspect()
        with self.assertRaises(ValueError):self.session.apply(True)
        self.session.rehearsal = self.root/'ensayo'
        with self.assertRaises(ValueError):self.session.apply(False)

    def test_change_project_invalidates_previous_evidence(self):
        self.inspect(); self.session.rehearsal = self.root/'ensayo'
        self.session.choose(self.target)
        self.assertIsNone(self.session.signature); self.assertIsNone(self.session.rehearsal)
        with self.assertRaises(ValueError):self.session.apply(True)

    def test_rejects_trial_inside_live_project_or_package(self):
        self.inspect()
        with patch('asistente_actualizacion.subprocess.run') as process:
            for parent in (self.target,self.target/'datos',self.source,self.source/'docs'):
                with self.assertRaises(ValueError):self.session.rehearse(parent)
            process.assert_not_called()
        self.assertEqual(sha256(self.database),self.before)

    def test_changed_manifest_requires_new_check_and_test(self):
        self.inspect(); self.session.rehearsal = self.root/'ensayo'
        self.manifest.write_text(self.manifest.read_text(encoding='utf-8')+'\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'paquete cambió'):self.session.apply(True)

    def test_tampered_package_file_blocked_even_if_manifest_unchanged(self):
        self.inspect(); self.session.rehearsal = self.root/'ensayo'
        (self.source/'main.py').write_text('# alterado',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'alterado'):self.session.apply(True)
        self.assertEqual(sha256(self.database),self.before)

    def test_rehearsal_success_leaves_live_database_unchanged(self):
        self.inspect()
        with patch('asistente_actualizacion.subprocess.run',side_effect=self.fake_rehearsal()):
            first = self.session.rehearse(self.root/'pruebas')
            second = self.session.rehearse(self.root/'pruebas')
        self.assertNotEqual(first,second); self.assertTrue(first.is_dir())
        self.assertEqual(self.session.rehearsal,second); self.assertEqual(sha256(self.database),self.before)

    def test_failed_or_wrong_version_report_blocks_apply(self):
        self.inspect()
        for options in ({'correct':False},{'version':'anterior'},{'code':1}):
            with patch('asistente_actualizacion.subprocess.run',side_effect=self.fake_rehearsal(**options)):
                with self.assertRaises(ValueError):self.session.rehearse(self.root/'pruebas')
            self.assertIsNone(self.session.rehearsal)
            with self.assertRaises(ValueError):self.session.apply(True)

    def test_windows_must_pass_actual_windows7_profile(self):
        self.inspect(); self.session.windows = True
        with patch('asistente_actualizacion.subprocess.run',side_effect=self.fake_rehearsal(profile=False)):
            with self.assertRaisesRegex(ValueError,'Windows 7 SP1'):self.session.rehearse(self.root/'pruebas')
        self.assertIsNone(self.session.rehearsal)

    def test_missing_target_windows_environment_stops_without_write(self):
        self.session.windows = True
        # Ausencia real de TODOS los candidatos, independiente del Python del test.
        with patch('app.runtime.candidates',return_value=[self.root/'ausente.exe']):
            with self.assertRaisesRegex(ValueError,'No se encontró'):self.session.inspect()
        self.assertEqual(sha256(self.database),self.before)

    def test_unsupported_profiles_rejected(self):
        validate_profile(self.profile,True)
        for values in ({'python':'3.8.9'},{'python':'3.11.4'},{'bits':32},{'pillow':'12.3.0'},
                       {'implementation':'PyPy'},{'libtiff':False},{'tk':None}):
            with self.assertRaises(ValueError):validate_profile(dict(self.profile,**values),True)

    def test_apply_calls_protected_cli_with_exact_paths_and_consumes_trial(self):
        self.inspect(); trial = self.root/'ensayo'; trial.mkdir(); self.session.rehearsal = trial
        def run(command,**kwargs):
            self.assertEqual(command,[str(self.session.interpreter),str(self.source/'actualizar.py'),
                                      '--destino',str(self.target),'--aplicar'])
            self.assertNotIn('shell',kwargs)
            kwargs['stdout'].write('Registro de prueba\n')
            return subprocess.CompletedProcess(command,0)
        with patch('asistente_actualizacion.subprocess.run',side_effect=run):log = self.session.apply(True)
        self.assertIn('Registro de prueba',log.read_text(encoding='utf-8'))
        self.assertIsNone(self.session.rehearsal)
        with self.assertRaises(ValueError):self.session.apply(True)

    def test_failed_apply_preserves_log_and_requires_review(self):
        self.inspect(); trial = self.root/'ensayo'; trial.mkdir(); self.session.rehearsal = trial
        with patch('asistente_actualizacion.subprocess.run',return_value=subprocess.CompletedProcess([],1)):
            with self.assertRaisesRegex(ValueError,'No abras el proyecto'):self.session.apply(True)
        self.assertTrue((trial/'actualizacion.log').is_file()); self.assertIsNone(self.session.rehearsal)


if __name__ == '__main__': unittest.main()
