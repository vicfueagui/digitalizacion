"""Regresiones que deben ejecutarse en Windows: no se simulan como aprobadas en Mac."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from app.backup import backup_existing,verify_backup
from app.demo import create_demo
from app.update_recovery import data_fingerprint
from app.workspace import Workspace,CODE_ROOT


@unittest.skipUnless(os.name=='nt','Requiere Windows y bloqueo nativo de archivos')
class WindowsMigrationTests(unittest.TestCase):
    def locked_sidecar(self,suffix):
        import ctypes
        from ctypes import wintypes
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();ws=Workspace(create_demo(root/'datos sintéticos á'))
            db=sqlite3.connect(str(ws.database));db.execute('PRAGMA journal_mode=WAL')
            try:
                before=data_fingerprint(ws)
                db.execute("INSERT INTO folios(numero) VALUES('CONFIRMADO-WINDOWS')");db.commit()
                sidecar=Path(str(ws.database)+suffix)
                kernel=ctypes.WinDLL('kernel32',use_last_error=True)
                create=kernel.CreateFileW;create.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];create.restype=wintypes.HANDLE
                close=kernel.CloseHandle;close.argtypes=[wintypes.HANDLE];close.restype=wintypes.BOOL
                handle=create(str(sidecar),0x80000000,3,None,3,0,None)  # lectura/escritura compartida; no permite borrar/renombrar
                if handle==wintypes.HANDLE(-1).value:raise ctypes.WinError(ctypes.get_last_error())
                try:
                    with self.assertRaises(PermissionError):os.replace(str(sidecar),str(root/'no-renombrar'))
                    original_resolve=Path.resolve
                    def blocked(path,*args,**kwargs):
                        if str(path)==str(sidecar):raise PermissionError('[WinError 32] ruta auxiliar bloqueada')
                        return original_resolve(path,*args,**kwargs)
                    # Bloqueo real más detector del orden de exclusión. La API SQLite sigue leyendo WAL.
                    with patch.object(Path,'resolve',blocked):
                        after=data_fingerprint(ws);result=backup_existing(ws,root/'respaldo');verify_backup(result)
                    self.assertNotEqual(before['database'],after['database'])
                    with sqlite3.connect(str(result/'datos/digitalizacion.sqlite3')) as copied:
                        self.assertEqual(copied.execute("SELECT COUNT(*) FROM folios WHERE numero='CONFIRMADO-WINDOWS'").fetchone()[0],1)
                finally:close(handle)
            finally:db.close()

    def test_native_wal_locked_with_committed_data(self):self.locked_sidecar('-wal')
    def test_native_shm_locked_with_committed_data(self):self.locked_sidecar('-shm')

    def test_powershell_bootstrap_invalid_venv_spaces_unicode(self):
        from app.runtime import probe
        try:probe(Path(sys.executable),'legado')
        except ValueError:self.skipTest('El bootstrap conservador se ensaya con CPython 3.8.10/Pillow 9.5.0')
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'Usuario á con espacios';root.mkdir()
            for name in ('EJECUTAR.bat','ejecutar_python.ps1','python_runtime.py'):
                shutil.copy2(str(CODE_ROOT/name),str(root/name))
            (root/'app').mkdir()
            for name in ('__init__.py','runtime.py'):shutil.copy2(str(CODE_ROOT/'app'/name),str(root/'app'/name))
            (root/'.venv/Scripts').mkdir(parents=True);(root/'.venv/Scripts/python.exe').touch()
            (root/'python_ruta.txt').write_text(sys.executable,encoding='utf-8')
            # El despacho centinela comprueba argv sin abrir producción ni ejecutar toda la suite otra vez.
            (root/'lanzar.py').write_text('import sys\nassert sys.argv[1:]==["probar", "argumento con espacios"]\nprint("RESOLUTOR_OK")\n',encoding='utf-8')
            cmd=Path(os.environ['SystemRoot'])/'System32/cmd.exe'
            command='"'+str(cmd)+'" /d /s /c ""'+str(root/'EJECUTAR.bat')+'" probar "argumento con espacios""'
            result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
            self.assertEqual(result.returncode,0,result.stdout);self.assertIn(b'RESOLUTOR_OK',result.stdout)
