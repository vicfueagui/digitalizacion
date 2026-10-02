"""Recepción explícita de integraciones y presentación común de identidad."""
import datetime
import tkinter as tk
from tkinter import ttk,messagebox
from .integrations import Integrations


def heading(store,work):
    c=Integrations(store).context(work)
    return '{} · {} · L{} · {} · {}'.format(c['nombre'],c['curp'],c['legajo'],c['folio'],c['etiqueta'])


def show_integrations(app,work):
    from .ui import Table,Form
    service=Integrations(app.store)
    win=tk.Toplevel(app);win.title('Integraciones · '+heading(app.store,work));win.geometry('1050x600')
    ttk.Label(win,text=heading(app.store,work),style='Subtitle.TLabel',wraplength=1000,padding=10).pack(fill='x')
    ttk.Label(win,text='Una integración incorpora documentos nuevos al mismo expediente. Cada una se cuenta y procesa por separado.\nLa nueva entrega contiene todos los TIFF vigentes del expediente; las entregas anteriores se conservan.',padding=10).pack(fill='x')
    total=tk.StringVar();ttk.Label(win,textvariable=total,padding=10).pack(anchor='w')
    table=Table(win,['id','etiqueta','folio','recibido','fisicos','tiff','paginas','estado','referencia']);table.pack(fill='both',expand=True)
    def reload():
        table.fill(service.list(work));t=service.totals(work)
        total.set('{} hojas confirmadas · {} conteos pendientes · {} TIFF vigentes · {} páginas'.format(t['hojas_confirmadas'],t['conteos_pendientes'],t['tiff'],t['paginas']))
    def start():
        # Evitar que un visor antiguo importe accidentalmente al lote nuevo.
        coder=getattr(app,'coder',None)
        if coder is not None and coder.winfo_exists() and coder.work==work:
            if not coder.close():return
        folios={r['numero']:r['id'] for r in app.store.rows('SELECT id,numero FROM folios WHERE activo=1 ORDER BY numero')}
        current=service.current(work);selected=app.store.one('folios',current['folio_id'])['numero']
        def submit(v):
            text=heading(app.store,work)+'\n\nFolio: '+v['folio']+'\nRecepción: '+v['fecha']+'\nReferencia: '+v['referencia']+'\n\n¿Cotejaste físicamente CURP, legajo y la nueva documentación?'
            if not messagebox.askyesno('Confirmar recepción de integración',text,parent=win):return
            service.start(work,v['motivo'],v['fecha'],folios[v['folio']],v['referencia'],v['persona'],confirmed=True)
            reload();app.refresh();messagebox.showinfo('Integración iniciada','Ahora cuenta SOLO las hojas nuevas. Después digitaliza, codifica, organiza y solicita revisión.',parent=win)
        Form(win,'Nueva integración · recepción física',[
            ('folio','Folio de recepción',selected,list(folios)),('fecha','Fecha real (AAAA-MM-DD)',datetime.date.today().isoformat()),
            ('referencia','Acuse / referencia física',''),('motivo','Documentación que se integra / motivo',''),
            ('persona','Digitalizador',current['digitalizador'],{'store':app.store,'kind':'persona'})],submit)
    def history():
        chosen=table.selected()
        app.text_view('Detalle de integración',{'Integración':next(r for r in service.list(work) if r['id']==chosen),
            'Bloques de conteo':app.store.rows('SELECT id,cantidad,nota,activo,creado FROM conteos WHERE integracion_id=? ORDER BY id',(chosen,)),
            'Etapas':app.store.rows('SELECT estado,inicio,fin,motivo,operador FROM historial WHERE integracion_id=? ORDER BY id',(chosen,))},win)
    bar=ttk.Frame(win,padding=8);bar.pack(fill='x')
    for title,fn in [('Nueva integración',start),('Ver historial del lote',history),('Contar integración actual',lambda:app.detail(work)),('Actualizar',reload)]:
        ttk.Button(bar,text=title,command=lambda f=fn:app.safe(f)).pack(side='left',padx=4)
    reload();return win
