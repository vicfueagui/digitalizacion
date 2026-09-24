"""Explorador TIFF local: detalles/lista y miniaturas virtuales de la primera página."""
import math
import sys
import tkinter as tk
from tkinter import ttk
from collections import OrderedDict
from .ui import Table


class FlowBar(ttk.Frame):
    """Herramientas legibles que pasan a otra fila cuando cambia el ancho."""
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs);self.items=[];self.job=None
        self.bind('<Configure>',lambda e:self.schedule())
    def add(self,widget):
        self.items.append(widget);self.schedule();return widget
    def schedule(self):
        if self.job:self.after_cancel(self.job)
        self.job=self.after_idle(self.layout)
    def layout(self):
        self.job=None;width=max(100,self.winfo_width());row=0;x=0;col=0
        for widget in self.items:
            needed=widget.winfo_reqwidth()+4
            if x and x+needed>width:row+=1;x=0;col=0
            widget.grid(row=row,column=col,sticky='w',padx=2,pady=2)
            x+=needed;col+=1
    def destroy(self):
        if self.job:self.after_cancel(self.job)
        super().destroy()


class FileBrowser(ttk.Frame):
    def __init__(self,parent,service,on_select):
        super().__init__(parent);self.service=service;self.rows=[];self.cache=OrderedDict();self.photos=[]
        self.job=None;self.paint_job=None;self.columns=1;self.cell_height=200
        self.mode=tk.StringVar(value='Detalles');self.size=tk.IntVar(value=128);self.count=tk.StringVar(value='Sin archivos')
        bar=ttk.Frame(self);bar.pack(fill='x',pady=(0,3))
        ttk.Label(bar,text='Archivos',font='TkHeadingFont').pack(side='left')
        mode=ttk.Combobox(bar,textvariable=self.mode,values=['Detalles','Lista','Miniaturas'],state='readonly',width=11)
        mode.pack(side='right');mode.bind('<<ComboboxSelected>>',lambda e:self.change_view())
        self.size_bar=ttk.Frame(self)
        ttk.Label(self.size_bar,text='Tamaño').pack(side='left')
        ttk.Scale(self.size_bar,from_=64,to=224,variable=self.size,command=lambda v:self.schedule()).pack(side='left',fill='x',expand=True)
        ttk.Label(self.size_bar,text='Ctrl + rueda').pack(side='right')
        self.body=ttk.Frame(self);self.body.pack(fill='both',expand=True)
        self.table=Table(self.body,['id','nombre','paginas','fecha','codigo','estado']);self.tree=self.table.tree
        self.tree.configure(displaycolumns=('nombre','paginas','codigo','estado','fecha'),selectmode='browse')
        for name,width,title in [('nombre',190,'Archivo'),('paginas',48,'Págs.'),('codigo',65,'Código'),('estado',90,'Estado'),('fecha',125,'Fecha')]:
            self.tree.column(name,width=width,minwidth=40,stretch=name=='nombre');self.tree.heading(name,text=title)
        self.table.pack(fill='both',expand=True)
        self.grid_frame=ttk.Frame(self.body)
        self.canvas=tk.Canvas(self.grid_frame,background='#eef2f5',highlightthickness=0,takefocus=True,yscrollincrement=24)
        scroll=ttk.Scrollbar(self.grid_frame,command=self.scroll)
        self.canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda e:self.schedule())
        self.canvas.bind('<MouseWheel>',self.wheel)
        self.canvas.bind('<Button-4>',lambda e:self.wheel(e,1));self.canvas.bind('<Button-5>',lambda e:self.wheel(e,-1))
        self.canvas.bind('<Button-1>',self.click)
        for key,delta in [('Left',-1),('Right',1),('Up',-1),('Down',1)]:
            self.canvas.bind('<'+key+'>',lambda e,k=key,d=delta:self.move(d*self.columns if k in ('Up','Down') else d))
        self.tree.bind('<<TreeviewSelect>>',on_select)
        self.tree.bind('<<TreeviewSelect>>',lambda e:self.schedule(),add='+')
        ttk.Label(self,textvariable=self.count,anchor='w').pack(fill='x',pady=3)
        saved=service.store.rows("SELECT value FROM meta WHERE key='visor_archivos'")
        if saved:
            parts=saved[0]['value'].split(',')
            if parts[0] in ('Detalles','Lista','Miniaturas'):self.mode.set(parts[0])
            try:self.size.set(max(64,min(224,int(parts[-1]))))
            except ValueError:pass
        self.change_view()

    def selected(self):return self.table.selected()
    def fill(self,rows):
        self.rows=rows;self.table.fill(rows);self.count.set('{} TIFF · {} páginas'.format(len(rows),sum(r['paginas'] for r in rows)))
        self.schedule()
    def change_view(self):
        self.table.pack_forget();self.grid_frame.pack_forget();self.size_bar.pack_forget()
        if self.mode.get()=='Miniaturas':
            self.size_bar.pack(fill='x',before=self.body,pady=(0,4));self.grid_frame.pack(fill='both',expand=True)
        else:
            self.tree.configure(displaycolumns=('nombre','paginas','codigo','estado','fecha') if self.mode.get()=='Detalles' else ('nombre',))
            self.table.pack(fill='both',expand=True)
        self.schedule();self.see_selected()
    def save_preferences(self):
        with self.service.store.db:self.service.store.db.execute("INSERT OR REPLACE INTO meta VALUES('visor_archivos',?)",(self.mode.get()+','+str(int(self.size.get())),))
    def schedule(self):
        if self.job:self.after_cancel(self.job)
        self.job=self.after(60,self.layout)
    def layout(self):
        self.job=None
        if self.mode.get()!='Miniaturas':return
        size=int(self.size.get());width=max(100,self.canvas.winfo_width())
        self.columns=max(1,width//(size+20));self.cell_width=width/self.columns;self.cell_height=size+66
        self.canvas.configure(scrollregion=(0,0,width,max(1,math.ceil(len(self.rows)/self.columns)*self.cell_height)))
        self.draw()
    def scroll(self,*args):self.canvas.yview(*args);self.schedule_draw()
    def schedule_draw(self):
        if self.paint_job:self.after_cancel(self.paint_job)
        self.paint_job=self.after(30,self.draw)
    def wheel(self,event,direction=None):
        delta=direction if direction is not None else event.delta if sys.platform=='darwin' else event.delta/120.
        if not delta:return 'break'
        if event.state & 4:
            self.size.set(max(64,min(224,int(self.size.get())+(16 if delta>0 else -16))));self.schedule()
        else:
            self.canvas.yview_scroll(-max(1,min(5,round(abs(delta))))*(1 if delta>0 else -1),'units');self.schedule_draw()
        return 'break'
    def thumbnail(self,row,size):
        from PIL import Image,ImageTk
        key=(row['id'],row['hash_actual'],row['ruta'],size)
        if key in self.cache:self.cache.move_to_end(key);return self.cache[key]
        photo=None
        try:
            # Solo página 1, un archivo por vez; nunca decodificar el lote entero.
            with Image.open(str(self.service.path(row['ruta']))) as im:
                im.seek(0);im.thumbnail((size-12,size-12))
                converted=im.convert('RGB')
                try:photo=ImageTk.PhotoImage(converted,master=self)
                finally:converted.close()
        except (OSError,ValueError,RuntimeError,Image.DecompressionBombError):pass
        self.cache[key]=photo
        while len(self.cache)>48:self.cache.popitem(last=False)
        return photo
    def draw(self):
        self.paint_job=None
        if self.mode.get()!='Miniaturas' or not hasattr(self,'cell_width'):return
        self.canvas.delete('all');self.photos=[]
        top=max(0,self.canvas.canvasy(0));height=self.canvas.winfo_height();size=int(self.size.get())
        start=max(0,int(top//self.cell_height)*self.columns)
        end=min(len(self.rows),(int((top+height)//self.cell_height)+2)*self.columns)
        selected=self.tree.selection();chosen=int(selected[0]) if selected else None
        for index in range(start,end):
            row=self.rows[index];x=(index%self.columns)*self.cell_width;y=(index//self.columns)*self.cell_height
            active=row['id']==chosen;tag='file:'+str(row['id'])
            self.canvas.create_rectangle(x+3,y+3,x+self.cell_width-3,y+self.cell_height-3,fill='#d9eaf9' if active else '#ffffff',outline='#3177ad' if active else '#d6dfe6',width=2 if active else 1,tags=tag)
            photo=self.thumbnail(row,size)
            if photo:
                self.photos.append(photo);self.canvas.create_image(x+self.cell_width/2,y+size/2+7,image=photo,tags=tag)
            else:self.canvas.create_text(x+self.cell_width/2,y+size/2,text='TIFF\nSin miniatura',fill='#677784',justify='center',tags=tag)
            label=row['nombre']
            if len(label)>34:label=label[:22]+'…'+label[-9:]
            self.canvas.create_text(x+self.cell_width/2,y+size+11,text=label,width=self.cell_width-12,anchor='n',justify='center',tags=tag)
            self.canvas.create_text(x+self.cell_width/2,y+self.cell_height-13,text='{} pág. · {}'.format(row['paginas'],row['codigo'] or 'Sin código'),fill='#526574',tags=tag)
    def click(self,event):
        self.canvas.focus_set()
        index=int(self.canvas.canvasy(event.y)//self.cell_height)*self.columns+int(event.x//getattr(self,'cell_width',1))
        if 0<=index<len(self.rows):self.tree.selection_set(str(self.rows[index]['id']))
    def move(self,delta):
        ids=[r['id'] for r in self.rows];selected=self.tree.selection()
        if ids:
            index=ids.index(int(selected[0])) if selected and int(selected[0]) in ids else 0
            self.tree.selection_set(str(ids[max(0,min(len(ids)-1,index+delta))]))
        return 'break'
    def see_selected(self):
        if self.mode.get()!='Miniaturas':return
        ids=[r['id'] for r in self.rows];selected=self.tree.selection()
        if not selected or int(selected[0]) not in ids:return
        y=(ids.index(int(selected[0]))//self.columns)*self.cell_height
        total=max(1,math.ceil(len(ids)/self.columns)*self.cell_height)
        top=self.canvas.canvasy(0);bottom=top+self.canvas.winfo_height()
        if y<top:self.canvas.yview_moveto(y/total)
        elif y+self.cell_height>bottom:self.canvas.yview_moveto(max(0,y+self.cell_height-self.canvas.winfo_height())/total)
        self.schedule_draw()
    def destroy(self):
        for job in (self.job,self.paint_job):
            if job:self.after_cancel(job)
        self.cache.clear();self.photos=[];super().destroy()
