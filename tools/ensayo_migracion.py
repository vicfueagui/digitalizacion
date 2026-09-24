"""Traslado completo reproducible con DEMO, nunca con producción ni aceptación real."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from app.backup import sha256
from app.transfer import export_migration,verify_package,restore_migration,compare_source,verify_destination
from app.migration_acceptance import rehearse,activate
from app.runtime import environment
from app.workspace import Workspace
from app.update_recovery import write_json


def run(destination,code):
    destination.mkdir(parents=True,exist_ok=False)
    origin=destination/'Origen usuario anterior á';workspace=Workspace(origin)
    subprocess.run([sys.executable,str(code/'main.py'),'--crear-demo',str(origin)],cwd=str(code),env=environment(),check=True)
    if not (origin/'DEMO.json').is_file():raise ValueError('Solo se permite la demo creada por el ensayo.')
    before=sha256(workspace.database)
    exported=export_migration(workspace,code,destination/'Paquete conservador',laboratory=True)
    package=Path(exported['paquete']);digest=exported['sha256_manifiesto']
    manifest=verify_package(package,digest)
    comparison=compare_source(package,workspace,digest)
    if comparison['diferencias']:raise ValueError('Origen alterado durante ensayo.')
    target=destination/'Otro usuario ñ unidad nueva'
    restored=restore_migration(package,target,digest)
    verified=verify_destination(target)
    if verified['diferencias']:raise ValueError('Destino diferente.')
    trial=rehearse(target,sys.executable)
    accepted=activate(target,confirmed=True)  # Exclusivamente paquete marcado DEMO/laboratorio.
    if accepted['estado']!='Laboratorio habilitado':raise ValueError('El ensayo jamás habilita producción.')
    # Abrir el MISMO código con la copia restaurada real del ensayo; leer ambas clases de TIFF.
    script='''import sys,tkinter as tk
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from app.core import Store
from app.ui import App
from app.coding import page_info
from PIL import Image,ImageTk
store=Store(workspace=sys.argv[2]);app=App(store)
classes=set();images=[]
for row in store.rows('SELECT ruta,paginas FROM archivos_tiff WHERE activo=1'):
 path=store.workspace.path(row['ruta']);info=page_info(path,True);classes.add('multi' if len(info)>1 else 'single')
 with Image.open(str(path)) as image:
  for page in range(image.n_frames):
   image.seek(page);preview=image.copy();preview.thumbnail((240,240));images.append(ImageTk.PhotoImage(preview,master=app));preview.close()
assert classes=={'multi','single'},classes
label=tk.Label(app,image=images[-1]);label.pack();app.update();app.after(800,app.destroy);app.mainloop();store.db.close()
print('MISMO CODIGO: aplicación y TIFF individual/multipágina restaurados abiertos correctamente')
'''
    with (destination/'abrir_restaurado.log').open('x',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-c',script,str(target/'programa'),str(target/'workspace')],
                       cwd=str(target/'programa'),env=environment(),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    after=compare_source(package,workspace,digest)
    result={'exportacion':exported,'origen':comparison,'restauracion':restored,'destino_antes_de_captura':verified,
            'ensayo':trial,'aceptacion_demo':accepted,'version_codigo_conservado':manifest['version_aplicacion'],
            'origen_sqlite_bytes_intactos':sha256(workspace.database)==before,'origen_al_final':after,
            'apertura_real_demo_restaurada':True,'produccion_certificada':False}
    write_json(destination/'resultado.json',result)
    if not result['origen_sqlite_bytes_intactos'] or after['diferencias']:raise ValueError('El origen cambió.')
    print('ENSAYO FICTICIO COMPLETO. Informe:',destination/'resultado.json')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destino',required=True);parser.add_argument('--codigo',default=str(ROOT))
    args=parser.parse_args();run(Path(args.destino).resolve(),Path(args.codigo).resolve())


if __name__=='__main__':main()
