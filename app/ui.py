import datetime
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from .core import Store, ROOT, STATES, TASK_STATES
from . import VERSION
from .importers import import_excel, import_csv
from .operational_ui import OperationalUI

class Form(tk.Toplevel):
    """Formulario modal. Campos: clave, etiqueta, valor inicial, opciones opcionales."""
    def __init__(self,parent,title,fields,submit,preview=None):
        super().__init__(parent);self.title(title);self.transient(parent);self.previous_grab=self.grab_current();self.grab_set()
        self.values={};self.columnconfigure(1,weight=1)
        for i,field in enumerate(fields):
            key,label,value=field[:3]
            ttk.Label(self,text=label).grid(row=i,column=0,sticky='w',padx=12,pady=5)
            var=tk.StringVar(value='' if value is None else str(value));self.values[key]=var
            if len(field)>3 and isinstance(field[3],dict):
                from .directory_ui import DirectoryPicker
                widget=DirectoryPicker(self,field[3]['store'],field[3]['kind'],var)
            elif len(field)>3:
                widget=ttk.Combobox(self,textvariable=var,values=field[3],state='readonly',width=60)
            else:widget=ttk.Entry(self,textvariable=var,width=63)
            widget.grid(row=i,column=1,sticky='ew',padx=12,pady=5)
            if i==0:(widget.combo if hasattr(widget,'combo') else widget).focus_set()
        def save():
            try:
                submit({k:v.get().strip() for k,v in self.values.items()});self.destroy()
            except (ValueError,sqlite3.Error,OSError) as e:messagebox.showerror('Revisa los datos',str(e),parent=self)
        bar=ttk.Frame(self);bar.grid(row=len(fields),column=0,columnspan=2,pady=15)
        ttk.Button(bar,text='Guardar',command=save).pack(side='left',padx=8)
        ttk.Button(bar,text='Cancelar',command=self.destroy).pack(side='left')
        if preview:
            def show_preview():
                try:preview({k:v.get().strip() for k,v in self.values.items()})
                except (ValueError,sqlite3.Error,OSError) as e:messagebox.showerror('Vista previa',str(e),parent=self)
            ttk.Button(bar,text='Ver TIFF elegido',command=show_preview).pack(side='left',padx=8)
        self.bind('<Escape>',lambda e:self.destroy())
    def destroy(self):
        previous=getattr(self,'previous_grab',None)
        super().destroy()
        if previous:
            try:
                if previous.winfo_exists():previous.grab_set()
            except tk.TclError:pass

