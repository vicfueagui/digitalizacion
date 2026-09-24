"""Recepción por selección con confirmación visual; las diferencias se revisan aparte."""
import tkinter as tk
import sqlite3
from tkinter import ttk,messagebox
from .directory import normalized
from .operations import Operations,CUSTODY
from .reception import Reception


class ReceiptConfirmation(tk.Toplevel):
    def __init__(self,parent,items):
        from .ui import Table
        super().__init__(parent);self.loan=parent;self.service=Reception(parent.app.store);self.items=list(items)
        self.title('Confirmar recepción · '+parent.number);self.geometry('900x540');self.minsize(760,460)
        self.transient(parent);self.previous_grab=self.grab_current();self.grab_set()
        ttk.Label(self,text='Revisa los expedientes seleccionados. Sus CURP se toman de la lista importada.',padding=10).pack(anchor='w')
        self.table=Table(self,['id','curp_esperada','nombre','legajo_propuesto','resultado']);self.table.pack(fill='both',expand=True,padx=10)
        self.table.tree.configure(displaycolumns=('curp_esperada','nombre','legajo_propuesto','resultado'))
        for key,title,width in [('curp_esperada','CURP de la lista',180),('nombre','Nombre',270),('legajo_propuesto','Legajo a recibir',100),('resultado','Comprobación',150)]:
            self.table.tree.heading(key,text=title);self.table.tree.column(key,width=width,minwidth=65,stretch=key=='nombre')
        options=ttk.Frame(self,padding=10);options.pack(fill='x')
        self.legajo=tk.StringVar(value='1');self.confirmed=tk.BooleanVar(value=False);self.reason=tk.StringVar()
        ttk.Label(options,text='Legajo para registros que no lo indican:').grid(row=0,column=0,sticky='w')
        self.legajo_entry=ttk.Entry(options,textvariable=self.legajo,width=6);self.legajo_entry.grid(row=0,column=1,sticky='w',padx=6)
        ttk.Label(options,text='Los legajos ya indicados se conservan. Puedes añadir otros físicos después.',wraplength=710).grid(row=1,column=0,columnspan=2,sticky='w',pady=4)
        self.summary=tk.StringVar();ttk.Label(self,textvariable=self.summary,wraplength=840,padding=(10,4)).pack(fill='x')
        ttk.Checkbutton(self,text='He cotejado estos expedientes físicos y confirmo las CURP y legajos mostrados.',variable=self.confirmed,command=self.check).pack(anchor='w',padx=10,pady=6)
        note=ttk.Frame(self,padding=(10,0));note.pack(fill='x');ttk.Label(note,text='Nota / acuse (opcional)').pack(side='left')
        ttk.Entry(note,textvariable=self.reason).pack(side='left',fill='x',expand=True,padx=8)
        buttons=ttk.Frame(self,padding=10);buttons.pack(fill='x')
        self.accept_button=ttk.Button(buttons,text='Aceptar y crear expedientes',command=self.save);self.accept_button.pack(side='left')
        ttk.Button(buttons,text='Cancelar',command=self.destroy).pack(side='right')
        self.rows=[];self.error='';self.legajo.trace_add('write',self.preview);self.preview()
        self.bind('<Escape>',lambda e:self.destroy())

    def preview(self,*args):
        self.confirmed.set(False);self.error=''
        try:
            self.rows=self.service.preview(self.loan.folio,self.items,self.legajo.get())
            self.table.fill(self.rows);unknown=sum(r['legajo_nuevo'] for r in self.rows)
            self.legajo_entry.configure(state='normal' if unknown else 'disabled')
            blocked=[r for r in self.rows if r['errores']]
            self.error='; '.join(blocked[0]['errores']) if blocked else ''
            self.summary.set(self.error or '{} seleccionados · {} ya aceptados · {} sin legajo en origen: se confirmarán con el número mostrado.'.format(len(self.rows),sum(r['validacion']=='Aceptado' for r in self.rows),unknown))
        except ValueError as error:self.error=str(error);self.summary.set(self.error)
        self.check()

    def check(self):self.accept_button.configure(state='normal' if self.confirmed.get() and not self.error else 'disabled')
    def save(self):
        try:
            reason='Recepción física cotejada con las CURP y legajos de la selección.'
            if self.reason.get().strip():reason+=' '+self.reason.get().strip()
            result=self.service.accept(self.loan.folio,self.items,reason,self.confirmed.get(),self.legajo.get())
            self.loan.reload(True);self.loan.notice.set('{} aceptados · {} ya aceptados. Los {} expedientes están disponibles en Expedientes.'.format(result['aceptados'],result['ya_aceptados'],len(result['ciclos'])))
            self.destroy()
        except (ValueError,OSError,sqlite3.Error) as error:messagebox.showerror('Recepción',str(error),parent=self)
    def destroy(self):
        previous=getattr(self,'previous_grab',None);super().destroy()
        if previous:
            try:
                if previous.winfo_exists():previous.grab_set()
            except tk.TclError:pass


