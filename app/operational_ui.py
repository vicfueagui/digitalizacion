"""Pantallas operativas; las decisiones y validaciones permanecen en servicios."""
import json
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from .operations import Operations,KANBAN,CUSTODY
from .delivery import Deliveries
from .review import Reviews,OBSERVATION_TYPES
from .reporting import Reporting
from .legacy import LegacyImport


def readable(value,depth=0):
    if isinstance(value,dict):return '\n'.join('  '*depth+str(k)+': '+('\n'+readable(v,depth+1) if isinstance(v,(list,dict)) else str(v) if v is not None else 'Sin dato confirmado') for k,v in value.items())
    if isinstance(value,list):return '\n\n'.join(readable(v,depth) for v in value) or 'Sin registros'
    return str(value) if value is not None else 'Sin dato confirmado'


class SnapshotViewer(tk.Toplevel):
    """Evidencia de una entrega; no tiene acciones de edición."""
    def __init__(self,parent,path,page=1):
        super().__init__(parent);self.title('Evidencia de entrega · solo lectura');self.geometry('840x650')
        from .coding import page_info
        self.path=path;self.count=len(page_info(path,True));self.page=max(0,min(self.count-1,int(page or 1)-1))
        bar=ttk.Frame(self);bar.pack(fill='x');self.label=ttk.Label(bar);self.label.pack(side='left')
        ttk.Button(bar,text='Página anterior',command=lambda:self.show(-1)).pack(side='left')
        ttk.Button(bar,text='Página siguiente',command=lambda:self.show(1)).pack(side='left')
        self.canvas=tk.Canvas(self,background='#d9e1e4');self.canvas.pack(fill='both',expand=True);self.after(100,self.show)
    def show(self,delta=0):
        from .coding import render_page
        from .coding_v3 import preview_image
        from PIL import ImageTk
        self.page=max(0,min(self.count-1,self.page+delta));frame=render_page(self.path,self.page)
        width=max(300,self.canvas.winfo_width());height=max(300,self.canvas.winfo_height());ratio=min(width/frame.width,height/frame.height,1)
        preview=preview_image(frame,(max(1,int(frame.width*ratio)),max(1,int(frame.height*ratio))));frame.close()
        self.photo=ImageTk.PhotoImage(preview);preview.close();self.canvas.delete('all');self.canvas.create_image(width/2,height/2,image=self.photo)
        self.label.configure(text='Página {} de {} · {}'.format(self.page+1,self.count,self.path.name))


