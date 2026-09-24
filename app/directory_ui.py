"""Selectores editables y mantenimiento del directorio operativo."""
import tkinter as tk
import sqlite3
from tkinter import ttk,messagebox,simpledialog
from .directory import Directory,KINDS


class DirectoryPicker(ttk.Frame):
    def __init__(self,parent,store,kind,variable):
        super().__init__(parent);self.directory=Directory(store);self.kind=kind;self.variable=variable
        self.combo=ttk.Combobox(self,textvariable=variable,width=45,postcommand=self.refresh)
        self.combo.pack(side='left',fill='x',expand=True)
        ttk.Button(self,text='+ / Editar',command=lambda:directory_window(self,store,kind,self.selected)).pack(side='left',padx=(4,0))
        self.refresh()
    def refresh(self):self.combo.configure(values=[r['nombre'] for r in self.directory.entries(self.kind)])
    def selected(self,row):self.refresh();self.variable.set(row['nombre'])


def directory_window(parent,store,kind='persona',on_select=None):
    from .ui import Table,Form
    win=tk.Toplevel(parent);win.title('Directorio · altas, cambios y bajas');win.geometry('860x500');win.transient(parent.winfo_toplevel())
    previous=win.grab_current();win.grab_set()
    def close():
        win.destroy()
        if previous:
            try:
                if previous.winfo_exists():previous.grab_set()
            except tk.TclError:pass
    win.protocol('WM_DELETE_WINDOW',close)
    directory=Directory(store);bar=ttk.Frame(win,padding=8);bar.pack(fill='x')
    names={v:k for k,v in KINDS.items()};category=tk.StringVar(value=KINDS[kind]);query=tk.StringVar();inactive=tk.BooleanVar()
    combo=ttk.Combobox(bar,textvariable=category,values=list(names),state='readonly',width=25);combo.pack(side='left')
    ttk.Label(bar,text='Buscar').pack(side='left',padx=5);ttk.Entry(bar,textvariable=query,width=25).pack(side='left')
    table=Table(win,['id','nombre','notas','activo']);table.pack(fill='both',expand=True,padx=8)
    table.tree.column('id',width=45);table.tree.column('nombre',width=280);table.tree.column('activo',width=55)
    def refresh(*args):table.fill(directory.entries(names[category.get()],query.get(),inactive.get()))
    def edit(ident=None):
        old=directory.get(ident) if ident else {}
        def save(values):
            row_id=directory.save(names[category.get()],values['nombre'],values['notas'],ident,values['motivo']);refresh()
            if on_select:on_select(directory.get(row_id))
        Form(win,'Editar registro' if ident else 'Nuevo registro',[
            ('nombre','Nombre',old.get('nombre','')),('notas','Notas / función / contacto',old.get('notas','')),
            ('motivo','Motivo','Alta de directorio' if not ident else '')],save)
    def toggle():
        reason=simpledialog.askstring('Baja / reactivación','Motivo. Se conservan sus vínculos y nombres históricos.',parent=win)
        if reason:directory.toggle(table.selected(),reason);refresh()
    def select():
        row=directory.get(table.selected())
        if not row['activo']:raise ValueError('Reactiva el registro antes de seleccionarlo.')
        if on_select:on_select(row);close()
    def safe(action):
        try:action()
        except (ValueError,OSError,sqlite3.Error) as error:
            # Los errores de captura quedan visibles; no se descarta una operación fallida.
            messagebox.showerror('Directorio',str(error),parent=win)
    actions=ttk.Frame(win,padding=8);actions.pack(fill='x')
    for title,action in [('Nuevo',edit),('Editar',lambda:edit(table.selected())),('Desactivar / reactivar',toggle)]:
        ttk.Button(actions,text=title,command=lambda fn=action:safe(fn)).pack(side='left',padx=3)
    if on_select:ttk.Button(actions,text='Usar seleccionado',command=lambda:safe(select)).pack(side='left',padx=3)
    ttk.Checkbutton(bar,text='Incluir bajas',variable=inactive,command=refresh).pack(side='left',padx=5)
    combo.bind('<<ComboboxSelected>>',refresh);query.trace_add('write',refresh)
    ttk.Label(win,text='La baja impide nuevas selecciones; no borra préstamos ni asignaciones. Renombrar conserva el texto de los registros anteriores.',wraplength=820,padding=8).pack(fill='x')
    refresh();return win
