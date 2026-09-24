"""Instalación local, sin red, del visor para Python 3.8 de Windows x64."""
import hashlib
import platform
import struct
import subprocess
import sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent
    wheel=root/'instaladores'/'Pillow-9.5.0-cp38-cp38-win_amd64.whl'
    if sys.platform!='win32' or platform.python_implementation()!='CPython' or sys.version_info[:3]!=(3,8,10) or struct.calcsize('P')!=8:
        raise SystemExit('Este instalador requiere Windows y Python 3.8 de 64 bits. Intérprete actual: '+sys.version)
    if sys.prefix == sys.base_prefix:
        raise SystemExit('Crea primero .venv con Python 3.8.10 x64 y ejecuta .venv\\Scripts\\python.exe instalar_visor.py. No se instalará globalmente.')
    expected=(root/'instaladores'/'SHA256.txt').read_text().split()[0]
    if hashlib.sha256(wheel.read_bytes()).hexdigest()!=expected:raise SystemExit('El instalador no coincide con su huella. Descarga de nuevo la actualización.')
    subprocess.check_call([sys.executable,'-m','pip','install','--no-index','--no-deps',str(wheel)])
    subprocess.check_call([sys.executable,'-c',"from PIL import Image,ImageTk,features; print('Pillow',Image.__version__); assert features.check('libtiff'), 'Falta soporte TIFF'; print('Visor TIFF instalado correctamente')"])

if __name__=='__main__':main()
