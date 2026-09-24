"""Visor TIFF por página y explorador de copias de trabajo."""
import datetime
import os
import sqlite3
import tkinter as tk
from tkinter import ttk,messagebox,filedialog,simpledialog
from pathlib import Path
from .workspace import portable_name
from .coding import CodingService,render_page,pillow
from .ui import Table,Form

from .coding_ui_v3 import CodingUIV3
from .coding_v3 import preview_image
from .file_browser import FileBrowser,FlowBar

class CodingWindow(CodingUIV3,tk.Toplevel):
    def __init__(self,parent,work):
        pillow()  # Fallo claro antes de crear una ventana a medio inicializar.
        super().__init__(parent);self.parent=parent;self.service=CodingService(parent.store);self.work=work
        self.current=None;self.page=0;self.ops=[];self.image=None;self.photo=None;self.scale=1.;self.zoom=None;self.loading=False;self.selection_start=None
        self.chord=None;self.pressed=set();self.order=tk.StringVar(value='Fecha escaneo');self.desc=tk.BooleanVar();self.advance=tk.BooleanVar(value=True);self.original_view=tk.BooleanVar();self.crop_mode=tk.BooleanVar()
        w=parent.store.one('trabajos',work);folio=parent.store.one('folios',w['folio_id'])['numero']
        self.title('Codificar · {} · {} · legajo {}'.format(folio,w['curp'],w['legajo']))
        width=max(860,min(1380,self.winfo_screenwidth()-80));height=max(520,min(850,self.winfo_screenheight()-110))
        self.geometry('{}x{}'.format(width,height));self.minsize(860,520)
        self.protocol('WM_DELETE_WINDOW',self.close)
        style=ttk.Style(self);style.configure('Coding.TButton',padding=(5,2),width=0)
        self.header=FlowBar(self,padding=(4,2));self.header.pack(fill='x')
        self.menu_button(self.header,'Importar',[('Archivos TIFF…',self.import_files),('Carpeta…',self.import_folder)])
        self.menu_button(self.header,'Archivo',[('Renombrar (F2)',self.rename),('Marcar reescaneo…',self.mark_scan),('Reescaneos…',self.corrections_view),('Retirar TIFF…',self.remove_file),('TIFF retirados…',self.removed_view),('Historial / originales…',self.history),('Recuperar operación…',self.recover)])
        self.menu_button(self.header,'Editar',[('Guardar (Ctrl+S)',self.save),('Deshacer (Ctrl+Z)',self.undo),('Descartar ajustes…',self.discard),('Girar 90° izquierda',lambda:self.add_op(('rotate',90))),('Girar 90° derecha',lambda:self.add_op(('rotate',-90))),('Ajuste −0.2°',lambda:self.add_op(('rotate',-.2))),('Ajuste +0.2°',lambda:self.add_op(('rotate',.2))),('Otro ángulo…',self.angle)])
        self.button(self.header,'Organizar / entregar',self.organize)
        self.button(self.header,'Atajos',self.shortcuts)
        self.header.add(ttk.Checkbutton(self.header,text='Avanzar al codificar',variable=self.advance))
        pan=tk.PanedWindow(self,orient='horizontal',sashwidth=7,borderwidth=0);pan.pack(fill='both',expand=True,padx=5)
        left=ttk.Frame(pan,width=280,padding=(3,3));pan.add(left,minsize=205)
        ordering=ttk.Frame(left);ordering.pack(fill='x',pady=(0,4))
        ttk.Label(ordering,text='Orden').pack(side='left')
        combo=ttk.Combobox(ordering,textvariable=self.order,values=['Fecha escaneo','Fecha creación','Nombre','Código'],state='readonly',width=13);combo.pack(side='left',fill='x',expand=True,padx=3);combo.bind('<<ComboboxSelected>>',lambda e:self.refresh_files())
        ttk.Checkbutton(ordering,text='Desc.',variable=self.desc,command=self.refresh_files).pack(side='right')
        self.files_table=FileBrowser(left,self.service,self.select_file);self.files_table.pack(fill='both',expand=True)
        center=ttk.Frame(pan);pan.add(center,minsize=300,stretch='always')
        self.page_label=tk.StringVar(value='Vista previa')
        title=ttk.Label(center,textvariable=self.page_label,anchor='center',padding=4);title.pack(fill='x')
        bottom=ttk.Frame(center);bottom.pack(side='bottom',fill='x')
        nav=FlowBar(bottom);nav.pack(fill='x')
        self.button(nav,'‹ TIFF',lambda:self.navigate(-1));self.button(nav,'TIFF ›',lambda:self.navigate(1))
        self.button(nav,'‹ Pág.',lambda:self.page_move(-1));self.button(nav,'Pág. ›',lambda:self.page_move(1))
        self.button(nav,'Ajustar',self.fit);self.button(nav,'100%',lambda:self.set_zoom(1.))
        self.zoom_label=tk.StringVar(value='');nav.add(ttk.Label(nav,textvariable=self.zoom_label,width=5))
        edit=FlowBar(bottom);edit.pack(fill='x')
        self.button(edit,'↶ 90°',lambda:self.add_op(('rotate',90)));self.button(edit,'↷ 90°',lambda:self.add_op(('rotate',-90)))
        edit.add(ttk.Checkbutton(edit,text='Recortar',variable=self.crop_mode))
        self.button(edit,'Deshacer',self.undo);self.button(edit,'Guardar',self.save)
        edit.add(ttk.Checkbutton(edit,text='Sin ajustes',variable=self.original_view,command=lambda:self.safe(self.render)))
        area=ttk.Frame(center);area.pack(fill='both',expand=True);self.canvas=tk.Canvas(area,bg='#34434a',highlightthickness=0,takefocus=True)
        sx=ttk.Scrollbar(area,orient='horizontal',command=self.canvas.xview);sy=ttk.Scrollbar(area,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=sx.set,yscrollcommand=sy.set);self.canvas.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew');area.rowconfigure(0,weight=1);area.columnconfigure(0,weight=1)
        self.canvas.bind('<ButtonPress-1>',self.mouse_down);self.canvas.bind('<B1-Motion>',self.mouse_drag);self.canvas.bind('<ButtonRelease-1>',self.mouse_up)
        self.canvas.bind('<ButtonPress-2>',lambda e:self.canvas.scan_mark(e.x,e.y));self.canvas.bind('<B2-Motion>',lambda e:self.canvas.scan_dragto(e.x,e.y,gain=1))
        self.canvas.bind('<MouseWheel>',self.wheel)
        right=ttk.Frame(pan,width=280,padding=(3,3));pan.add(right,minsize=205)
        ttk.Label(right,text='Catálogo',font='TkHeadingFont').pack(anchor='w')
        searchbar=ttk.Frame(right);searchbar.pack(fill='x',pady=4);ttk.Label(searchbar,text='Buscar').pack(side='left')
        self.search=tk.StringVar();entry=ttk.Entry(searchbar,textvariable=self.search);entry.pack(side='left',fill='x',expand=True,padx=4);entry.bind('<KeyRelease>',lambda e:self.refresh_catalog())
        self.cat_table=Table(right,['id','codigo','atajo','titulo']);self.cat_table.pack(fill='both',expand=True)
        self.cat_table.tree.configure(displaycolumns=('codigo','atajo','titulo'))
        for name,size in [('codigo',65),('atajo',85),('titulo',130)]:self.cat_table.tree.column(name,width=size,minwidth=45,stretch=name=='titulo')
        self.cat_table.tree.bind('<Double-1>',lambda e:self.safe(self.assign_selected));self.cat_table.tree.bind('<<TreeviewSelect>>',lambda e:self.show_catalog())
        self.cat_text=tk.Text(right,height=4,wrap='word',width=20,relief='flat',background='#f1f4f7');self.cat_text.pack(fill='x',pady=3)
        ttk.Button(right,text='Asignar código',style='Coding.TButton',command=lambda:self.safe(self.assign_selected)).pack(fill='x',pady=3)
        self.info=tk.StringVar(value='Importa escaneos de este expediente y legajo.')
        self.info_label=ttk.Label(self,textvariable=self.info,anchor='w',padding=(6,3));self.info_label.pack(fill='x')
        self.bind('<KeyPress>',self.key_press);self.bind('<KeyRelease>',lambda e:self.pressed.discard(e.keysym.lower()))
        self.setup_v3(pan,left,center,right)
        self.refresh_catalog();self.refresh_files();self.after(180,self.first_file)

    def safe(self,fn):
        try:return fn()
        except (ValueError,OSError,sqlite3.Error,EOFError,RuntimeError) as e:messagebox.showerror('Codificación',str(e),parent=self)
    def button(self,frame,label,fn):
        button=ttk.Button(frame,text=label,style='Coding.TButton',command=lambda:self.safe(fn))
        if isinstance(frame,FlowBar):frame.add(button)
        else:button.pack(side='left',padx=2,pady=2)
        return button
    def menu_button(self,frame,label,actions):
        button=ttk.Menubutton(frame,text=label);menu=tk.Menu(button,tearoff=False);button.configure(menu=menu)
        for title,action in actions:menu.add_command(label=title,command=lambda fn=action:self.safe(fn))
        frame.add(button);return menu
    def require(self):
        if self.current is None:raise ValueError('Selecciona un TIFF primero.')
        return self.service.file(self.current)
    def first_file(self):
        children=self.files_table.tree.get_children()
        if children:self.files_table.tree.selection_set(children[0])
    def refresh_files(self):
        self.loading=True
        rows=self.service.files(self.work,self.order.get(),self.desc.get())
        for r in rows:
            corrections=self.parent.store.rows("SELECT id FROM correcciones_tiff WHERE archivo_id=? AND estado='Pendiente'",(r['id'],))
            if corrections:r['estado']='REESCANEAR'
            r.update(nombre=portable_name(r['ruta']),fecha=datetime.datetime.fromtimestamp(r['fecha_origen']).strftime('%d/%m/%Y %H:%M:%S'))
        self.files_table.fill(rows)
        if self.current and str(self.current) in self.files_table.tree.get_children():self.files_table.tree.selection_set(str(self.current));self.files_table.tree.see(str(self.current))
        self.loading=False
    def legacy_refresh_catalog(self):
        q=self.search.get().casefold();self.catalog=self.service.catalog()
        self.cat_table.fill([dict(c,secuencia='F6 '+c['secuencia'],favorito='Ctrl+'+str(c['favorito']) if c['favorito'] else '') for c in self.catalog if q in (c['codigo']+' '+c['titulo']+' '+c['descripcion']).casefold()])
    def show_catalog(self):
        if not self.cat_table.tree.selection():return
        cid=self.cat_table.selected();c=next(c for c in self.catalog if c['id']==cid)
        self.cat_text.configure(state='normal');self.cat_text.delete('1.0','end');self.cat_text.insert('1.0',c['titulo']+'\n\n'+c['descripcion']);self.cat_text.configure(state='disabled')
    def pending(self):
        if not self.ops:return True
        answer=messagebox.askyesnocancel('Edición pendiente','¿Guardar la edición de esta página antes de continuar?\nSí: guardar. No: descartar. Cancelar: seguir editando.',parent=self)
        if answer is None:return False
        if answer:self.save()
        else:self.ops=[]
        return True
    def select_file(self,event=None):
        if self.loading or not self.files_table.tree.selection():return
        ident=self.files_table.selected()
        if ident==self.current:return
        def switch():
            if not self.pending():self.refresh_files();return
            old=self.current;self.current=ident;self.page=0;self.ops=[];self.zoom=None
            try:self.render();self.files_table.see_selected()
            except Exception:self.current=old;self.refresh_files();raise
        self.safe(switch)
    def render(self):
        row=self.require();path=self.service.path(row['ruta'])
        if self.image is not None:self.image.close()
        self.image=render_page(path,self.page,[] if self.original_view.get() else self.ops)
        self.page_label.set('Página {} / {} · {}'.format(self.page+1,row['paginas'],row['codigo'] or 'Sin código'))
        self.draw();self.info.set('{} · página {}/{} · {}×{} px · {} · {}'.format(path.name,self.page+1,row['paginas'],self.image.width,self.image.height,row['codigo'] or 'Sin código','CAMBIOS SIN GUARDAR' if self.ops else 'Sin cambios pendientes'))
    def draw(self):
        if self.image is None:return
        from PIL import Image,ImageTk
        width=max(100,self.canvas.winfo_width());height=max(100,self.canvas.winfo_height())
        self.scale=self.zoom if self.zoom else min(width/self.image.width,height/self.image.height)
        # El zoom no crea una imagen de miles de megapíxeles: máximo 16 Mpx en pantalla.
        size=(max(1,int(self.image.width*self.scale)),max(1,int(self.image.height*self.scale)))
        if size[0]*size[1]>16000000:raise ValueError('Reduce el zoom: la vista superaría 16 millones de píxeles.')
        preview=preview_image(self.image,size);self.photo=ImageTk.PhotoImage(preview,master=self);preview.close()
        self.canvas.delete('all');self.canvas.create_image(0,0,image=self.photo,anchor='nw');self.canvas.configure(scrollregion=(0,0,*size))
        if hasattr(self,'zoom_label'):self.zoom_label.set('{:.0f}%'.format(self.scale*100))
    def fit(self):self.zoom=None;self.draw()
    def set_zoom(self,value):
        old=self.zoom;self.zoom=value
        try:self.draw()
        except Exception:self.zoom=old;raise
    def zoom_by(self,factor):self.set_zoom(max(.05,min(3.,self.scale*factor)))
    def legacy_wheel(self,event):
        if event.state & 4:self.safe(lambda:self.zoom_by(1.15 if event.delta>0 else 1/1.15))
        else:self.canvas.yview_scroll(-1 if event.delta>0 else 1,'units')
        return 'break'
    def navigate(self,delta):
        if not self.pending():return
        ids=[int(i) for i in self.files_table.tree.get_children()]
        if not ids:return
        pos=ids.index(self.current) if self.current in ids else 0;new=max(0,min(len(ids)-1,pos+delta))
        if ids[new]!=self.current:self.files_table.tree.selection_set(str(ids[new]));self.files_table.tree.see(str(ids[new]));self.select_file()
    def page_move(self,delta):
        row=self.require()
        if not self.pending():return
        self.page=max(0,min(row['paginas']-1,self.page+delta));self.ops=[];self.render()
    def add_op(self,op):
        self.require();self.original_view.set(False);self.ops.append(op)
        try:self.render()
        except Exception:self.ops.pop();self.render();raise
    def angle(self):
        angle=simpledialog.askfloat('Rotación fina','Grados: positivo gira a la izquierda; negativo a la derecha.',minvalue=-180,maxvalue=180,parent=self)
        if angle is not None:self.add_op(('rotate',angle))
    def undo(self):
        if self.ops:self.ops.pop();self.render()
    def discard(self):
        if self.ops and messagebox.askyesno('Descartar','¿Descartar los ajustes aún no guardados de esta página?',parent=self):self.ops=[];self.render()
    def save(self):
        self.require()
        if self.ops:
            self.service.save_edit(self.current,self.page,self.ops);self.ops=[];self.original_view.set(False);self.render();self.refresh_files();self.parent.refresh()
    def position(self,event):
        if self.image is None:return 0,0
        return (max(0,min(self.image.width,int(self.canvas.canvasx(event.x)/self.scale))),max(0,min(self.image.height,int(self.canvas.canvasy(event.y)/self.scale))))
    def mouse_down(self,event):
        self.canvas.focus_set()
        if self.crop_mode.get() and not self.original_view.get() and self.image is not None:self.selection_start=self.position(event)
        else:self.canvas.scan_mark(event.x,event.y)
    def mouse_drag(self,event):
        if self.selection_start:
            x,y=self.position(event);a,b=self.selection_start;self.canvas.delete('crop');self.canvas.create_rectangle(a*self.scale,b*self.scale,x*self.scale,y*self.scale,outline='#ffb33b',width=2,tags='crop')
        else:self.canvas.scan_dragto(event.x,event.y,gain=1)
    def mouse_up(self,event):
        if self.selection_start:
            a,b=self.selection_start;x,y=self.position(event);self.selection_start=None;self.canvas.delete('crop')
            if abs(a-x)>3 and abs(b-y)>3:self.safe(lambda:self.add_op(('crop',min(a,x),min(b,y),max(a,x),max(b,y))))
            self.crop_mode.set(False)
    def legacy_key_press(self,event):
        key=event.keysym.lower()
        if key in self.pressed:return
        self.pressed.add(key)
        if key=='escape':self.chord=None;self.crop_mode.set(False);return 'break'
        # Atajos locales: nunca codificar mientras se escribe en un campo/formulario.
        if event.widget.winfo_class() in ('TEntry','Entry','Text','TCombobox','Spinbox'):return
        if key=='f6':self.chord='';self.info.set('Código: escribe las dos letras del catálogo (Escape cancela).');return 'break'
        if self.chord is not None and len(key)==1 and key.isalpha():
            self.chord+=key.upper()
            if len(self.chord)==2:
                seq=self.chord;self.chord=None;cat=next((c for c in self.catalog if c['secuencia']==seq),None)
                if cat:self.safe(lambda:self.assign(cat['codigo']))
                else:self.info.set('No hay código activo para F6 '+seq)
            else:self.info.set('Secuencia: '+self.chord+'…')
            return 'break'
        if event.state & 4:
            if key in '123456789' and len(key)==1:
                cat=next((c for c in self.catalog if c['favorito']==int(key)),None)
                if cat:self.safe(lambda:self.assign(cat['codigo']))
                else:self.info.set('Asigna Ctrl+'+key+' desde Atajos.')
                return 'break'
            if key=='s':self.safe(self.save);return 'break'
            if key=='z':self.safe(self.undo);return 'break'
        actions={'f2':self.rename,'f7':lambda:self.navigate(-1),'f8':lambda:self.navigate(1),'prior':lambda:self.page_move(-1),'next':lambda:self.page_move(1)}
        if key in actions:self.safe(actions[key]);return 'break'
    def assign_selected(self):
        ident=self.cat_table.selected();self.assign(next(c['codigo'] for c in self.catalog if c['id']==ident))
    def assign(self,code):
        self.require()
        if not self.pending():return
        ids=[int(i) for i in self.files_table.tree.get_children()];pos=ids.index(self.current);next_id=ids[pos+1] if pos+1<len(ids) else None
        self.service.assign(self.current,code);self.refresh_files();self.render();self.parent.refresh()
        if self.advance.get() and next_id:self.files_table.tree.selection_set(str(next_id));self.select_file()
        self.canvas.focus_set()
    def rename(self):
        row=self.require()
        if not self.pending():return
        name=simpledialog.askstring('Renombrar','Nombre completo con código y extensión TIFF:',initialvalue=portable_name(row['ruta']),parent=self)
        if name:self.service.rename(self.current,name);self.refresh_files();self.render();self.parent.refresh()
    def import_files(self):
        if not self.pending():return
        paths=filedialog.askopenfilenames(parent=self,title='Escaneos de este expediente y legajo',filetypes=[('TIFF','*.tif *.tiff'),('Todos','*.*')])
        if paths:self.import_paths(paths)
    def import_folder(self):
        if not self.pending():return
        folder=filedialog.askdirectory(parent=self,title='Carpeta con escaneos de UN expediente/legajo')
        if folder:self.import_paths(sorted(p for p in Path(folder).iterdir() if p.is_file() and p.suffix.lower() in ('.tif','.tiff')))
    def import_paths(self,paths):
        if not paths:raise ValueError('No hay TIFF en la carpeta elegida. Se leen solo archivos directamente en esa carpeta.')
        if not messagebox.askyesno('Confirmar expediente','Se copiarán {} TIFF al expediente/legajo que aparece arriba.\n¿Todos corresponden a ese trabajo?'.format(len(paths)),parent=self):return
        self.configure(cursor='watch');self.update_idletasks()
        try:result=self.service.import_files(self.work,paths)
        finally:self.configure(cursor='')
        self.refresh_files();self.parent.refresh();self.first_file()
        messagebox.showinfo('Importación','Copiados: {}\nDuplicados idénticos omitidos: {}\nErrores: {}'.format(result['importados'],result['duplicados'],'\n'.join(result['errores']) or 'Ninguno'),parent=self)
    def legacy_shortcuts(self):
        win=tk.Toplevel(self);win.title('Atajos de documentos');win.geometry('900x550');table=Table(win,['id','codigo','secuencia','favorito','titulo']);table.pack(fill='both',expand=True);table.fill(self.service.catalog())
        def edit():
            cid=table.selected();c=next(c for c in self.service.catalog() if c['id']==cid)
            def submit(v):self.service.set_shortcut(cid,v['sequence'],v['favorite']);table.fill(self.service.catalog());self.refresh_catalog()
            Form(win,'Atajo de '+c['codigo'],[('sequence','Dos letras después de F6',c['secuencia']),('favorite','Ctrl + número (vacío para quitar)',c['favorito'] or '')],submit)
        self.button(win,'Modificar atajo',edit)
        def export():
            path=self.parent.store.workspace.reports/'atajos_documentos.csv';path.parent.mkdir(exist_ok=True)
            self.parent.store.csv_write(path,self.service.catalog());messagebox.showinfo('Atajos exportados',str(path),parent=win)
        self.button(win,'Exportar lista para imprimir',export)
        ttk.Label(win,text='Los atajos son exclusivos de esta ventana. No se activan en el Explorador de Windows.').pack()
    def history(self):
        row=self.require();win=tk.Toplevel(self);win.title('Original y revisiones');win.geometry('900x500');win.transient(self);win.grab_set()
        ttk.Label(win,text='Original preservado: '+str(self.service.path(row['original'])),wraplength=850).pack(anchor='w')
        table=Table(win,['id','fecha','tipo','estado','detalle']);table.pack(fill='both',expand=True)
        table.fill(self.parent.store.rows('SELECT * FROM operaciones_tiff WHERE archivo_id=? ORDER BY id DESC',(self.current,)))
        def restore():
            if not self.pending():return
            if messagebox.askyesno('Restaurar imagen original','Se recuperarán todas las páginas originales del TIFF. Se conserva el nombre codificado y un respaldo de la versión actual. ¿Continuar?',parent=win):
                self.service.restore_original(self.current);self.ops=[];self.page=0;self.render();self.parent.refresh();win.destroy()
        self.button(win,'Restaurar imagen original',restore)
    def recover(self):
        if not self.pending():return
        if messagebox.askyesno('Recuperar operación','Se intentará recuperar el último estado registrado. Las copias de importaciones interrumpidas se conservarán en recuperados. ¿Continuar?',parent=self):
            n=self.service.recover(self.work);self.refresh_files();self.parent.refresh();messagebox.showinfo('Recuperación',str(n)+' operaciones recuperadas.',parent=self)

    def organize(self):
        if not self.pending():return
        plan=self.service.plan(self.work);win=tk.Toplevel(self);win.title('Vista previa de organización');win.geometry('1000x550');win.transient(self);win.grab_set()
        table=Table(win,['id','source','target','paginas']);table.pack(fill='both',expand=True);table.fill(plan)
        ttk.Label(win,text='Se moverán las copias gestionadas. Escaneos originales intactos. Los estados de proceso no se avanzan automáticamente.').pack()
        def run():
            self.configure(cursor='watch');self.update_idletasks()
            try:out=self.service.organize(self.work)
            finally:self.configure(cursor='')
            self.refresh_files();self.parent.refresh();win.destroy();messagebox.showinfo('Organización completada','Carpetas creadas e inventario vinculado a este legajo.\nReporte: '+str(out),parent=self)
        self.button(win,'Confirmar organización',run)
    def close(self):
        try:
            if not self.pending():return False
        except Exception as e:messagebox.showerror('No se pudo guardar',str(e),parent=self);return False
        if self.image is not None:self.image.close()
        self.save_layout();self.files_table.save_preferences()
        for job in (self.resize_job,getattr(self,'wheel_job',None)):
            if job:self.after_cancel(job)
        self.destroy();return True