class OperationalUI:
    def form(self,title,fields,submit,parent=None):
        from .ui import Form
        fields=list(fields)
        for index,field in enumerate(fields):
            kind={'origen':'area','entrega':'persona','recibe':'persona','persona':'persona','responsable':'persona'}.get(field[0])
            if field[0]=='ubicacion' and 'original' in field[1].lower():kind='ubicacion'
            if kind and len(field)==3:fields[index]=tuple(field)+({'store':self.store,'kind':kind},)
        return Form(parent or self,title,fields,submit)

    def import_loan_list(self):
        from .intake_ui import ImportListWindow
        example=self.store.workspace.root/'ejemplos'
        path=filedialog.askopenfilename(parent=self,title='Lista de expedientes por folio',initialdir=str(example if example.exists() else self.store.workspace.root),filetypes=[('Excel / CSV','*.xlsx *.csv *.tsv'),('Todos','*.*')])
        if path:return ImportListWindow(self,path)

    def text_view(self,title,value,parent=None):
        win=tk.Toplevel(parent or self);win.title(title);win.geometry('880x620')
        text=tk.Text(win,wrap='word');scroll=ttk.Scrollbar(win,command=text.yview);text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');text.pack(fill='both',expand=True);text.insert('1.0',readable(value));text.configure(state='disabled')
        return win

    def setup_kanban(self):
        from .ui import Table
        page=self.pages['Kanban'];ttk.Label(page,text='Etapas derivadas del ciclo. Doble clic abre Expediente 360. La custodia física aparece por separado.').pack(anchor='w')
        self.board_filters={}
        for group in (('folio','digitalizador','responsable'),('custodia','prioridad','validacion','con_observaciones')):
            bar=self.bar(page)
            for key in group:
                ttk.Label(bar,text={'con_observaciones':'Observaciones'}.get(key,key.capitalize())).pack(side='left',padx=3)
                var=tk.StringVar();self.board_filters[key]=var
                choices={'custodia':['']+CUSTODY,'prioridad':['','Baja','Normal','Alta','Urgente'],'validacion':['','OK','OK con advertencias','REQUIERE REVISIÓN','BLOQUEANTE','Sin vigencia'],'con_observaciones':['','Sí','No']}.get(key)
                if choices:ttk.Combobox(bar,textvariable=var,values=choices,state='readonly',width=18).pack(side='left')
                else:ttk.Entry(bar,textvariable=var,width=17).pack(side='left')
        bar=self.bar(page);self.button(bar,'Aplicar filtros',self.refresh);self.button(bar,'Tareas auxiliares históricas',self.task_list)
        frame=ttk.Frame(page);frame.pack(fill='both',expand=True);self.boards={}
        ttk.Style(self).configure('Kanban.Treeview',rowheight=122)
        for i,state in enumerate(KANBAN):
            column=ttk.LabelFrame(frame,text=state,padding=2);column.grid(row=0,column=i,sticky='nsew',padx=2);frame.columnconfigure(i,weight=1)
            table=Table(column,['id','tarjeta']);table.tree.configure(style='Kanban.Treeview');table.tree.column('id',width=35);table.tree.column('tarjeta',width=185)
            table.pack(fill='both',expand=True);table.tree.bind('<Double-1>',lambda e,t=table:self.safe(lambda:self.summary_window(t.selected())))
            self.boards[state]=table
        frame.rowconfigure(0,weight=1)

    def refresh_board(self):
        cards=Reporting(self.store).cards(**{k:v.get().strip() for k,v in self.board_filters.items()})
        for row in cards:
            row['tarjeta']='{} · L{}\n{}\n{}\n{}\n{}\n{} TIFF · {} págs. · {} obs.\n{}'.format(row['curp'],row['legajo'],row['folio'],row['digitalizador'] or 'Por asignar',row['estado'],row['custodia'],row['tiff_activos'],row['paginas'],row['observaciones'],row['validacion'])
        for state,table in self.boards.items():table.fill([r for r in cards if r['columna']==state])

    def setup_folios(self):
        from .ui import Table
        page=self.pages['Folios'];bar=self.bar(page)
        self.button(bar,'Nuevo folio',lambda:self.folio_form());self.button(bar,'Editar datos básicos',lambda:self.folio_form(self.folio_table.selected()))
        self.button(bar,'Recepción / préstamo',lambda:self.loan_window(self.folio_table.selected()))
        self.button(bar,'Importar lista Excel / CSV',self.import_loan_list)
        self.folio_table=Table(page,['id','numero','area_origen','recepcion_at','recepcion_estado','entrega','recibe','responsable','activo']);self.folio_table.pack(fill='both',expand=True)
        self.folio_table.tree.bind('<Double-1>',lambda e:self.safe(lambda:self.loan_window(self.folio_table.selected())))

    def loan_window(self,folio):
        from .reception_ui import LoanWindow
        return LoanWindow(self,folio)

    def assignment_form(self,work=None,folio=None):
        def save(v):
            Operations(self.store).assign(v['persona'],v['motivo'],work,folio,v['rol'],v['colaborar']=='Sí');self.refresh()
        self.form('Asignación con historial',[('persona','Persona responsable',''),('rol','Rol','Digitalizador',['Digitalizador','Revisor','Responsable']),('colaborar','Añadir colaborador (sin sustituir)','No',['No','Sí']),('motivo','Motivo','')],save)

    def legacy_cycle_form(self):
        def save(v):
            ident=Operations(self.store).legacy_cycle(v['curp'],v['legajo'],v['nombre']);self.refresh();self.summary_window(ident)
        self.form('Expediente histórico sin folio confirmado',[('curp','CURP',''),('legajo','Legajo confirmado',''),('nombre','Nombre (opcional)','')],save)

    def metadata_form(self,work):
        w=self.store.one('trabajos',work)
        def save(v):Operations(self.store).card_metadata(work,v['nota'],v['prioridad'],v['etiqueta'],v['bloqueo'],v['fecha']);self.refresh()
        self.form('Nota y prioridad · no cambian etapa',[('nota','Nota',w['notas']),('prioridad','Prioridad',w['prioridad'],['Baja','Normal','Alta','Urgente']),('etiqueta','Etiqueta',w['etiqueta']),('bloqueo','Bloqueo / motivo',w['bloqueo']),('fecha','Fecha objetivo (AAAA-MM-DD)',w['fecha_objetivo'])],save)

    def summary_window(self,work):
        from .ui import Table
        d=Deliveries(self.store);reviews=Reviews(self.store);reporting=Reporting(self.store)
        w=self.store.one('trabajos',work);win=tk.Toplevel(self);win.title('Expediente 360 · '+w['curp']+' · L'+str(w['legajo']));win.geometry('1060x690')
        bar=self.bar(win);self.button(bar,'Conteo / incidencias / etapas',lambda:self.detail(work));self.button(bar,'Préstamo',lambda:self.loan_window(w['folio_id']))
        self.button(bar,'Asignar',lambda:self.assignment_form(work=work));self.button(bar,'Nota / prioridad',lambda:self.metadata_form(work))
        self.button(bar,'Legajos de esta CURP',lambda:self.legajos_view(work))
        nb=ttk.Notebook(win);nb.pack(fill='both',expand=True);pages={}
        for name in ('Resumen','Entregas','Observaciones','Importar carpeta CURP','Historial'):
            p=ttk.Frame(nb,padding=6);nb.add(p,text=name);pages[name]=p
        text=tk.Text(pages['Resumen'],wrap='word');text.pack(fill='both',expand=True)
        deliveries=Table(pages['Entregas'],['id','numero','estado','creado','operador','manifest_hash']);bar=self.bar(pages['Entregas'])
        observations=Table(pages['Observaciones'],['id','tipo','descripcion','estado','pagina','ubicacion_fisica','responsable','respuesta','entrega_detectada','entrega_resuelta'])
        history=Table(pages['Historial'],['fecha','operador','evento','motivo']);history.pack(fill='both',expand=True)
        def reload():
            data=reporting.summary(work);display={k:data[k] for k in ('Identificación','Custodia física','Asignaciones','Proceso','Conteo físico','Digital vigente','Dato legado declarado','Cambios de última entrega')}
            display['Validación actual']=data['Validación']['Resultado actual'];display['Advertencias / bloqueos']=data['Validación']['Problemas']
            text.configure(state='normal');text.delete('1.0','end');text.insert('1.0',readable(display));text.configure(state='disabled')
            deliveries.fill(data['Entregas']);observations.fill(data['Observaciones']);history.fill([dict(e,id=i) for i,e in enumerate(data['Línea de tiempo'])]);self.refresh()
        def prepare():d.prepare(work);reload();nb.select(pages['Entregas'])
        def approve():
            delivery=deliveries.selected()
            def save(v):reviews.approve(delivery,v['motivo']);reload()
            self.form('Aprobar entrega exacta',[('motivo','Evidencia de revisión completa','')],save,win)
        self.button(bar,'Preparar nueva entrega',prepare);self.button(bar,'Ver TIFF de entrega',lambda:self.delivery_view(deliveries.selected(),win))
        self.button(bar,'Iniciar revisión',lambda:(reviews.begin(deliveries.selected()),reload()))
        self.button(bar,'Aprobar',approve);self.button(bar,'Ver manifiesto',lambda:self.text_view('Manifiesto',d.verify(deliveries.selected()),win));deliveries.pack(fill='both',expand=True)
        def export_delivery():
            from pathlib import Path
            ident=deliveries.selected();row=d.get(ident)
            parent=filedialog.askdirectory(title='Carpeta contenedora: se creará una carpeta NUEVA por entrega',parent=win)
            if parent:
                target=d.export_copy(ident,Path(parent)/Path(row['ruta']).name)
                messagebox.showinfo('Entrega exportada','Carpeta nueva verificada:\n'+str(target)+'\nManifest hash: '+row['manifest_hash'],parent=win)
        self.button(self.bar(pages['Entregas']),'Exportar a carpeta nueva',export_delivery)
        bar=self.bar(pages['Observaciones'])
        def observe():
            delivery=deliveries.selected();sessions=self.store.rows('SELECT * FROM sesiones_revision WHERE entrega_id=? AND fin IS NULL ORDER BY inicio DESC',(delivery,))
            if not sessions:raise ValueError('Selecciona una entrega e inicia su revisión en Entregas.')
            manifest=d.verify(delivery);mapping={'Expediente completo / documento faltante':None};mapping.update({i['nombre_canonico']:i for i in manifest['items']})
            def save(v):
                item=mapping[v['documento']];reviews.observe(sessions[0]['id'],v['tipo'],v['descripcion'],v['responsable'],item['document_asset_id'] if item else None,item['file_version_id'] if item else None,int(v['pagina']) if v['pagina'] else None,v['ubicacion'],v['evidencia'],v['bloqueante']=='Sí');reload()
            self.form('Observación sobre entrega '+str(manifest['numero']),[('documento','Documento',next(iter(mapping)),list(mapping)),('pagina','Página TIFF (opcional)',''),('ubicacion','Ubicación física de la hoja',''),('tipo','Tipo',OBSERVATION_TYPES[0],OBSERVATION_TYPES),('descripcion','Descripción',''),('responsable','Responsable de corregir',''),('evidencia','Evidencia / referencia',''),('bloqueante','Impide aprobación final','Sí',['Sí','No'])],save,win)
        def response():
            ident=observations.selected();versions={'Sin entrega':None};versions.update({'Entrega '+str(r['numero'])+' · '+r['estado']:r['id'] for r in self.store.rows("SELECT * FROM entregas WHERE trabajo_id=? AND estado NOT IN ('Preparando','Incompleta') ORDER BY numero",(work,))})
            def save(v):reviews.update_observation(ident,v['estado'],v['respuesta'],versions[v['entrega']]);reload()
            self.form('Respuesta / validación explícita',[('estado','Nuevo estado','En corrección',['En corrección','Resuelta','Validada','Anulada','Abierta']),('entrega','Entrega donde se corrigió','Sin entrega',list(versions)),('respuesta','Respuesta / evidencia','')],save,win)
        self.button(bar,'Nueva sobre entrega seleccionada',observe);self.button(bar,'Responder / validar',response);self.button(bar,'Ver evidencia exacta',lambda:self.observation_evidence(observations.selected(),win));observations.pack(fill='both',expand=True)
        legacy=LegacyImport(self.store);preflight=[None];p=pages['Importar carpeta CURP'];bar=self.bar(p);result=tk.Text(p,wrap='word')
        ttk.Label(p,text='Primero analizar; no se mueve, renombra ni borra el origen. Registrar análisis deja archivos externos; adoptar crea copias verificadas.',wraplength=980).pack(anchor='w')
        def analyze():
            source=filedialog.askdirectory(title='Carpeta CURP histórica',parent=win)
            if not source:return
            preflight[0]=legacy.preflight(work,source);result.configure(state='normal');result.delete('1.0','end');result.insert('1.0',readable(preflight[0]));result.configure(state='disabled')
        def register(adopt):
            if not preflight[0]:raise ValueError('Analiza primero la carpeta y revisa el diagnóstico.')
            if not messagebox.askyesno('Confirmar incorporación','¿Copiar los TIFF al almacenamiento gestionado?' if adopt else '¿Registrar este diagnóstico manteniendo los archivos externos?',parent=win):return
            legacy.register(work,preflight[0],adopt);reload()
        self.button(bar,'1. Analizar carpeta',analyze);self.button(bar,'2. Registrar análisis',lambda:register(False));self.button(bar,'2. Adoptar copias / reanudar',lambda:register(True));result.pack(fill='both',expand=True)
        bottom=self.bar(win);self.button(bottom,'Actualizar resumen',reload);self.button(bottom,'Validar expediente',lambda:(self.text_view('Reporte de confianza',d.validate(work),win),reload()))
        self.button(bottom,'Exportar 360 imprimible',lambda:messagebox.showinfo('Reporte HTML',str(reporting.export_summary(work)),parent=win))
        if w['conciliacion_pendiente']:
            def reconcile():
                def save(v):Operations(self.store).confirm_legacy_link(work,v['motivo']);reload()
                self.form('Confirmar vínculo histórico sin fusionar',[('motivo','Evidencia de identidad CURP + legajo y ciclo','')],save,win)
            self.button(self.bar(win),'Confirmar vínculo histórico con el maestro',reconcile)
        reload();win._reload_operational=reload
        return win

    def delivery_view(self,delivery,parent=None):
        from .ui import Table
        d=Deliveries(self.store);manifest=d.verify(delivery);root=self.store.workspace.path(d.get(delivery)['ruta'])
        win=tk.Toplevel(parent or self);win.title('Entrega {} · TIFF inmutables'.format(manifest['numero']));win.geometry('950x550')
        table=Table(win,['id','nombre_canonico','codigo','carpeta','paginas','document_asset_id','file_version_id']);bar=self.bar(win)
        items={i['archivo_id']:i for i in manifest['items']}
        def view():d.verify(delivery);SnapshotViewer(win,root/items[table.selected()]['ruta'])
        self.button(bar,'Ver TIFF de esta entrega',view);table.pack(fill='both',expand=True);table.fill([dict(i,id=i['archivo_id']) for i in manifest['items']])
        table.tree.bind('<Double-1>',lambda e:self.safe(view));return win

    def observation_evidence(self,ident,parent=None):
        row=self.store.rows('SELECT * FROM observaciones_revision WHERE id=?',(ident,))[0]
        d=Deliveries(self.store);manifest=d.verify(row['entrega_detectada'])
        item=next((i for i in manifest['items'] if i['file_version_id']==row['version_id']),None)
        if not item:return self.text_view('Observación de expediente',row,parent)
        root=self.store.workspace.path(d.get(row['entrega_detectada'])['ruta'])
        return SnapshotViewer(parent or self,root/item['ruta'],row['pagina'] or 1)
