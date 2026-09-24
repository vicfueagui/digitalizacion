"""Abrir el asistente de traslado sin datos, comprobar distribución y cerrar."""
from pathlib import Path
import sys
import tkinter as tk
import tempfile
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from app.migration_ui import MigrationWindow

root=tk.Tk();window=MigrationWindow(root);root.update()
for size in ('900x730','1024x768'):
    root.geometry(size);root.update()
    for button in window.buttons:
        if button.winfo_viewable():
            right=button.winfo_rootx()-root.winfo_rootx()+button.winfo_width()
            assert right<=root.winfo_width(),(button['text'],size,right)
from app.demo import create_demo
from app.integrity import diagnose
from app.workspace import Workspace
with tempfile.TemporaryDirectory() as temp:
    ws=Workspace(create_demo(Path(temp)/'demo'))
    window.work('Auditoría sintética en trabajador',lambda:diagnose(ws,ROOT))
    completed=[]
    def finish():
        if window.busy:root.after(150,finish);return
        text=window.text.get('1.0','end')
        completed.append('"correcto": true' in text)
        root.destroy()
    root.after(150,finish);root.after(30000,root.destroy);root.mainloop()
    assert completed==[True], 'No terminó la auditoría de prueba en la ventana' 
print('OK: asistente de migración abierto, controles visibles, sin datos operacionales.')
