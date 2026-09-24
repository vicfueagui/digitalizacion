"""Recorrido Tk; tareas de disco en un trabajador, sin bloquear la ventana."""
import datetime
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox

from .workspace import Workspace,CODE_ROOT
from .integrity import diagnose,save_report
from .transfer import export_migration,verify_package,restore_migration,compare_source,verify_destination,load_installation
from .migration_acceptance import rehearse,activate,launch
from .runtime import environment


class MigrationWindow:
    def __init__(self,root):
        self.root=root;self.busy=False;self.events=queue.Queue();self.buttons=[]
        root.title('Digitalización — traslado a Windows 10');root.geometry('900x730');root.minsize(720,590)
        box=ttk.Frame(root,padding=16);box.pack(fill='both',expand=True)
        ttk.Label(box,text='Trasladar el sistema conservando sus datos',font=('TkDefaultFont',16,'bold')).pack(anchor='w')
        ttk.Label(box,text='Primero prepara en Windows 7. Después restaura y comprueba en Windows 10.\nConserva el origen cerrado: no trabajes en las dos computadoras a la vez.',wraplength=820).pack(anchor='w',pady=(6,12))
        tabs=ttk.Notebook(box);tabs.pack(fill='x');source=ttk.Frame(tabs,padding=12);target=ttk.Frame(tabs,padding=12)
        tabs.add(source,text='1 · Equipo de origen');tabs.add(target,text='2 · Equipo nuevo')
        self.ws=self.field(source,'Carpeta de datos del origen',0)
        self.code=self.field(source,'Carpeta del programa que funciona',1)
        ttk.Label(source,text='Si todo está junto, selecciona la misma carpeta en ambos campos.').grid(row=2,column=0,columnspan=3,sticky='w',pady=6)
        self.old=tk.StringVar();ttk.Label(source,text='Raíz histórica probada (opcional)').grid(row=3,column=0,sticky='w')
        ttk.Entry(source,textvariable=self.old).grid(row=3,column=1,columnspan=2,sticky='ew')
        self.lab=tk.BooleanVar();ttk.Checkbutton(source,text='Solo laboratorio: exige datos ficticios con marca DEMO',variable=self.lab).grid(row=4,column=0,columnspan=3,sticky='w',pady=8)
        bar=ttk.Frame(source);bar.grid(row=5,column=0,columnspan=3,sticky='w')
        self.button(bar,'Auditar datos',self.audit);self.button(bar,'Preparar migración',self.export);self.button(bar,'Comparar origen con paquete',self.compare)
        self.package=self.field(target,'Carpeta del paquete recibido',0)
        self.digest=tk.StringVar();ttk.Label(target,text='SHA-256 guardado en origen').grid(row=1,column=0,sticky='w')
        ttk.Entry(target,textvariable=self.digest).grid(row=1,column=1,columnspan=2,sticky='ew')
        self.install=self.field(target,'Carpeta de instalación restaurada',2)
        bar=ttk.Frame(target);bar.grid(row=3,column=0,columnspan=3,sticky='w',pady=8)
        self.button(bar,'Verificar paquete',self.verify);self.button(bar,'Restaurar en carpeta nueva',self.restore)
        bar=ttk.Frame(target);bar.grid(row=4,column=0,columnspan=3,sticky='w',pady=4)
        self.button(bar,'Verificar destino',lambda:self.destination('verify'));self.button(bar,'Ejecutar ensayo',lambda:self.destination('rehearse'));self.button(bar,'Abrir demo',self.demo)
        self.confirm=tk.BooleanVar();ttk.Checkbutton(target,text='Revisé la demo y los TIFF. Windows 7 está cerrado y seguirá congelado.',variable=self.confirm).grid(row=5,column=0,columnspan=3,sticky='w',pady=8)
        bar=ttk.Frame(target);bar.grid(row=6,column=0,columnspan=3,sticky='w')
        self.button(bar,'Habilitar destino',lambda:self.destination('activate'));self.button(bar,'Abrir sistema',lambda:self.destination('launch'))
        self.status=tk.StringVar(value='Listo. Los informes permanecen en este equipo; no se envían por internet.')
        ttk.Label(box,textvariable=self.status,wraplength=820).pack(anchor='w',pady=(12,4))
        self.progress=ttk.Progressbar(box,mode='indeterminate');self.progress.pack(fill='x')
        frame=ttk.Frame(box);frame.pack(fill='both',expand=True,pady=8)
        self.text=tk.Text(frame,height=10,wrap='word',state='disabled');scroll=ttk.Scrollbar(frame,command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set);self.text.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
        self.button(box,'Copiar resultado',self.copy_result)
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(150,self.poll)

    def field(self,parent,label,row):
        var=tk.StringVar();ttk.Label(parent,text=label).grid(row=row,column=0,sticky='w',padx=(0,10),pady=4)
        ttk.Entry(parent,textvariable=var).grid(row=row,column=1,sticky='ew');parent.columnconfigure(1,weight=1)
        def choose():
            value=filedialog.askdirectory(parent=self.root,title=label)
            if value:var.set(value)
        ttk.Button(parent,text='Elegir…',command=choose).grid(row=row,column=2,padx=(6,0));return var

    def button(self,parent,label,command):
        def guarded():
            try:command()
            except (ValueError,OSError) as error:messagebox.showerror('No se puede continuar',str(error),parent=self.root)
        button=ttk.Button(parent,text=label,command=guarded);button.pack(side='left',padx=(0,6));self.buttons.append(button)

    def required(self,var):
        value=var.get().strip()
        if not value:raise ValueError('Completa las carpetas indicadas antes de continuar.')
        return Path(value).resolve()

    def sha(self):
        value=self.digest.get().strip().lower()
        if len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Pega los 64 caracteres del SHA-256 guardado al preparar la migración.')
        return value

    def new_folder(self,title,prefix):
        value=filedialog.asksaveasfilename(parent=self.root,title=title,initialfile=prefix+'-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        return Path(value).resolve() if value else None

    def work(self,title,function):
        if self.busy:return
        self.busy=True;self.status.set(title+'… Puede tardar varios minutos.');self.progress.start(15)
        for button in self.buttons:button.configure(state='disabled')
        def task():
            try:self.events.put((True,function()))
            except Exception as error:self.events.put((False,str(error)))
        threading.Thread(target=task,daemon=True).start()

    def poll(self):
        try:
            ok,result=self.events.get_nowait();self.busy=False;self.progress.stop()
            for button in self.buttons:button.configure(state='normal')
            self.status.set('Operación completada. Lee el resultado.' if ok else 'Operación detenida. No continúes hasta resolver la causa.')
            self.text.configure(state='normal');self.text.delete('1.0','end');self.text.insert('end',json.dumps(result,ensure_ascii=False,indent=2) if ok else result);self.text.configure(state='disabled')
            if ok and isinstance(result,dict):
                if result.get('paquete'):self.package.set(result['paquete']);self.digest.set(result['sha256_manifiesto'])
                if result.get('instalacion'):self.install.set(result['instalacion'])
        except queue.Empty:pass
        self.root.after(150,self.poll)

    def audit(self):
        ws=Workspace(self.required(self.ws));code=self.required(self.code);out=self.new_folder('Guardar diagnóstico en carpeta nueva','Diagnostico')
        if not out:return
        def action():
            report=diagnose(ws,code);save_report(report,out)
            return {'correcto':report['correcto'],'problemas':report['problemas'],'informe':str(out)}
        self.work('Auditando SQLite y todos los TIFF',action)

    def export(self):
        ws=Workspace(self.required(self.ws));code=self.required(self.code);lab=self.lab.get();old=self.old.get().strip()
        out=self.new_folder('Crear paquete en carpeta nueva fuera del origen','Digitalizacion-Migracion')
        if out:self.work('Preparando migración',lambda:export_migration(ws,code,out,historical_roots=[old] if old else [],laboratory=lab))

    def compare(self):
        ws=Workspace(self.required(self.ws));package=self.required(self.package);digest=self.sha()
        self.work('Comparando origen congelado',lambda:compare_source(package,ws,digest))

    def verify(self):
        package=self.required(self.package);digest=self.sha()
        def action():
            result=verify_package(package,digest);return {'conclusion':'PAQUETE VERIFICADO','id':result['id'],'solo_laboratorio':result['solo_laboratorio']}
        self.work('Verificando todos los archivos del paquete',action)

    def restore(self):
        package=self.required(self.package);digest=self.sha();out=self.new_folder('Crear instalación nueva (no seleccionar una existente)','Digitalizacion')
        if out:self.work('Restaurando en espacio nuevo',lambda:restore_migration(package,out,digest))

    def destination(self,action):
        root=self.required(self.install);confirmed=self.confirm.get()
        functions={'verify':lambda:verify_destination(root),'rehearse':lambda:rehearse(root),
                   'activate':lambda:activate(root,confirmed),'launch':lambda:launch(root)}
        self.work({'verify':'Verificando destino','rehearse':'Ejecutando pruebas y ventanas con datos ficticios','activate':'Habilitando destino','launch':'Sistema abierto; cierra la aplicación para volver'}[action],functions[action])

    def demo(self):
        root,state,manifest=load_installation(self.required(self.install))
        if not state.get('ensayo'):raise ValueError('Ejecuta primero el ensayo.')
        from .manifests import plain_path
        report=plain_path(root,state['ensayo']);info=json.loads(report.read_text(encoding='utf-8'))
        self.work('Demo abierta; revisa TIFF de una y varias páginas y ciérrala',lambda:subprocess.call(
            [info['ejecutable'],str(root/'programa/main.py'),'--workspace',str(report.parent/'demo')],cwd=str(root/'programa'),env=environment()))

    def copy_result(self):
        self.root.clipboard_clear();self.root.clipboard_append(self.text.get('1.0','end').strip())

    def close(self):
        if self.busy:messagebox.showinfo('Operación en curso','Espera a que finalice. Cerrar por la fuerza deja el traslado bloqueado.',parent=self.root)
        else:self.root.destroy()


def run(audit=False):
    root=tk.Tk();window=MigrationWindow(root)
    if audit:window.status.set('Selecciona datos y programa del origen; pulsa Auditar datos.')
    root.mainloop()
