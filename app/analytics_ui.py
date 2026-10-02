"""Cubo exploratorio y barras de los grupos visibles, sin bibliotecas externas."""
import datetime
import tkinter as tk
from tkinter import ttk,messagebox
from .analytics import Cube,PERIODS,DIMENSIONS,SOURCES


class CubePanel(ttk.Frame):
    def __init__(self,parent,app,dashboard):
        super().__init__(parent,padding=8);self.app=app;self.dashboard=dashboard;self.service=Cube(app.store);self.data=None;self.works=[]
        from .ui import Table
        from .dashboard_ui import BarChart
        self.options={};bar=ttk.Frame(self);bar.pack(fill='x')
        for key,label,values in [('source','Medida temporal',SOURCES),('period','Periodo',PERIODS),('dimension','Agrupar por',DIMENSIONS)]:
            ttk.Label(bar,text=label).pack(side='left',padx=4);var=tk.StringVar(value=values[0] if key!='period' else 'Mes');self.options[key]=var
            combo=ttk.Combobox(bar,textvariable=var,values=values,state='readonly',width=24 if key=='source' else 16);combo.pack(side='left');combo.bind('<<ComboboxSelected>>',lambda e:app.safe(self.refresh))
        bar=ttk.Frame(self,padding=(0,6));bar.pack(fill='x')
        for key,label in [('start','Desde'),('end','Hasta')]:
            ttk.Label(bar,text=label+' (AAAA-MM-DD)').pack(side='left');var=tk.StringVar();self.options[key]=var
            entry=ttk.Entry(bar,textvariable=var,width=12);entry.pack(side='left',padx=5);entry.bind('<Return>',lambda e:app.safe(self.refresh))
        ttk.Button(bar,text='Aplicar fechas',command=lambda:app.safe(self.refresh)).pack(side='left',padx=5)
        ttk.Button(bar,text='Exportar cubo',command=lambda:app.safe(self.export)).pack(side='right')
        self.summary=tk.StringVar();ttk.Label(self,textvariable=self.summary,wraplength=960).pack(fill='x',pady=5)
        self.table=Table(self,['id','periodo','grupo','expedientes','integraciones','hojas','pendientes','tiff','paginas']);self.table.pack(fill='both',expand=True)
        self.table.tree.configure(displaycolumns=('periodo','grupo','expedientes','integraciones','hojas','pendientes','tiff','paginas'))
        for col,title,width in [('periodo','Periodo',90),('grupo','Grupo',180),('expedientes','Expedientes',90),('integraciones','Integraciones',90),('hojas','Hojas confirmadas',115),('pendientes','Sin conteo',85),('tiff','TIFF',65),('paginas','Páginas',65)]:
            self.table.tree.heading(col,text=title);self.table.tree.column(col,width=width,minwidth=55,stretch=col=='grupo')
        self.table.tree.bind('<Double-1>',lambda e:app.safe(self.detail));self.table.tree.bind('<Return>',lambda e:app.safe(self.detail))
        self.chart=BarChart(self,lambda row:self.drill(row['ids'],row['label']));self.chart.configure(height=170);self.chart.pack(fill='x')
        ttk.Label(self,text='Barras: 5 grupos con más páginas y su proporción del total visible. Doble clic en una celda abre expedientes.\nLas fechas son de recepción o importación registrada; nunca se suman copias de entregas.',wraplength=970).pack(fill='x')
    def refresh(self,works=None):
        if works is not None:self.works=works
        self.data=self.service.snapshot(self.works,**{k:v.get().strip() for k,v in self.options.items()})
        rows=self.data['filas'];activity=self.data['fuente']==SOURCES[1]
        self.table.fill([dict(r,**{k:'No aplica' for k in ('hojas','pendientes','integraciones')}) if activity else r for r in rows])
        t=self.data['totales'];self.summary.set('{} expedientes distintos · {} TIFF · {} páginas · {} registros sin fecha ({} excluidos por fechas).\n{} · Se aplican también los filtros generales de Expedientes.'.format(t['expedientes_distintos'],t['tiff'],t['paginas'],self.data['sin_fecha'],self.data['sin_fecha_excluidos'],self.data['fuente']))
        total=t['paginas'];ordered=sorted(rows,key=lambda r:r['paginas'],reverse=True)[:5]
        self.chart.set_rows([dict(label=r['periodo']+' / '+r['grupo'],value=r['paginas'],total=total,percent=round(r['paginas']*100/total,1) if total else None,color='#B3282A',ids=r['ids']) for r in ordered])
    def detail(self):
        r=self.data['filas'][self.table.selected()];return self.drill(r['ids'],r['periodo']+' · '+r['grupo'])
    def drill(self,ids,title):return self.dashboard.drill({'ids':ids,'label':title})
    def export(self):
        self.refresh()
        folder=self.app.store.workspace.reports/('cubo_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        self.service.export(self.data,folder);messagebox.showinfo('Cubo exportado',str(folder),parent=self)
