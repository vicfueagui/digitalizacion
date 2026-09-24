import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from app.runtime import probe,resolve,validate

GOOD=dict(python='3.8.10',implementacion='CPython',python_bits=64,tk='8.6',tcl='8.6.9',pillow='9.5.0',libtiff=True)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        self.venv=self.root/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python');self.venv.parent.mkdir(parents=True)
        self.explicit=self.root/'Python configurado á.exe';self.explicit.write_bytes(b'probe mocked')

    def process(self):return subprocess.CompletedProcess([],0,json.dumps(GOOD),'')

    def test_missing_venv_uses_explicit_executed_interpreter(self):
        with patch('app.runtime.subprocess.run',return_value=self.process()) as run:
            selected,info,rejected=resolve(self.root,self.explicit)
        self.assertEqual(selected,self.explicit);self.assertTrue(rejected);self.assertEqual(run.call_args[0][0][0],str(self.explicit))

    def test_zero_byte_venv_never_executed(self):
        self.venv.touch()
        with patch('app.runtime.subprocess.run',return_value=self.process()) as run:
            selected,info,rejected=resolve(self.root,self.explicit)
        self.assertEqual(selected,self.explicit);self.assertEqual(run.call_count,1);self.assertIn('0 bytes',rejected[0]['motivo'])

    def test_nonzero_broken_venv_falls_back_after_execution_failure(self):
        self.venv.write_bytes(b'broken')
        with patch('app.runtime.subprocess.run',side_effect=[OSError('Win32 inválido'),self.process()]):
            selected,info,rejected=resolve(self.root,self.explicit)
        self.assertEqual(selected,self.explicit);self.assertTrue(rejected)

    def test_valid_venv_preferred(self):
        self.venv.write_bytes(b'mocked')
        with patch('app.runtime.subprocess.run',return_value=self.process()):selected,info,rejected=resolve(self.root,self.explicit)
        self.assertEqual(selected,self.venv);self.assertFalse(rejected)

    def test_runtime_must_really_match_each_component(self):
        for field,bad in (('python','3.8.9'),('python_bits',32),('tk',None),('tk','9.0'),('tcl',None),('pillow','12.3.0'),('libtiff',False),('implementacion','PyPy')):
            with self.subTest(field=field,bad=bad),self.assertRaises(ValueError):validate(dict(GOOD,**{field:bad}))

    def test_config_file_path_spaces_unicode(self):
        (self.root/'python_ruta.txt').write_text(str(self.explicit),encoding='utf-8')
        with patch('app.runtime.subprocess.run',return_value=self.process()):selected,info,rejected=resolve(self.root)
        self.assertEqual(selected,self.explicit)

    def test_unparseable_probe_rejected(self):
        with patch('app.runtime.subprocess.run',return_value=subprocess.CompletedProcess([],0,'invalid','')):
            with self.assertRaisesRegex(ValueError,'diagnóstico'):probe(self.explicit)

    def test_installer_profile_does_not_require_pillow_but_does_require_tk(self):
        validate(dict(GOOD,pillow=None,libtiff=False),'instalar')
        with self.assertRaises(ValueError):validate(dict(GOOD,tk=None),'instalar')
