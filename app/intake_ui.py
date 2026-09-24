"""Vista previa y correspondencia de columnas para listas de préstamos."""
import tkinter as tk
from tkinter import ttk,messagebox
from .intake import LoanLists,read_tables,detect_header,infer_mapping,FIELDS
from .directory_ui import DirectoryPicker


class ImportListWindow(tk.Toplevel):
    def __init__(self,parent,path):
        from .ui import Table
        tables=read_tables(path)
        if not tables:raise ValueError('No hay hojas con datos.')
        super().__init__(parent);self.parent=parent;self.path=path;self.service=LoanLists(parent.store);self.plan=None
        self.title('Importar lista de expedientes por folio');self.geometry('{}x{}'.format(min(1180,self.winfo_screenwidth()-60),min(780,self.winfo_screenheight()-100)));self.minsize(840,580)
        self.tables=tables
        ttk.Label(self,text='1. Revisa las columnas  →  2. Actualiza la vista previa  →  3. Confirma la importación',padding=8).pack(anchor='w')
        top=ttk.Frame(self,padding=(8,0));top.pack(fill='x')
        self.sheet=tk.StringVar(value=next(iter(self.tables)));self.header=tk.StringVar()
        ttk.Label(top,text='Hoja').pack(side='left');sheet=ttk.Combobox(top,textvariable=self.sheet,values=list(self.tables),state='readonly',width=24);sheet.pack(side='left',padx=5)
        ttk.Label(top,text='Fila de encabezado').pack(side='left');ttk.Entry(top,textvariable=self.header,width=6).pack(side='left',padx=4)
        ttk.Button(top,text='Leer encabezados',command=lambda:self.safe(self.columns)).pack(side='left',padx=5)
        defaults=ttk.Frame(self,padding=8);defaults.pack(fill='x')
        self.folio=tk.StringVar();self.legajo=tk.StringVar();self.area=tk.StringVar()
        ttk.Label(defaults,text='Folio si falta').grid(row=0,column=0,sticky='w');ttk.Entry(defaults,textvariable=self.folio,width=15).grid(row=0,column=1,padx=5)
        ttk.Label(defaults,text='Legajo si falta (vacío = pendiente)').grid(row=0,column=2,sticky='w');ttk.Entry(defaults,textvariable=self.legajo,width=5).grid(row=0,column=3,padx=5)
        ttk.Label(defaults,text='Área de origen si falta').grid(row=1,column=0,sticky='w',pady=4)
        DirectoryPicker(defaults,parent.store,'area',self.area).grid(row=1,column=1,columnspan=3,sticky='ew')
        self.mapping_frame=ttk.LabelFrame(self,text='Correspondencia de encabezados',padding=6);self.mapping_frame.pack(fill='x',padx=8)
        self.mapping_vars={};self.mapping_choices={}
        self.table=Table(self,['id','resultado','fila','folio','curp','nombre','legajo','sistema','solicitud','integra','trabajado','detalle']);self.table.pack(fill='both',expand=True,padx=8,pady=6)
        self.table.tree.configure(displaycolumns=('fila','resultado','folio','curp','nombre','legajo','detalle'))
        for col,width in [('fila',40),('resultado',110),('folio',80),('curp',175),('nombre',210),('legajo',50),('detalle',330)]:self.table.tree.column(col,width=width,minwidth=35)
        self.summary=tk.StringVar(value='Selecciona las columnas correspondientes.');ttk.Label(self,textvariable=self.summary,wraplength=1080,padding=8).pack(fill='x')
        actions=ttk.Frame(self,padding=8);actions.pack(fill='x')
        ttk.Button(actions,text='Actualizar vista previa',command=lambda:self.safe(self.preview)).pack(side='left',padx=4)
        self.confirm=ttk.Button(actions,text='Confirmar importación',command=lambda:self.safe(self.commit));self.confirm.pack(side='left',padx=4)
        self.receipt_folio=None
        self.next_button=ttk.Button(actions,text='Continuar con recepción',state='disabled',command=lambda:self.safe(lambda:self.parent.loan_window(self.receipt_folio)));self.next_button.pack(side='left',padx=4)
        ttk.Button(actions,text='Cerrar',command=self.destroy).pack(side='right')
        ttk.Label(self,text='No. es consecutivo. La fecha de solicitud no es recepción. TRABAJADOS se conserva como dato declarado.',padding=(8,0,8,8)).pack(anchor='w')
        sheet.bind('<<ComboboxSelected>>',lambda e:self.new_sheet())
        for variable in (self.header,self.folio,self.legajo,self.area):variable.trace_add('write',self.invalidate)
        self.new_sheet()
    def safe(self,action):
        import sqlite3
        try:self.configure(cursor='watch');self.update_idletasks();return action()
        except (ValueError,OSError,sqlite3.Error) as error:messagebox.showerror('Importar lista',str(error),parent=self)
        finally:
            if self.winfo_exists():self.configure(cursor='')
    def invalidate(self,*args):
        self.plan=None;self.confirm.configure(state='disabled')
        self.receipt_folio=None;self.next_button.configure(state='disabled')
    def new_sheet(self):
        self.header.set(str(detect_header(self.tables[self.sheet.get()])));self.safe(self.columns)
    def columns(self):
        try:number=int(self.header.get())
        except ValueError:raise ValueError('Indica el número de fila del encabezado.')
        headers=next((values for n,values in self.tables[self.sheet.get()] if n==number),None)
        if headers is None:raise ValueError('Fila de encabezados inexistente.')
        for widget in self.mapping_frame.winfo_children():widget.destroy()
        choices={'No usar esta columna':None};choices.update({'{} · {}'.format(i+1,h or '(sin título)'):i for i,h in enumerate(headers)})
        self.mapping_choices=choices;self.mapping_vars={};mapping=infer_mapping(headers)
        for i,(field,title) in enumerate(FIELDS.items()):
            row=i//2;col=(i%2)*2
            ttk.Label(self.mapping_frame,text=title).grid(row=row,column=col,sticky='w',padx=4,pady=2)
            var=tk.StringVar(value=next((k for k,v in choices.items() if v==mapping.get(field)),next(iter(choices))))
            combo=ttk.Combobox(self.mapping_frame,textvariable=var,values=list(choices),state='readonly',width=36);combo.grid(row=row,column=col+1,sticky='ew',padx=4,pady=2)
            self.mapping_frame.columnconfigure(col+1,weight=1);self.mapping_vars[field]=var;var.trace_add('write',self.invalidate)
        self.invalidate()
        if 'curp' in mapping and ('folio' in mapping or self.folio.get()):self.preview()
        else:self.summary.set('No se reconocieron las columnas obligatorias. Asocia CURP y Folio y actualiza la vista previa.')
    def options(self):
        return {'sheet':self.sheet.get(),'header_row':int(self.header.get()),'mapping':{k:self.mapping_choices[v.get()] for k,v in self.mapping_vars.items() if self.mapping_choices[v.get()] is not None},
                'default_folio':self.folio.get().strip(),'default_legajo':self.legajo.get().strip() or None,'area':self.area.get().strip()}
    def preview(self):
        plan=self.service.preview(self.path,**self.options());self.plan=plan
        rows=[]
        for row in plan['filas']:
            rows.append(dict(row['datos'],id=row['fila'],fila=row['fila'],resultado='Por revisar' if row['errores'] else 'Legajo pendiente' if row['datos']['legajo'] is None else 'Importable',detalle='; '.join(row['errores']+row['advertencias'])))
        self.table.fill(rows);self.summary.set('{} filas válidas · {} por revisar · {} sin legajo. Las filas con errores se conservan como pendientes; no se crean identidades falsas.'.format(plan['validas'],plan['por_revisar'],plan['sin_legajo']))
        self.confirm.configure(state='normal')
    def commit(self):
        if self.plan is None:raise ValueError('Actualiza primero la vista previa.')
        self.receipt_folio=None;self.next_button.configure(state='disabled')
        result=self.service.commit(self.plan);self.parent.refresh();self.confirm.configure(state='disabled')
        messagebox.showinfo('Lista registrada',('Este archivo y configuración ya estaban importados.\n' if result['ya_importado'] else '')+
            'Folios nuevos: {folios_nuevos}\nElementos nuevos: {elementos_nuevos}\nCiclos registrados: {ciclos_nuevos}\nYa registrados: {duplicados}\nFilas por revisar: {por_revisar}\nLegajos pendientes: {sin_legajo}\n\nContinúa con recepción: selecciona los físicos cotejados y pulsa Aceptar seleccionados. No necesitas recapturar CURP.'.format(**result),parent=self)
        self.parent.tabs.select(self.parent.pages['Folios'])
        folios=self.parent.store.rows('SELECT DISTINCT folio_id FROM lista_registros WHERE lista_id=? AND folio_id IS NOT NULL',(result['lista_id'],))
        if len(folios)==1:
            self.receipt_folio=folios[0]['folio_id'];self.parent.folio_table.tree.selection_set(str(self.receipt_folio));self.next_button.configure(state='normal')