class Table(ttk.Frame):
    def __init__(self,parent,columns):
        super().__init__(parent);self.columns=columns
        self.tree=ttk.Treeview(self,columns=columns,show='headings',selectmode='browse')
        for c in columns:
            self.tree.heading(c,text=c,anchor='center');self.tree.column(c,width=130,minwidth=60,anchor='center')
        self.tree.bind('<Control-Return>',self.show_row)
        y=ttk.Scrollbar(self,orient='vertical',command=self.tree.yview)
        x=ttk.Scrollbar(self,orient='horizontal',command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        self.tree.grid(row=0,column=0,sticky='nsew');y.grid(row=0,column=1,sticky='ns');x.grid(row=1,column=0,sticky='ew')
        self.columnconfigure(0,weight=1);self.rowconfigure(0,weight=1)
    def fill(self,rows):
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(rows):
            self.tree.insert('', 'end', iid=str(r.get('id',i)),values=[r.get(c,'') if r.get(c) is not None else '' for c in self.columns])
    def selected(self):
        s=self.tree.selection()
        if not s:raise ValueError('Selecciona primero una fila de la lista.')
        try:return int(s[0])
        except ValueError:return s[0]

    def show_row(self,event=None):
        selection=self.tree.selection()
        if not selection:return
        win=tk.Toplevel(self);win.title('Contenido completo de la fila');win.geometry('760x480')
        text=tk.Text(win,wrap='word');text.pack(fill='both',expand=True)
        for name,value in zip(self.columns,self.tree.item(selection[0],'values')):
            text.insert('end',str(name)+': '+str(value)+'\n\n')
        text.configure(state='disabled')

class App(OperationalUI,tk.Tk):
    def __init__(self,store):
        super().__init__();self.store=store;self.title('Digitalización · Control local '+VERSION);self.geometry('1120x740');self.minsize(880,620)
        if self.tk.call('tk','windowingsystem')=='win32':self.option_add('*Font','{Segoe UI} 10')
        style=ttk.Style(self)
        if 'clam' in style.theme_names():style.theme_use('clam')
        style.configure('Treeview',rowheight=27);style.configure('Title.TLabel',font=('Segoe UI',18,'bold'),foreground='#173c4c')
        top=ttk.Frame(self,padding=12);top.pack(fill='x')
        ttk.Label(top,text='Digitalización',style='Title.TLabel').pack(side='left')
        ttk.Label(top,text='Control de expedientes · local · un operador',padding=12).pack(side='left')
        ttk.Button(top,text='Cambiar operador',command=lambda:self.safe(self.operator)).pack(side='right')
        ttk.Button(top,text='Ayuda',command=lambda:self.safe(self.help)).pack(side='right',padx=5)
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=12,pady=6)
        self.pages={}
        for name in ('Expedientes','Indicadores','Kanban','Folios','Catálogos','Reportes TIFF','Importación y respaldo'):
            page=ttk.Frame(self.tabs,padding=8);self.tabs.add(page,text=name);self.pages[name]=page
        self.status=tk.StringVar(value='Listas nuevas: Folios → Importar lista Excel/CSV. Consulta Ayuda para el recorrido completo.')
        ttk.Label(self,textvariable=self.status,padding=10,wraplength=1050).pack(fill='x')
        self.filter_job=None
        self.setup_works();self.setup_dashboard();self.setup_kanban();self.setup_folios();self.setup_catalog();self.setup_reports();self.setup_import()
        if (self.store.workspace.root/'DEMO.json').exists():self.title(self.title()+' · DEMOSTRACIÓN FICTICIA')
        self.refresh();self.protocol('WM_DELETE_WINDOW',self.close)
        self.tabs.bind('<<NotebookTabChanged>>',lambda e:self.safe(lambda:self.bi.refresh(self.filtered())) if self.tabs.tab(self.tabs.select(),'text')=='Indicadores' else None)

    def help(self):
        import webbrowser
        manual=ROOT/'docs/MANUAL_USUARIO.html'
        if not manual.is_file():raise ValueError('No se encontró el manual. Recupera el paquete completo de esta versión.')
        if not webbrowser.open(manual.as_uri()):
            messagebox.showinfo('Manual de uso','Abre este archivo en tu navegador:\n'+str(manual),parent=self)

    def safe(self,fn):
        try:
            self.configure(cursor='watch');self.update_idletasks()
            return fn()
        except (ValueError,sqlite3.Error,OSError,KeyError) as e:messagebox.showerror('Revisa la operación',str(e),parent=self)
        finally:
            if self.winfo_exists():self.configure(cursor='')
    def button(self,parent,label,fn):
        ttk.Button(parent,text=label,command=lambda:self.safe(fn)).pack(side='left',padx=3,pady=4)
    def bar(self,page):
        f=ttk.Frame(page);f.pack(fill='x');return f
    def operator(self):
        from .directory import Directory
        def save(values):
            value=values['persona'].strip()
            if not value:raise ValueError('Selecciona o registra la persona operadora.')
            with self.store.db:Directory(self.store).ensure('persona',value)
            self.store.operador=value;self.status.set('Operador: '+value)
        Form(self,'Operador local',[('persona','Persona que aparecerá en bitácora',self.store.operador,{'store':self.store,'kind':'persona'})],save)
    def close(self):
        coder=getattr(self,'coder',None)
        if coder is not None and coder.winfo_exists() and not coder.close():return
        try:self.store.backup()
        except Exception as e:
            if not messagebox.askyesno('No se pudo respaldar',str(e)+'\n¿Cerrar de todas formas?'):return
        if self.filter_job:self.after_cancel(self.filter_job);self.filter_job=None
        self.store.db.close();self.destroy()

    def setup_works(self):
        p=self.pages['Expedientes'];f=self.bar(p);self.filters={}
        fields=[('texto','CURP / nombre',22),('folio','Folio',12),('estado','Estado',23),('digitalizador','Digitalizador',16)]
        for key,label,width in fields:
            ttk.Label(f,text=label).pack(side='left',padx=3);v=tk.StringVar();self.filters[key]=v
            if key=='estado':ttk.Combobox(f,textvariable=v,values=['']+STATES,width=width,state='readonly').pack(side='left')
            else:ttk.Entry(f,textvariable=v,width=width).pack(side='left')
        f=self.bar(p)
        for key,label in [('desde','Recibido desde'),('hasta','hasta')]:
            ttk.Label(f,text=label).pack(side='left',padx=3);v=tk.StringVar();self.filters[key]=v;ttk.Entry(f,textvariable=v,width=12).pack(side='left')
        self.show_inactive=tk.BooleanVar();ttk.Checkbutton(f,text='Incluir inactivos',variable=self.show_inactive).pack(side='left',padx=5)
        self.button(f,'Filtrar',self.refresh);self.button(f,'Limpiar',self.clear_filters)
        f=self.bar(p)
        self.button(f,'Nuevo',lambda:self.work_form());self.button(f,'Editar',lambda:self.work_form(self.works_table.selected()))
        self.button(f,'Expediente 360',lambda:self.summary_window(self.works_table.selected()))
        self.button(f,'Codificar TIFF',self.open_coder)
        self.button(f,'Registros asociados',self.associated_view)
        self.button(f,'Desactivar / reactivar',lambda:self.toggle('trabajos',self.works_table.selected()))
        more=self.bar(p)
        self.button(more,'Ver / añadir legajos de la misma CURP',lambda:self.legajos_view(self.works_table.selected()))
        self.button(more,'Importar lista de folio Excel / CSV',self.import_loan_list)
        ttk.Label(p,text='Inventario activo del ciclo vigente: TIFF y páginas. Escribe para filtrar; no se suman entregas históricas.').pack(anchor='w')
        self.works_table=Table(p,['id','curp','nombre','folio','legajo','estado','total_tiff','total_paginas','fisicos','digitalizador','recepcion'])
        self.works_table.tree.configure(displaycolumns=('curp','nombre','folio','legajo','estado','total_tiff','total_paginas','fisicos','digitalizador','recepcion'))
        for column,title,width in [('curp','CURP',172),('nombre','Nombre',190),('folio','Folio',85),('legajo','Leg.',45),('estado','Proceso',145),('total_tiff','TIFF',55),('total_paginas','Páginas',65),('fisicos','Hojas físicas',80),('digitalizador','Digitalizador',115),('recepcion','Recepción',95)]:
            self.works_table.tree.heading(column,text=title);self.works_table.tree.column(column,width=width,minwidth=35,stretch=column=='nombre')
        self.works_table.pack(fill='both',expand=True)
        self.works_table.tree.bind('<Double-1>',lambda e:self.safe(lambda:self.summary_window(self.works_table.selected())))
        for variable in list(self.filters.values())+[self.show_inactive]:variable.trace_add('write',self.schedule_filter)
    def associated_view(self):
        ident=self.works_table.selected();win=tk.Toplevel(self);win.title('Registros históricos de la misma CURP y legajo');win.geometry('1050x550')
        ttk.Label(win,text='Ciclos de un mismo expediente maestro en distintos folios. Elegir el ciclo vigente no fusiona ni borra conteos, documentos o historiales.',wraplength=1000).pack()
        table=Table(win,['id','folio','curp','legajo','estado','fisicos','activo']);table.pack(fill='both',expand=True);table.fill(self.store.associated(ident))
        bar=self.bar(win)
        self.button(bar,'Expediente 360 del ciclo',lambda:self.summary_window(table.selected()))
        def choose():
            reason=self.reason()
            if reason:self.store.prefer(table.selected(),reason);self.refresh()
        def code():
            from .coding_ui import CodingWindow
            coder=getattr(self,'coder',None)
            if coder is not None and coder.winfo_exists() and not coder.close():return
            self.coder=CodingWindow(self,table.selected())
        self.button(bar,'Usar como registro principal',choose);self.button(bar,'Ver TIFF de este registro',code)

    def open_coder(self):
        from .coding_ui import CodingWindow
        ident=self.works_table.selected()
        coder=getattr(self,'coder',None)
        if coder is not None and coder.winfo_exists():
            if coder.work==ident:coder.lift();return
            if not coder.close():return
        version=self.store.rows("SELECT value FROM meta WHERE key='coding_schema_version'")
        if not version or version[0]['value']!='3':self.store.backup()
        self.coder=CodingWindow(self,ident)

    def clear_filters(self):
        for v in self.filters.values():v.set('')
        self.show_inactive.set(False);self.refresh()
    def legajos_view(self,ident):
        work=self.store.one('trabajos',ident);win=tk.Toplevel(self);win.title('Legajos de '+work['curp']);win.geometry('1050x570')
        ttk.Label(win,text='Cada legajo conserva su conteo, TIFF y entregas. Los ciclos de otros folios permanecen en el historial.',padding=8).pack(anchor='w')
        bar=self.bar(win);table=Table(win,['id','curp','legajo','folio','estado','total_tiff','total_paginas','fisicos','digitalizador'])
        table.pack(fill='both',expand=True);table.fill([r for r in self.store.works(activos=False) if r['curp']==work['curp']])
        self.button(bar,'Abrir Expediente 360',lambda:self.summary_window(table.selected()))
        def add():
            from .intake import register_legajos
            def save(values):
                register_legajos(self.store,work['prestamo_item_id'],values['legajos'],values['motivo']);self.refresh()
                table.fill([r for r in self.store.works(activos=False) if r['curp']==work['curp']])
            Form(win,'Añadir físicos al folio '+self.store.one('folios',work['folio_id'])['numero'],[('legajos','Números de legajo separados por comas',''),('motivo','Evidencia del desglose físico','')],save)
        self.button(bar,'Añadir legajos en este folio',add)
        return win

    def schedule_filter(self,*args):
        if self.filter_job:self.after_cancel(self.filter_job)
        self.filter_job=self.after(220,self.refresh_filtered)
    def filtered(self):
        from .core import date
        values={k:v.get().strip() for k,v in self.filters.items()};self.filter_date_hint=''
        for key in ('desde','hasta'):
            if values[key]:
                try:values[key]=date(values[key])
                except ValueError:values[key]='';self.filter_date_hint='Completa la fecha (AAAA-MM-DD) para aplicar ese límite.'
        return self.store.works(**values,activos=not self.show_inactive.get(),partial=True)
    def refresh_filtered(self,update_dashboard=True):
        if self.filter_job:self.after_cancel(self.filter_job)
        self.filter_job=None;selected=self.works_table.tree.selection();rows=self.filtered()
        self.works_table.fill(rows)
        if selected and self.works_table.tree.exists(selected[0]):self.works_table.tree.selection_set(selected[0]);self.works_table.tree.see(selected[0])
        self.status.set('{} expedientes encontrados. {}'.format(len(rows),self.filter_date_hint))
        if update_dashboard and hasattr(self,'bi') and self.tabs.tab(self.tabs.select(),'text')=='Indicadores':self.bi.refresh(rows)
        return rows
    def reason(self):return simpledialog.askstring('Trazabilidad','¿Por qué realizas este cambio?',parent=self)
    def toggle(self,table,ident):
        reason=self.reason()
        if reason:self.store.toggle(table,ident,reason);self.refresh()
    def work_form(self,ident=None):
        old=self.store.one('trabajos',ident) if ident else {}
        folios=self.store.rows('SELECT * FROM folios WHERE activo=1 ORDER BY numero')
        if not folios:raise ValueError('Primero crea un folio en la pestaña Folios.')
        mapping={str(f['id'])+' | '+f['numero']:f['id'] for f in folios}
        selected=next((k for k,v in mapping.items() if v==old.get('folio_id')),next(iter(mapping)))
        name=self.store.rows('SELECT nombre FROM personas WHERE curp=?',(old.get('curp',''),))
        fields=[('folio','Folio del ciclo',selected,[selected] if ident else list(mapping)),('curp','CURP',old.get('curp','')),('nombre','Nombre',name[0]['nombre'] if name else ''),('legajo','Legajo',old.get('legajo',1)),('recibido','Fecha recibido (AAAA-MM-DD)',old.get('recibido','')),('fuera_broche','Hojas fuera del broche (incluidas en el total)',old.get('fuera_broche',0)),('carpetas','Carpetas verificadas',old.get('carpetas',0),['0','1']),('notas','Observaciones',old.get('notas','')),('motivo','Motivo','Alta' if not ident else '')]
        def submit(v):
            self.store.save_work(mapping[v.pop('folio')],v.pop('curp'),v.pop('nombre'),v.pop('legajo'),digitalizador=old.get('digitalizador',''),ident=ident,**v);self.refresh()
        Form(self,'Ciclo de digitalización · expediente maestro CURP + legajo',fields,submit)

    def detail(self,ident):
        w=self.store.one('trabajos',ident);win=tk.Toplevel(self);win.title('Expediente '+w['curp']+' · legajo '+str(w['legajo']));win.geometry('1000x660')
        nb=ttk.Notebook(win);nb.pack(fill='both',expand=True,padx=10,pady=10)
        pages={}
        for name in ('Conteo','Incidencias','Etapas e historial','Métricas TIFF'):
            p=ttk.Frame(nb,padding=10);nb.add(p,text=name);pages[name]=p
        p=pages['Conteo'];total=tk.StringVar();ttk.Label(p,textvariable=total,style='Title.TLabel').pack(anchor='w')
        ttk.Label(p,text='Incluye en los bloques todas las hojas físicas, también las que están fuera del broche.').pack(anchor='w')
        bar=self.bar(p);ttk.Label(bar,text='Hojas del bloque:').pack(side='left');qty=ttk.Entry(bar,width=12);qty.pack(side='left',padx=5)
        table=Table(p,['id','cantidad','nota','activo','creado'])
        def reload():
            table.fill(self.store.rows('SELECT * FROM conteos WHERE trabajo_id=? ORDER BY id',(ident,)))
            total.set('Suma de bloques: {}   |   Total confirmado: {}'.format(self.store.count_total(ident) or 0,self.store.one('trabajos',ident)['fisicos']))
            self.refresh()
        def add():self.store.add_count(ident,qty.get());qty.delete(0,'end');reload();qty.focus_set()
        self.button(bar,'Agregar (Enter)',add);qty.bind('<Return>',lambda e:self.safe(add))
        def edit(remove=False):
            cid=table.selected();row=self.store.one('conteos',cid)
            def submit(v):self.store.edit_count(cid,v['cantidad'],v['motivo'],remove);reload()
            Form(win,'Anular bloque' if remove else 'Corregir bloque',[('cantidad','Cantidad',row['cantidad']),('motivo','Motivo','')],submit)
        self.button(bar,'Corregir',edit);self.button(bar,'Anular bloque',lambda:edit(True))
        def confirm():
            count=self.store.confirm_count(ident);reload();messagebox.showinfo('Conteo guardado','Total físico confirmado: '+str(count)+'. Avanza las etapas en Etapas e historial.',parent=win)
        self.button(bar,'Confirmar total',confirm);table.pack(fill='both',expand=True);reload();qty.focus_set()
        p=pages['Incidencias'];bar=self.bar(p);inc=Table(p,['id','codigo_snapshot','documento','problema','accion','estado','creado'])
        def reload_inc():inc.fill(self.store.rows('SELECT * FROM incidencias WHERE trabajo_id=? ORDER BY id',(ident,)));self.refresh()
        def incident_form(iid=None):
            old=self.store.one('incidencias',iid) if iid else {}
            cats=self.store.rows("SELECT * FROM catalogos WHERE tipo='incidencia' AND (activo=1 OR id=?) ORDER BY codigo",(old.get('catalogo_id',-1),))
            mapping={'Sin catálogo':None};mapping.update({c['codigo']:c['id'] for c in cats})
            chosen=next((k for k,v in mapping.items() if v==old.get('catalogo_id')),'Sin catálogo')
            def submit(v):
                self.store.save_incident(ident,mapping[v.pop('catalogo')],ident=iid,**v);reload_inc()
            Form(win,'Incidencia',[('catalogo','Tipo',chosen,list(mapping)),('documento','Código / nombre del documento',old.get('documento','')),('problema','Problema observado',old.get('problema','')),('accion','Acción realizada',old.get('accion','')),('estado','Estado',old.get('estado','Abierta'),['Abierta','Resuelta','Anulada']),('motivo','Motivo','Registro de incidencia' if not iid else '')],submit)
        self.button(bar,'Nueva incidencia',incident_form);self.button(bar,'Editar / resolver / anular',lambda:incident_form(inc.selected()));inc.pack(fill='both',expand=True);reload_inc()
        p=pages['Etapas e historial'];bar=self.bar(p)
        state=tk.StringVar(value=w['estado']);ttk.Combobox(bar,textvariable=state,values=STATES,state='readonly',width=28).pack(side='left')
        hist=Table(p,['id','estado','inicio','fin','motivo','operador'])
        def reload_hist():hist.fill(self.store.rows('SELECT * FROM historial WHERE trabajo_id=? ORDER BY id',(ident,)));self.refresh()
        def change():
            reason=simpledialog.askstring('Cambio de etapa','Motivo; si retrocedes, explica la reapertura:',parent=win)
            if reason:self.store.change_state(ident,state.get(),reason);reload_hist()
        self.button(bar,'Aplicar etapa',change)
        ttk.Label(p,text='Avanza una etapa a la vez. Puedes retroceder con motivo. Las fechas se registran al aplicar el cambio.').pack(anchor='w',pady=8)
        hist.pack(fill='both',expand=True);reload_hist()
        p=pages['Métricas TIFF'];txt=tk.Text(p,wrap='word');txt.pack(fill='both',expand=True)
        e=self.store.latest(ident)
        text='Sin inventario de legajo vinculado. Abre Reportes TIFF, revisa la ruta y confirma folio/legajo/alcance.'
        if e:
            payload=json.loads(e['payload']);text='Último inventario vinculado: '+e['fecha']+'\n\n'+'\n'.join(k+': '+str(v) for k,v in payload.items())
        txt.insert('1.0',text);txt.configure(state='disabled')

    def setup_dashboard(self):
        from .dashboard_ui import DashboardPanel
        self.bi=DashboardPanel(self.pages['Indicadores'],self);self.kpi=self.bi.metrics;self.chart=self.bi.stages
    def export(self):
        dest=self.store.workspace.reports/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        self.store.export([w for w in self.filtered() if w['activo']],dest);messagebox.showinfo('Exportación',str(dest)+'\ntrabajos e indicadores: filtrados. Tablas de historial: completas.')
    def legacy_setup_kanban(self):
        p=self.pages['Kanban'];ttk.Label(p,text='Tareas de proceso. Su estado no cambia automáticamente el estado documental. Doble clic para editar.').pack(anchor='w')
        self.button(self.bar(p),'Nueva tarea',lambda:self.task_form())
        self.button(self.bar(p),'Ver tareas y desactivar / reactivar',self.task_list)
        frame=ttk.Frame(p);frame.pack(fill='both',expand=True);self.boards={}
        for i,state in enumerate(TASK_STATES):
            col=ttk.LabelFrame(frame,text=state,padding=3);col.grid(row=0,column=i,sticky='nsew',padx=3);frame.columnconfigure(i,weight=1)
            table=Table(col,['id','titulo']);table.pack(fill='both',expand=True);table.tree.column('id',width=35);table.tree.column('titulo',width=135)
            table.tree.bind('<Double-1>',lambda e,t=table:self.safe(lambda:self.task_form(t.selected())))
            self.boards[state]=table
        frame.rowconfigure(0,weight=1)
    def task_list(self):
        win=tk.Toplevel(self);win.title('Todas las tareas');win.geometry('900x500')
        bar=self.bar(win);table=Table(win,['id','titulo','estado','trabajo_id','activo'])
        def toggle():
            self.toggle('tareas',table.selected());table.fill(self.store.rows('SELECT * FROM tareas ORDER BY id'))
        self.button(bar,'Desactivar / reactivar',toggle);table.pack(fill='both',expand=True);table.fill(self.store.rows('SELECT * FROM tareas ORDER BY id'))

    def task_form(self,ident=None):
        old=self.store.one('tareas',ident) if ident else {}
        def submit(v):
            work_value=v.pop('work');work=int(work_value) if work_value else None
            self.store.save_task(work=work,ident=ident,**v);self.refresh()
        Form(self,'Tarea auxiliar (no cambia etapa documental)',[('titulo','Título',old.get('titulo','')),('estado','Estado de tarea',old.get('estado','Pendiente'),TASK_STATES),('work','ID del ciclo (opcional)',old.get('trabajo_id','')),('notas','Notas',old.get('notas','')),('motivo','Motivo','Actualización de tarea')],submit)

    def legacy_setup_folios(self):
        p=self.pages['Folios'];bar=self.bar(p)
        self.button(bar,'Nuevo folio',lambda:self.folio_form());self.button(bar,'Editar',lambda:self.folio_form(self.folio_table.selected()));self.button(bar,'Desactivar / reactivar',lambda:self.toggle('folios',self.folio_table.selected()))
        self.folio_table=Table(p,['id','numero','fecha_recepcion','responsable','activo']);self.folio_table.pack(fill='both',expand=True)
    def folio_form(self,ident=None):
        old=self.store.one('folios',ident) if ident else {}
        def submit(v):self.store.save_folio(ident=ident,**v);self.refresh()
        Form(self,'Folio',[('numero','Número con año',old.get('numero','')),('fecha','Fecha real de recepción',old.get('fecha_recepcion','')),('responsable','Responsable',old.get('responsable',''),{'store':self.store,'kind':'persona'}),('motivo','Motivo','Alta de folio' if not ident else '')],submit)
    def setup_catalog(self):
        p=self.pages['Catálogos'];bar=self.bar(p)
        from .directory_ui import directory_window
        self.button(bar,'Áreas / personas / sistemas / ubicaciones',lambda:directory_window(self,self.store))
        bar=self.bar(p)
        self.cat_filter=tk.StringVar(value='documento');ttk.Combobox(bar,textvariable=self.cat_filter,values=['documento','incidencia'],state='readonly',width=14).pack(side='left')
        self.cat_search=tk.StringVar();ttk.Entry(bar,textvariable=self.cat_search,width=25).pack(side='left',padx=4)
        self.button(bar,'Buscar',self.refresh);self.button(bar,'Nuevo',lambda:self.catalog_form());self.button(bar,'Editar',lambda:self.catalog_form(self.cat_table.selected()));self.button(bar,'Desactivar / reactivar',lambda:self.toggle('catalogos',self.cat_table.selected()))
        self.cat_table=Table(p,['id','codigo','carpeta','titulo','descripcion','accion','activo']);self.cat_table.pack(fill='both',expand=True)
    def catalog_form(self,ident=None):
        old=self.store.one('catalogos',ident) if ident else {};kind=old.get('tipo',self.cat_filter.get())
        fields=[('codigo','Código',old.get('codigo','')),('carpeta','Carpeta',old.get('carpeta',''),['','PERSONALES','FEDERAL']),('titulo','Documento / nombre de incidencia',old.get('titulo','')),('descripcion','Descripción / problema',old.get('descripcion','')),('accion','Acción sugerida',old.get('accion','')),('motivo','Motivo','Alta de catálogo' if not ident else '')]
        def submit(v):self.store.save_catalog(kind,ident=ident,**v);self.refresh()
        Form(self,'Catálogo de '+kind,fields,submit)
    def setup_reports(self):
        p=self.pages['Reportes TIFF'];ttk.Label(p,text='Revisa la ruta y el alcance antes de asignar. CURP completa no alimenta los totales por legajo.').pack(anchor='w')
        bar=self.bar(p);self.button(bar,'Ver 66 campos',self.report_detail);self.button(bar,'Vincular / corregir vínculo',self.bind_report)
        self.report_table=Table(p,['id','curp','fecha','trabajo_id','ambito','archivos','paginas','resultado','vigencia','ruta']);self.report_table.pack(fill='both',expand=True)
    def report_detail(self):
        row=self.store.one('ejecuciones',self.report_table.selected());win=tk.Toplevel(self);win.title('Reporte TIFF');win.geometry('900x650');text=tk.Text(win,wrap='word');text.pack(fill='both',expand=True)
        text.insert('1.0','\n'.join(k+': '+str(v) for k,v in json.loads(row['payload']).items()));text.configure(state='disabled')
    def bind_report(self):
        ident=self.report_table.selected();row=self.store.one('ejecuciones',ident)
        candidates=self.store.rows('SELECT t.id,f.numero,t.legajo FROM trabajos t JOIN folios f ON f.id=t.folio_id WHERE t.curp=? AND t.activo=1',(row['curp'],))
        mapping={'Sin trabajo':None};mapping.update({'{} | folio {} | legajo {}'.format(c['id'],c['numero'],c['legajo']):c['id'] for c in candidates})
        selected=next((k for k,v in mapping.items() if v==row['trabajo_id']),'Sin trabajo')
        def submit(v):
            if v['ambito']!='Sin asignar' and mapping[v['work']] is None:raise ValueError('Selecciona el trabajo correcto.')
            self.store.bind_execution(ident,mapping[v['work']],v['ambito'],v['motivo']);self.refresh()
        Form(self,'Confirmar alcance del inventario',[('work','Trabajo',selected,list(mapping)),('ambito','El inventario corresponde a',row['ambito'],['Sin asignar','Legajo','CURP completa']),('motivo','Evidencia / motivo de asignación','')],submit)
    def setup_import(self):
        p=self.pages['Importación y respaldo'];bar=self.bar(p)
        self.button(bar,'Importar lista de folio (Excel / CSV)',self.import_loan_list)
        bar=self.bar(p)
        self.button(bar,'1. Importar Excel inicial',self.load_excel);self.button(bar,'2. Importar CSV TIFF',self.load_csv);self.button(bar,'Respaldar base y TIFF',self.backup);self.button(bar,'Ver bitácora',self.audit_view)
        self.button(self.bar(p),'Crear ciclo histórico sin folio comprobado',self.legacy_cycle_form)
        ttk.Label(p,text='Excel: solo en una base sin trabajos. CSV: admite nuevas ejecuciones sin duplicar las ya importadas.').pack(anchor='w')
        bar=self.bar(p);self.button(bar,'Ver fuente de pendiente',self.pending_detail);self.button(bar,'Marcar pendiente revisado',self.resolve_pending)
        self.pending_table=Table(p,['id','tipo','detalle','estado']);self.pending_table.pack(fill='both',expand=True)
    def load_excel(self):
        path=filedialog.askopenfilename(title='Selecciona CONTROL_EXPEDIENTES.xlsx',initialdir=str(ROOT),filetypes=[('Excel','*.xlsx')])
        if path:
            if not messagebox.askyesno('Importación inicial','Se conservarán todas las filas originales. Los estados quedarán en Recibido hasta revisar los hitos históricos. ¿Importar?',parent=self):return
            self.store.backup();report=import_excel(self.store,path);self.refresh();messagebox.showinfo('Importación',json.dumps(report,ensure_ascii=False,indent=2))
    def load_csv(self):
        path=filedialog.askopenfilename(title='CSV de C:\\Reportes o copia adjunta',initialdir=str(ROOT/'fuentes'),filetypes=[('CSV','*.csv')])
        if path:
            self.store.backup();report=import_csv(self.store,path);self.refresh();messagebox.showinfo('Importación',json.dumps(report,ensure_ascii=False,indent=2)+'\nAsigna el alcance desde Reportes TIFF.')
    def backup(self):messagebox.showinfo('Respaldo completo creado',str(self.store.backup(full=True)))
    def pending_detail(self):
        row=self.store.one('pendientes',self.pending_table.selected());data=self.store.rows('SELECT * FROM origen WHERE id=?',(row['origen_id'],))
        win=tk.Toplevel(self);win.title('Fuente original');win.geometry('900x500');text=tk.Text(win,wrap='word');text.pack(fill='both',expand=True);text.insert('1.0',json.dumps(data,ensure_ascii=False,indent=2));text.configure(state='disabled')
    def resolve_pending(self):
        ident=self.pending_table.selected();reason=self.reason()
        if reason:
            with self.store.db:
                old=self.store.one('pendientes',ident);self.store.db.execute("UPDATE pendientes SET estado='Revisado' WHERE id=?",(ident,));self.store.audit('pendientes',ident,'revisar',old,self.store.one('pendientes',ident),reason)
            self.refresh()
    def audit_view(self):
        win=tk.Toplevel(self);win.title('Bitácora de cambios');win.geometry('1100x600');table=Table(win,['id','fecha','operador','entidad','registro','accion','motivo','antes','despues']);table.pack(fill='both',expand=True);table.fill(self.store.rows('SELECT * FROM auditoria ORDER BY id DESC'))
    def refresh(self):
        works=self.refresh_filtered(update_dashboard=False);self.bi.refresh(works)
        self.folio_table.fill(self.store.rows('SELECT * FROM folios ORDER BY numero'))
        search='%'+self.cat_search.get().strip()+'%'
        self.cat_table.fill(self.store.rows('SELECT * FROM catalogos WHERE tipo=? AND (codigo LIKE ? OR titulo LIKE ? OR descripcion LIKE ?) ORDER BY codigo',(self.cat_filter.get(),search,search,search)))
        self.refresh_board()
        reports=self.store.rows('SELECT * FROM ejecuciones ORDER BY fecha DESC,id DESC')
        for r in reports:
            last=self.store.latest(r['trabajo_id']) if r['trabajo_id'] else None
            r['vigencia']='Sin vigencia' if not r['valido'] else 'Actual' if last and last['id']==r['id'] else 'Histórico / sin asignar'
            data=json.loads(r['payload']);r.update(archivos=data['TOTAL_DIGITALES_TIFF'],paginas=data['TOTAL_PAG_DIGITALES_CONOCIDAS'],resultado=data['RESULTADO'],ruta=data['RUTA_EXPEDIENTE'])
        self.report_table.fill(reports);self.pending_table.fill(self.store.rows('SELECT * FROM pendientes ORDER BY id'))
        self.status.set('{} trabajos en la vista · {} reportes TIFF sin asignar · Operador: {}'.format(len(works),sum(r['ambito']=='Sin asignar' for r in reports),self.store.operador))
