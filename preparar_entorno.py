"""Preparación local del perfil conservador; no instala Pillow globalmente."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import uuid
import venv

from app.runtime import probe,environment

ROOT=Path(__file__).resolve().parent


def prepare(destination):
    destination=Path(destination).absolute()
    probe(Path(sys.executable),'instalar')
    if os.name!='nt':raise ValueError('Este preparador es para Windows. Los entornos de laboratorio Mac son independientes.')
    executable=destination/'Scripts/python.exe'
    if destination.exists():
        info=probe(executable,'instalar')
        if info.get('pillow') not in (None,'9.5.0'):
            raise ValueError('Este entorno ya usa otro Pillow. Elige una carpeta nueva; no se cambiarán sus dependencias.')
    else:
        venv.EnvBuilder(with_pip=True).create(str(destination))
        probe(executable,'instalar')  # Incluye el incidente real del ejecutable vacío.
    process=subprocess.run([str(executable),str(ROOT/'instalar_visor.py')],cwd=str(ROOT),env=environment())
    if process.returncode:raise ValueError('No se completó la instalación local de Pillow. Conserva el mensaje anterior.')
    probe(executable,'legado')
    config=ROOT/'python_ruta.txt'
    if config.exists():
        backup=ROOT/('python_ruta.anterior-'+uuid.uuid4().hex+'.txt')
        backup.write_bytes(config.read_bytes())
    temporary=ROOT/('.python_ruta-'+uuid.uuid4().hex+'.tmp')
    with temporary.open('x',encoding='utf-8') as out:
        out.write(str(executable)+'\n');out.flush();os.fsync(out.fileno())
    os.replace(str(temporary),str(config))
    return executable


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destino',help='Carpeta del entorno local (nunca copiar una .venv de otro equipo)')
    args=parser.parse_args()
    if args.destino:
        print('Entorno comprobado:',prepare(args.destino));return 0
    import tkinter as tk
    from tkinter import filedialog,messagebox
    root=tk.Tk();root.withdraw()
    try:
        destination=ROOT/'.venv'
        if destination.exists():
            try:probe(destination/'Scripts/python.exe','instalar')
            except (ValueError,OSError,subprocess.TimeoutExpired):
                messagebox.showinfo('Entorno anterior inválido','Se conservará el entorno anterior. Elige una carpeta contenedora para crear uno nuevo.',parent=root)
                parent=filedialog.askdirectory(parent=root,title='Dónde crear un entorno nuevo')
                if not parent:return 0
                destination=Path(parent)/('digitalizacion-python38-'+uuid.uuid4().hex[:6])
        if not messagebox.askokcancel('Preparar entorno local','Se comprobará/creará:\n'+str(destination)+'\n\nPython 3.8.10 x64 y Pillow 9.5.0. No se cambiarán datos del proyecto.',parent=root):return 0
        executable=prepare(destination)
        messagebox.showinfo('Entorno listo','Python comprobado:\n'+str(executable)+'\nAhora puedes abrir MIGRAR.bat.',parent=root)
        return 0
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        messagebox.showerror('Preparación detenida',str(error),parent=root);return 1
    finally:root.destroy()


if __name__=='__main__':sys.exit(main())