class LoanWindow(tk.Toplevel):
    def __init__(self,app,folio):
        from .ui import Table
        from .file_browser import FlowBar
        super().__init__(app);self.app=app;self.folio=folio;self.ops=Operations(app.store)
        self.number=app.store.one('folios',folio)['numero'];self.title('Recepción y custodia · '+self.number);self.geometry('1080x660');self.minsize(840,540)
        ttk.Label(self,text='Folio '+self.number,font=('TkDefaultFont',16,'bold'),padding=(10,8)).pack(anchor='w')
        ttk.Label(self,text='Selecciona los físicos cotejados y acepta sin recapturar CURP. Puedes aceptar uno, varios o toda la lista visible.',wraplength=1000,padding=(10,0)).pack(anchor='w')
        bar=FlowBar(self);bar.pack(fill='x',padx=8,pady=5)
        for title,action in [('Aceptar seleccionados',self.accept_selected),('Seleccionar visibles',self.select_visible),('Revisar diferencia',self.review),('Ver en Expedientes',self.show_works)]:
            bar.add(ttk.Button(bar,text=title,command=lambda fn=action:app.safe(fn)))
        more=ttk.Menubutton(bar,text='Más acciones ▾');menu=tk.Menu(more,tearoff=False);more.configure(menu=menu);bar.add(more)
        for title,action in [('Registrar entrega / recepción del folio',self.receive),('Registrar / añadir legajos',self.legajos),('Añadir expediente esperado',self.expected),('Recibido no relacionado',self.unlisted),('Abrir expediente seleccionado',self.open_work),('Asignar ciclos del folio',lambda:app.assignment_form(folio=folio)),('Registrar devolución / custodia',self.custody)]:
            menu.add_command(label=title,command=lambda fn=action:app.safe(fn))
        filters=ttk.Frame(self,padding=(10,0));filters.pack(fill='x');self.query=tk.StringVar();self.state=tk.StringVar(value='Todos')
        ttk.Label(filters,text='CURP / nombre').pack(side='left');ttk.Entry(filters,textvariable=self.query,width=28).pack(side='left',padx=6)
        ttk.Combobox(filters,textvariable=self.state,values=['Todos','Pendiente','Aceptado','Discrepancia','Faltante'],state='readonly',width=15).pack(side='left')
        ttk.Label(filters,text='Shift: rango · Ctrl / Cmd: varios').pack(side='right')
        self.table=Table(self,['id','curp_esperada','nombre','legajo_esperado','validacion','custodia','sistema_declarado','fecha_solicitud','integra_declarado','ubicacion_original','discrepancia'])
        self.table.tree.configure(selectmode='extended',displaycolumns=('curp_esperada','nombre','legajo_esperado','validacion','custodia','sistema_declarado'))
        for key,title,width in [('curp_esperada','CURP',180),('nombre','Nombre',240),('legajo_esperado','Legajo',65),('validacion','Recepción',115),('custodia','Custodia',180),('sistema_declarado','Sistema',95)]:
            self.table.tree.heading(key,text=title);self.table.tree.column(key,width=width,minwidth=50,stretch=key=='nombre')
        self.table.pack(fill='both',expand=True,padx=10,pady=7)
        self.table.tree.bind('<<TreeviewSelect>>',lambda e:self.selection_label())
        self.table.tree.bind('<Control-a>',self.select_visible)
        if self.tk.call('tk','windowingsystem')=='aqua':self.table.tree.bind('<Command-a>',self.select_visible)
        self.table.tree.bind('<Double-1>',lambda e:app.safe(self.accept_selected))
        self.count=tk.StringVar();self.notice=tk.StringVar(value='La aceptación crea el ciclo en Expedientes. La devolución física se registra por separado.')
        ttk.Label(self,textvariable=self.count,padding=(10,0)).pack(anchor='w')
        ttk.Label(self,textvariable=self.notice,wraplength=1010,padding=10).pack(fill='x')
        for var in (self.query,self.state):var.trace_add('write',lambda *args:self.reload())
        self.reload()

    def reload(self,notify=False):
        rows=self.app.store.rows('SELECT i.*,p.nombre FROM prestamo_items i LEFT JOIN personas p ON p.curp=i.curp_esperada WHERE folio_id=? ORDER BY i.id',(self.folio,))
        self.total=len(rows);selected=self.table.tree.selection();needle=normalized(self.query.get())
        visible=[r for r in rows if needle in normalized(r['curp_esperada']+' '+(r['nombre'] or '')) and (self.state.get()=='Todos' or r['validacion']==self.state.get())]
        self.table.fill(visible);self.table.tree.selection_set([i for i in selected if self.table.tree.exists(i)]);self.selection_label()
        if notify:self.app.refresh()
    def selection_label(self):self.count.set('{} en el folio · {} visibles · {} seleccionados'.format(self.total,len(self.table.tree.get_children()),len(self.table.tree.selection())))
    def select_visible(self,event=None):self.table.tree.selection_set(self.table.tree.get_children());return 'break'
    def one(self):
        if len(self.table.tree.selection())!=1:raise ValueError('Selecciona un solo elemento para esta acción.')
        return self.table.selected()
    def accept_selected(self):
        ids=[int(i) for i in self.table.tree.selection()]
        if not ids:raise ValueError('Selecciona los expedientes que cotejaste; puedes usar Seleccionar visibles.')
        return ReceiptConfirmation(self,ids)
    def receive(self):
        row=self.app.store.one('folios',self.folio)
        def save(v):self.ops.receive_folio(self.folio,v['origen'],v['entrega'],v['recibe'],v['acuse'],v['fecha'] or None);self.reload(True)
        return self.app.form('Recepción del folio',[('origen','Área de origen',row['area_origen']),('entrega','Entrega',row['entrega']),('recibe','Recibe',row['recibe']),('acuse','Referencia de firma/acuse',row['acuse']),('fecha','Fecha/hora ISO (vacío = ahora)',row['recepcion_at'])],save,self)
    def review(self):
        item=self.one();row=self.app.store.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0]
        def save(v):
            self.ops.validate_item(item,v['decision'],v['curp'],v['legajo'],v['motivo'],v['extra']=='Sí')
            if v['decision']=='Aceptado':self.ops.create_cycle(item)
            self.reload(True)
        return self.app.form('Revisar diferencia / faltante',[('decision','Resultado',row['validacion'],['Pendiente','Aceptado','Discrepancia','Faltante']),('curp','CURP recibida',row['curp_recibida'] or row['curp_esperada']),('legajo','Legajo recibido',row['legajo_recibido'] or row['legajo_esperado']),('extra','Aceptar extra tras aclaración','No',['No','Sí']),('motivo','Evidencia / discrepancia',row['discrepancia'])],save,self)
    def legajos(self):
        from .intake import register_legajos
        item=self.one()
        def save(v):register_legajos(self.app.store,item,v['legajos'],v['motivo']);self.reload(True)
        return self.app.form('Registrar físicos de la misma CURP',[('legajos','Legajos separados por comas (ej. 1,2,3)',''),('motivo','Evidencia del desglose físico','')],save,self)
    def expected(self):
        def save(v):self.ops.expect(self.folio,v['curp'],v['legajo'],v['ubicacion'],v['nombre']);self.reload(True)
        return self.app.form('Expediente esperado',[('curp','CURP',''),('legajo','Legajo',''),('nombre','Nombre',''),('ubicacion','Ubicación original','')],save,self)
    def unlisted(self):
        def save(v):self.ops.unlisted(self.folio,v['curp'],v['legajo'],v['motivo'],v['ubicacion']);self.reload(True)
        return self.app.form('Recibido fuera de lista',[('curp','CURP recibida',''),('legajo','Legajo recibido',''),('ubicacion','Ubicación original',''),('motivo','Discrepancia / evidencia','')],save,self)
    def custody(self):
        item=self.one()
        def save(v):self.ops.custody(item,v['estado'],v['motivo'],v['recibe']);self.reload(True)
        return self.app.form('Movimiento físico',[('estado','Custodia','En devolución',CUSTODY),('recibe','Quién recibe/acepta devolución',''),('motivo','Motivo / evidencia','')],save,self)
    def open_work(self):
        work=self.ops.create_cycle(self.one());self.reload(True);self.app.summary_window(work)
    def show_works(self):
        for var in self.app.filters.values():var.set('')
        self.app.filters['folio'].set(self.number);self.app.refresh_filtered();self.app.tabs.select(self.app.pages['Expedientes']);self.destroy()
