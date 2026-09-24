import sys
import json
import tkinter as tk
from tkinter import ttk,messagebox,filedialog,simpledialog
from pathlib import Path
from .workspace import portable_name
from .coding_v3 import NumericInput,preview_image

class CodingUIV3:
    def setup_v3(self,pan,left,center,right):
        self.pan=pan;self.left_panel=left;self.center_panel=center;self.right_panel=right
        self.numeric=NumericInput();self.resize_job=None;self.wheel_job=None;self.wheel_factor=1.;self.restoring_layout=False
        saved=self.parent.store.rows("SELECT value FROM meta WHERE key='visor_paneles'")
        values=saved[0]['value'].split(',') if saved else ['1','1']
        self.show_files=tk.BooleanVar(value=values[0]=='1');self.show_codes=tk.BooleanVar(value=values[-1]=='1')
        menu=self.menu_button(self.header,'Vista',[
            ('Solo imagen (F11)',self.only_image),('Restablecer paneles',self.reset_layout),
            ('Ayuda de navegación',lambda:messagebox.showinfo('Codificación',
             'Arrastra los separadores para dar espacio a archivos, imagen o catálogo.\n'
             'Archivos: Detalles, Lista o Miniaturas. Rueda desplaza; Ctrl + rueda cambia su tamaño.\n'
             'Imagen: rueda amplía/reduce; Shift + rueda desplaza. Arrastrar mueve la imagen.\n'
             'F7/F8: TIFF anterior/siguiente. RePág/AvPág: páginas. F11: solo imagen.\n'
             'Mantén Ctrl, escribe el número y suelta Ctrl para codificar. HL usa Ctrl+Shift.\n'
             'Editar contiene giro fino y descarte. Archivo contiene reescaneo, retiro e historial.',parent=self))])
        menu.add_separator();menu.add_checkbutton(label='Panel Archivos',variable=self.show_files,command=self.panels)
        menu.add_checkbutton(label='Panel Catálogo',variable=self.show_codes,command=self.panels)
        self.pan.bind('<ButtonRelease-1>',lambda e:self.save_layout())
        self.canvas.bind('<Configure>',lambda e:self.schedule_resize())
        self.canvas.bind('<Button-4>',lambda e:self.wheel_linux(e,1))
        self.canvas.bind('<Button-5>',lambda e:self.wheel_linux(e,-1))
        self.bind('<KeyRelease>',self.key_release)
        self.bind('<FocusOut>',self.focus_out,add='+')
        self.after(120,self.restore_layout)

    def focus_out(self,event):
        self.numeric.clear();self.pressed.clear()

    def panels(self):
        for pane in self.pan.panes():self.pan.forget(pane)
        side=max(205,min(320,int(self.winfo_width()*.24)))
        if self.show_files.get():self.pan.add(self.left_panel,minsize=205,width=side,stretch='never')
        self.pan.add(self.center_panel,minsize=300,stretch='always')
        if self.show_codes.get():self.pan.add(self.right_panel,minsize=205,width=side,stretch='never')
        with self.parent.store.db:self.parent.store.db.execute("INSERT OR REPLACE INTO meta VALUES('visor_paneles',?)",(('1' if self.show_files.get() else '0')+','+('1' if self.show_codes.get() else '0'),))
        self.schedule_resize()

    def save_layout(self):
        if self.restoring_layout:return
        widths={'files':self.left_panel.winfo_width(),'codes':self.right_panel.winfo_width()}
        with self.parent.store.db:self.parent.store.db.execute("INSERT OR REPLACE INTO meta VALUES('visor_anchos',?)",(json.dumps(widths),))

    def restore_layout(self):
        self.restoring_layout=True
        self.panels();self.update_idletasks()
        saved=self.parent.store.rows("SELECT value FROM meta WHERE key='visor_anchos'")
        if saved:
            try:
                widths=json.loads(saved[0]['value'])
                maximum=max(205,(self.winfo_width()-340)//2)
                if self.show_files.get():self.pan.paneconfigure(self.left_panel,width=max(205,min(maximum,int(widths['files']))))
                if self.show_codes.get():self.pan.paneconfigure(self.right_panel,width=max(205,min(maximum,int(widths['codes']))))
            except (ValueError,KeyError,TypeError):pass
        self.restoring_layout=False

    def reset_layout(self):
        with self.parent.store.db:self.parent.store.db.execute("DELETE FROM meta WHERE key='visor_anchos'")
        self.show_files.set(True);self.show_codes.set(True);self.panels()

    def only_image(self):
        show=not (self.show_files.get() or self.show_codes.get())
        self.show_files.set(show);self.show_codes.set(show);self.panels()

    def schedule_resize(self):
        if self.resize_job:self.after_cancel(self.resize_job)
        self.resize_job=self.after(100,self.resize_render)
    def resize_render(self):
        self.resize_job=None
        if self.zoom is None:self.safe(self.draw)

    def wheel(self,event):
        if not event.delta:return 'break'
        steps=max(-5,min(5,event.delta if sys.platform=='darwin' else event.delta/120.0))
        if event.state & 1:self.canvas.yview_scroll(-max(1,round(abs(steps)))* (1 if steps>0 else -1),'units');return 'break'
        self.queue_zoom(event,1.12**steps);return 'break'
    def wheel_linux(self,event,direction):
        if event.state & 1:self.canvas.yview_scroll(-direction*3,'units')
        else:self.queue_zoom(event,1.12**direction)
        return 'break'

    def queue_zoom(self,event,factor):
        self.wheel_factor*=factor
        self.wheel_event=event
        if self.wheel_job:self.after_cancel(self.wheel_job)
        self.wheel_job=self.after(60,self.flush_zoom)

    def flush_zoom(self):
        factor=self.wheel_factor;self.wheel_factor=1.;self.wheel_job=None
        self.zoom_at(self.wheel_event,factor)
    def zoom_at(self,event,factor):
        if self.image is None:return
        x=self.canvas.canvasx(event.x)/self.scale;y=self.canvas.canvasy(event.y)/self.scale
        def apply():
            self.zoom_by(factor)
            self.canvas.xview_moveto(max(0,(x*self.scale-event.x)/(self.image.width*self.scale)))
            self.canvas.yview_moveto(max(0,(y*self.scale-event.y)/(self.image.height*self.scale)))
        self.safe(apply)

    def key_press(self,event):
        key=event.keysym.lower()
        if key in self.pressed:return 'break' if self.numeric.digits else None
        self.pressed.add(key)
        if event.widget.winfo_toplevel()!=self:
            self.numeric.clear();return
        if event.widget.winfo_class() in ('TEntry','Entry','Text','TCombobox','Spinbox','TSpinbox'):
            self.numeric.clear();return
        if key=='escape':self.numeric.clear();self.crop_mode.set(False);self.info.set('Atajo cancelado.');return 'break'
        if event.state & 4:
            digit=None
            if len(key)==1 and key.isdigit():digit=key
            elif key.startswith('kp_') and key[-1].isdigit():digit=key[-1]
            elif sys.platform=='darwin' and (event.keycode & 255) in (18,19,20,21,23,22,26,28,25,29):
                digit=dict(zip((18,19,20,21,23,22,26,28,25,29),'1234567890'))[event.keycode & 255]
            elif sys.platform=='win32' and 48<=event.keycode<=57:digit=str(event.keycode-48)
            elif sys.platform=='win32' and 96<=event.keycode<=105:digit=str(event.keycode-96)
            elif key in ('exclam','at','numbersign','dollar','percent','asciicircum','ampersand','asterisk','parenleft','parenright'):
                digit=dict(zip(('exclam','at','numbersign','dollar','percent','asciicircum','ampersand','asterisk','parenleft','parenright'),'1234567890'))[key]
            if digit is not None:self.info.set(self.numeric.digit(digit,bool(event.state&1))+' · suelta Ctrl para aplicar');return 'break'
            if key=='s':self.safe(self.save);return 'break'
            if key=='z':self.safe(self.undo);return 'break'
        actions={'f2':self.rename,'f7':lambda:self.navigate(-1),'f8':lambda:self.navigate(1),'prior':lambda:self.page_move(-1),'next':lambda:self.page_move(1),'f11':self.only_image}
        if key in actions:self.numeric.clear();self.safe(actions[key]);return 'break'

    def key_release(self,event):
        key=event.keysym.lower();self.pressed.discard(key)
        if key in ('control_l','control_r'):
            self.pressed.clear()
            if event.widget.winfo_toplevel()!=self or event.widget.winfo_class() in ('TEntry','Entry','Text','TCombobox','Spinbox','TSpinbox'):
                self.numeric.clear();return
            selected=self.numeric.finish()
            if selected:
                cat=next((c for c in self.catalog if (c['combinacion'],c['numero'])==selected),None)
                if cat:self.safe(lambda:self.assign(cat['codigo']))
                else:self.info.set('Sin código para {} + {}'.format(*selected))
                return 'break'

    def refresh_catalog(self):
        q=self.search.get().casefold();self.catalog=self.service.catalog()
        self.cat_table.fill([dict(c,atajo=c['combinacion']+' + '+str(c['numero'])) for c in self.catalog if q in (c['codigo']+' '+c['titulo']+' '+c['descripcion']).casefold()])

    def shortcuts(self):
        from .ui import Table,Form
        win=tk.Toplevel(self);win.title('Atajos numéricos · suelta Ctrl para aplicar');win.geometry('900x550')
        table=Table(win,['id','codigo','combinacion','numero','titulo']);table.pack(fill='both',expand=True);table.fill(self.service.catalog())
        def edit():
            cid=table.selected();c=next(c for c in self.service.catalog() if c['id']==cid)
            def submit(v):self.service.set_numeric(cid,v['combo'],v['number']);table.fill(self.service.catalog());self.refresh_catalog()
            Form(win,'Atajo de '+c['codigo'],[('combo','Combinación',c['combinacion'],['Ctrl','Ctrl+Shift']),('number','Número (1 a 999)',c['numero'])],submit)
        self.button(win,'Modificar',edit)
        def export():
            path=self.parent.store.workspace.reports/'atajos_numericos.csv';path.parent.mkdir(exist_ok=True);self.parent.store.csv_write(path,self.service.catalog());messagebox.showinfo('Lista',str(path),parent=win)
        self.button(win,'Exportar lista',export)
        ttk.Label(win,text='Ejemplo: mantener Ctrl, pulsar 1 y 5, soltar Ctrl. Nunca se aplica el 1 antes del 15.').pack()

    def mark_scan(self):
        from .ui import Form
        row=self.require()
        if not self.pending():return
        def submit(v):
            self.service.mark_correction(row['id'],int(v['page']),v['location'],v['problem']);self.refresh_files();self.parent.refresh()
        Form(self,'Ubicar hoja para reescaneo',[('page','Página dentro de este TIFF',self.page+1),('location','Ubicación física: hoja, bloque, delante/detrás de…',''),('problem','Problema: cortada, borrosa, reverso incorrecto…','')],submit)

    def reset_current(self):
        self.current=None;self.page=0;self.ops=[];self.canvas.delete('all')
        if self.image is not None:self.image.close();self.image=None
        self.refresh_files();self.first_file();self.parent.refresh()

    def remove_file(self):
        row=self.require()
        if not self.pending():return
        reason=simpledialog.askstring('Retirar TIFF','Motivo. Se retirará de la entrega y de las métricas; se conservará en Retirados para poder recuperarlo.',parent=self)
        if reason:self.service.exclude(row['id'],reason);self.reset_current()

    def removed_view(self):
        from .ui import Table
        win=tk.Toplevel(self);win.title('TIFF retirados (excluidos del inventario)');win.geometry('950x500')
        table=Table(win,['id','ruta','paginas','codigo','estado']);table.pack(fill='both',expand=True)
        def refresh():table.fill(self.parent.store.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=? AND activo=0',(self.work,)))
        def restore():
            reason=simpledialog.askstring('Restaurar','Motivo:',parent=win)
            if reason:self.service.restore_removed(table.selected(),reason);refresh();self.refresh_files();self.parent.refresh()
        self.button(win,'Restaurar',restore);refresh()

    def corrections_view(self):
        from .ui import Table,Form
        win=tk.Toplevel(self);win.title('Reescaneos pendientes y resueltos');win.geometry('1100x580')
        table=Table(win,['id','archivo_id','pagina','ubicacion','problema','estado','nuevo_id']);table.pack(fill='both',expand=True)
        def refresh():table.fill(self.service.corrections(self.work))
        def export():
            path=self.parent.store.workspace.reports/('reescaneos_'+str(self.work)+'.csv');path.parent.mkdir(exist_ok=True);self.parent.store.csv_write(path,self.service.corrections(self.work));messagebox.showinfo('Lista de reescaneo',str(path),parent=win)
        def replace():
            cid=table.selected();correction=next(c for c in self.service.corrections(self.work) if c['id']==cid)
            mapping={str(r['id'])+' | '+portable_name(r['ruta'])+' | '+str(r['paginas'])+' páginas':r['id'] for r in self.service.files(self.work) if r['id']!=correction['archivo_id']}
            if not mapping:raise ValueError('Primero importa el TIFF reescaneado. Después selecciona aquí el reemplazo.')
            def submit(v):
                if not self.pending():return
                if v['scope']=='Solo página indicada':self.service.replace_scanned_page(cid,mapping[v['new']],v['reason'])
                else:self.service.replace_correction(cid,mapping[v['new']],v['reason'])
                self.reset_current();refresh()
            Form(win,'Aplicar reescaneo',[('scope','Alcance de la sustitución','Solo página indicada',['Solo página indicada','TIFF completo']),('new','Nuevo TIFF del mismo legajo',next(iter(mapping)),list(mapping)),('reason','Confirmo revisión de todas las páginas / motivo','')],submit,
                 preview=lambda values:self.preview_candidate(mapping[values['new']]))
        def resolve():
            reason=simpledialog.askstring('Resolver sin sustitución','Explica por qué ya no requiere reescaneo (o se retiró justificadamente):',parent=win)
            if reason:self.service.resolve_without_replacement(table.selected(),reason);refresh();self.parent.refresh()
        bar=ttk.Frame(win);bar.pack(fill='x');self.button(bar,'Exportar lista física',export);self.button(bar,'Vincular nuevo TIFF y sustituir',replace);self.button(bar,'Resolver con motivo',resolve)
        ttk.Label(win,text='1. Ubica y reescanea. 2. Importa el nuevo TIFF. 3. Valida sus páginas. 4. Vincula el reemplazo. 5. Organiza para recalcular.').pack();refresh()

    def preview_candidate(self,ident):
        from .coding import render_page
        from PIL import ImageTk
        row,path=self.service.checked(ident)
        win=tk.Toplevel(self);win.title('Revisar reemplazo: '+path.name);win.geometry('850x700')
        win.transient(self);win.grab_set()
        canvas=tk.Canvas(win,bg='#34434a');canvas.pack(fill='both',expand=True)
        label=tk.StringVar();ttk.Label(win,textvariable=label).pack()
        page=[0]
        def draw(delta=0):
            page[0]=max(0,min(row['paginas']-1,page[0]+delta))
            im=render_page(path,page[0]);scale=min(max(100,canvas.winfo_width())/im.width,max(100,canvas.winfo_height())/im.height)
            preview=preview_image(im,(max(1,int(im.width*scale)),max(1,int(im.height*scale))))
            canvas.photo=ImageTk.PhotoImage(preview,master=win);canvas.delete('all');canvas.create_image(0,0,image=canvas.photo,anchor='nw')
            label.set('Página {}/{} · {}×{} px'.format(page[0]+1,row['paginas'],im.width,im.height));preview.close();im.close()
        bar=ttk.Frame(win);bar.pack(fill='x')
        self.button(bar,'Página anterior',lambda:draw(-1));self.button(bar,'Página siguiente',lambda:draw(1));self.button(bar,'Cerrar vista previa',win.destroy)
        win.after(120,draw)
