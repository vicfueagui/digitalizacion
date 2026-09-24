"""Panel BI adaptable, cifras explícitas y exploración del detalle de cada barra."""
import datetime
import tkinter as tk
from tkinter import ttk,messagebox
from tkinter import font as tkfont
from .core import STATES
from .dashboard import Dashboard

INK='#173c4c'
MUTED='#456170'
PAPER='#f5f8fa'


def number(value):return '{:,}'.format(value).replace(',',' ')
def pct(value):return 'Sin base' if value is None else ('{:.1f}%'.format(value).replace('.',','))


class BarChart(tk.Canvas):
    """Redibuja datos ya calculados al ajustar el tamaño; no consulta la base."""
    def __init__(self,parent,on_select):
        super().__init__(parent,background=PAPER,highlightthickness=0,height=240,takefocus=True)
        self.rows=[];self.on_select=on_select;self.job=None;self.focus_row=0;self.regions=[]
        self.bind('<Configure>',lambda e:self.schedule())
        self.bind('<Button-1>',self.choose);self.bind('<Return>',self.enter)
        self.bind('<Down>',lambda e:self.move(1));self.bind('<Up>',lambda e:self.move(-1))
        self.bind('<FocusIn>',lambda e:self.schedule());self.bind('<FocusOut>',lambda e:self.schedule())
    def set_rows(self,rows):self.rows=rows;self.schedule()
    def schedule(self):
        if self.job:self.after_cancel(self.job)
        self.job=self.after_idle(self.draw)
    def draw(self):
        self.job=None;self.delete('all');self.regions=[]
        width=max(self.winfo_width(),260);height=max(self.winfo_height(),200)
        if not self.rows:return
        step=min(40,(height-10)/len(self.rows));label_width=min(140,width*.36);right=width-10
        # Cifra y porcentaje ocupan una banda propia: nunca quedan encima de la barra.
        value_font=tkfont.Font(self,font=('TkDefaultFont',10,'bold'))
        value_width=max(value_font.measure('{} · {}'.format(number(r['value']),pct(r['percent']))) for r in self.rows)
        bar_left=label_width+10;bar_right=max(bar_left+10,right-max(105,value_width+10))
        for i,row in enumerate(self.rows):
            y=8+i*step;total=row['total'];ratio=row['value']/total if total else 0
            self.create_text(8,y+step/2,text=row['label'],anchor='w',width=label_width-8,fill=INK,font=('TkDefaultFont',10),tags=('label',))
            self.create_rectangle(bar_left,y+step/2-6,bar_right,y+step/2+6,fill='#dce5eb',outline='')
            if ratio:self.create_rectangle(bar_left,y+step/2-6,bar_left+(bar_right-bar_left)*ratio,y+step/2+6,fill=row['color'],outline='')
            self.create_text(right,y+step/2,text='{} · {}'.format(number(row['value']),pct(row['percent'])),anchor='e',fill=INK,font=('TkDefaultFont',10,'bold'),tags=('value',))
            if self.focus_get()==self and i==self.focus_row:self.create_rectangle(3,y+1,width-3,y+step-1,outline='#267e78',dash=(2,2),tags=('focus',))
            self.regions.append((y,y+step))
    def choose(self,event):
        self.focus_set()
        for i,(top,bottom) in enumerate(self.regions):
            if top<=event.y<bottom:self.focus_row=i;self.schedule();self.on_select(self.rows[i]);break
    def enter(self,event=None):
        if self.rows:self.on_select(self.rows[self.focus_row])
    def move(self,delta):
        if self.rows:self.focus_row=max(0,min(len(self.rows)-1,self.focus_row+delta));self.schedule()
        return 'break'
    def destroy(self):
        if self.job:self.after_cancel(self.job)
        super().destroy()


class DashboardPanel(ttk.Frame):
    def __init__(self,parent,app):
        from .ui import Table
        super().__init__(parent);self.app=app;self.service=Dashboard(app.store);self.data=None
        self.pack(fill='both',expand=True)
        filters=ttk.Frame(self);filters.pack(fill='x',pady=(0,4))
        for col,(key,title,width) in enumerate([('texto','CURP / nombre',22),('folio','Folio',13),('digitalizador','Digitalizador',20),('estado','Estado',21)]):
            box=ttk.Frame(filters);box.grid(row=0,column=col,sticky='ew',padx=(0,8));filters.columnconfigure(col,weight=1)
            ttk.Label(box,text=title).pack(anchor='w')
            widget=ttk.Combobox(box,textvariable=app.filters[key],values=['']+STATES,state='readonly',width=width) if key=='estado' else ttk.Entry(box,textvariable=app.filters[key],width=width)
            widget.pack(fill='x')
        second=ttk.Frame(self);second.pack(fill='x',pady=(0,5))
        ttk.Label(second,text='Recibido desde').pack(side='left');ttk.Entry(second,textvariable=app.filters['desde'],width=11).pack(side='left',padx=4)
        ttk.Label(second,text='hasta').pack(side='left');ttk.Entry(second,textvariable=app.filters['hasta'],width=11).pack(side='left',padx=4)
        ttk.Button(second,text='Limpiar',command=app.clear_filters).pack(side='left',padx=3)
        ttk.Button(second,text='Actualizar',command=lambda:app.safe(lambda:self.refresh(app.filtered()))).pack(side='left',padx=3)
        ttk.Button(second,text='Exportar indicadores',command=lambda:app.safe(self.export)).pack(side='right')
        self.scope=tk.StringVar();self.scope_label=ttk.Label(self,textvariable=self.scope,wraplength=1000,foreground=MUTED);self.scope_label.pack(anchor='w',pady=(0,4))
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True)
        overview=ttk.Frame(self.tabs);details=ttk.Frame(self.tabs,padding=6);metrics=ttk.Frame(self.tabs,padding=6)
        for title,frame in [('Resumen',overview),('Por folio / digitalizador',details),('Todos los indicadores',metrics)]:self.tabs.add(frame,text=title)
        self.scroll=tk.Canvas(overview,background=PAPER,highlightthickness=0);yscroll=ttk.Scrollbar(overview,command=self.scroll.yview)
        self.scroll.configure(yscrollcommand=yscroll.set);yscroll.pack(side='right',fill='y');self.scroll.pack(fill='both',expand=True)
        self.body=ttk.Frame(self.scroll,padding=8);self.body_id=self.scroll.create_window(0,0,window=self.body,anchor='nw')
        self.body.bind('<Configure>',lambda e:self.scroll.configure(scrollregion=self.scroll.bbox('all')))
        self.scroll.bind('<Configure>',lambda e:self.scroll.itemconfigure(self.body_id,width=e.width))
        cards=ttk.Frame(self.body);cards.pack(fill='x');self.cards={}
        for i,(key,title) in enumerate([('Trabajos activos','Expedientes vigentes'),('CURP distintas','CURP distintas'),('Archivos TIFF','TIFF activos'),('Páginas conocidas','Páginas registradas')]):
            card=ttk.LabelFrame(cards,text=title,padding=(10,5));card.grid(row=0,column=i,sticky='nsew',padx=3);cards.columnconfigure(i,weight=1,uniform='cards')
            value=tk.StringVar(value='—');ttk.Label(card,textvariable=value,font=('TkDefaultFont',23,'bold'),foreground=INK).pack(anchor='w');self.cards[key]=value
        charts=ttk.Frame(self.body);charts.pack(fill='both',expand=True,pady=8)
        for i,(title,key) in enumerate([('Etapas del proceso','stages'),('Cobertura del trabajo','coverage')]):
            frame=ttk.LabelFrame(charts,text=title,padding=4);frame.grid(row=0,column=i,sticky='nsew',padx=3);charts.columnconfigure(i,weight=1,uniform='charts')
            chart=BarChart(frame,self.drill);chart.pack(fill='both',expand=True);setattr(self,key,chart)
        ttk.Label(self.body,text='Cada porcentaje usa los expedientes de esta vista como base. Selecciona una barra para ver su detalle.',wraplength=900,foreground=MUTED).pack(anchor='w')
        self.alert=tk.StringVar();ttk.Label(self.body,textvariable=self.alert,wraplength=970,padding=(0,8)).pack(anchor='w')
        pending=ttk.Frame(self.body);pending.pack(fill='x');self.pending=tk.StringVar()
        ttk.Label(pending,textvariable=self.pending,wraplength=610).pack(side='left',fill='x',expand=True)
        ttk.Button(pending,text='Ir a recepción en Folios',command=lambda:app.tabs.select(app.pages['Folios'])).pack(side='right')
        # Rueda solo en el resumen; las tablas conservan su desplazamiento nativo.
        def wheel(event):
            delta=event.delta
            if delta:self.scroll.yview_scroll(-1 if delta>0 else 1,'units')
            return 'break'
        def bind_wheel(widget):
            widget.bind('<MouseWheel>',wheel,add='+')
            widget.bind('<Button-4>',lambda e:self.scroll.yview_scroll(-1,'units'))
            widget.bind('<Button-5>',lambda e:self.scroll.yview_scroll(1,'units'))
            for child in widget.winfo_children():bind_wheel(child)
        bind_wheel(self.body);self.scroll.bind('<MouseWheel>',wheel)
        groupbar=ttk.Frame(details);groupbar.pack(fill='x');self.group=tk.StringVar(value='Folio')
        ttk.Label(groupbar,text='Agrupar por').pack(side='left')
        combo=ttk.Combobox(groupbar,textvariable=self.group,values=['Folio','Digitalizador'],state='readonly',width=20);combo.pack(side='left',padx=8);combo.bind('<<ComboboxSelected>>',lambda e:self.group_rows())
        ttk.Button(groupbar,text='Ver expedientes del grupo',command=lambda:app.safe(self.group_detail)).pack(side='right')
        self.group_table=Table(details,['id','grupo','expedientes','aceptados','tiff','paginas','cerrados','cierre']);self.group_table.pack(fill='both',expand=True,pady=6)
        self.group_table.tree.configure(displaycolumns=('grupo','expedientes','aceptados','tiff','paginas','cerrados','cierre'))
        for key,title,width in [('grupo','Grupo',200),('expedientes','Expedientes',90),('aceptados','Aceptados',85),('tiff','TIFF',65),('paginas','Páginas',85),('cerrados','Cerrados',85),('cierre','Cierre %',85)]:
            self.group_table.tree.heading(key,text=title);self.group_table.tree.column(key,width=width,minwidth=55,stretch=key=='grupo')
        self.group_table.tree.bind('<Double-1>',lambda e:app.safe(self.group_detail))
        self.metrics=Table(metrics,['indicador','valor']);self.metrics.pack(fill='both',expand=True)
        self.metrics.tree.column('indicador',width=420,anchor='w');self.metrics.tree.heading('indicador',text='Indicador');self.metrics.tree.heading('valor',text='Valor')
        self.metrics_note=ttk.Label(metrics,text='TIFF y páginas corresponden al inventario activo. No se suman entregas ni cifras legadas declaradas; el cierre mostrado es el estado registrado.',wraplength=920);self.metrics_note.pack(anchor='w',pady=6)
        self.wrap_width=None;self.bind('<Configure>',lambda e:self.fit_labels(e.width))

    def fit_labels(self,width):
        if width==self.wrap_width:return
        self.wrap_width=width;self.scope_label.configure(wraplength=max(260,width-12));self.metrics_note.configure(wraplength=max(260,width-32))
        for widget in self.body.winfo_children():
            if isinstance(widget,ttk.Label):widget.configure(wraplength=max(260,width-48))

    def refresh(self,works):
        filters={k:v.get().strip() for k,v in self.app.filters.items()};self.data=self.service.snapshot(works,filters)
        for key,var in self.cards.items():var.set(number(self.data['metrica'][key]))
        self.stages.set_rows(self.data['etapas']);self.coverage.set_rows(self.data['cobertura'])
        total=len(self.data['expedientes']);stamp=self.data['generado'][11:19]
        self.scope.set('{} expedientes activos · {} · actualizado {}. Filtros compartidos con Expedientes.'.format(total,'Vista filtrada' if any(filters.values()) else 'Todos los ciclos vigentes',stamp))
        if getattr(self.app,'filter_date_hint',''):self.scope.set(self.scope.get()+' '+self.app.filter_date_hint)
        m=self.data['metrica'];self.alert.set('{} incidencias · {} observaciones abiertas · {} sin conteo · {} inventarios desactualizados. Consulta la validación del contenido en Expediente 360.'.format(m['Incidencias abiertas'],m['Observaciones abiertas'],m['Sin conteo confirmado'],m['Inventarios desactualizados']))
        self.pending.set('Fuera de Expedientes: {} elementos aún sin ciclo · total del espacio, independiente de estos filtros.'.format(self.data['sin_ciclo_global']))
        self.metrics.fill([{'id':i,'indicador':k,'valor':'Sin base' if v is None else pct(v) if k.endswith('(%)') else number(v)} for i,(k,v) in enumerate(m.items())]);self.group_rows()
    def group_rows(self):
        if self.data is None:return
        self.group_data=self.data['grupos']['folio' if self.group.get()=='Folio' else 'digitalizador']
        self.group_table.fill([dict(r,id=i,cierre=pct(r['cierre'])) for i,r in enumerate(self.group_data)])
    def group_detail(self):
        row=self.group_data[self.group_table.selected()];self.drill({'label':row['grupo'],'ids':row['ids']})
    def drill(self,row):
        from .ui import Table
        win=tk.Toplevel(self);win.title('Indicadores · '+row['label']);win.geometry('1010x510')
        selected=set(row['ids']);rows=[dict(r,tiff=r['total_tiff'],paginas=r['total_paginas']) for r in self.data['expedientes'] if r['id'] in selected]
        ttk.Label(win,text='{} · {} expedientes del ámbito mostrado'.format(row['label'],len(rows)),padding=8).pack(anchor='w')
        table=Table(win,['id','curp','nombre','folio','legajo','estado','tiff','paginas','digitalizador']);table.pack(fill='both',expand=True)
        table.tree.configure(displaycolumns=('curp','nombre','folio','legajo','estado','tiff','paginas','digitalizador'));table.fill(rows)
        ttk.Button(win,text='Abrir Expediente 360',command=lambda:self.app.safe(lambda:self.app.summary_window(table.selected()))).pack(anchor='e',padx=8,pady=8)
        table.tree.bind('<Double-1>',lambda e:self.app.safe(lambda:self.app.summary_window(table.selected())))
        return win
    def export(self):
        self.refresh(self.app.filtered())
        path=self.app.store.workspace.reports/('indicadores_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        self.service.export(self.data,path);messagebox.showinfo('Indicadores exportados',str(path)+'\nIncluye cifras, etapas, grupos, expedientes y filtros de esta vista.',parent=self)
