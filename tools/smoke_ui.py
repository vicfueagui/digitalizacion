"""Prueba gráfica sintética. Abre Tk y el visor en el equipo local, y los cierra."""
import sys
import tempfile
import tkinter as tk
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from app.demo import create_demo
from app.core import Store
from app.ui import App
from app.coding_ui import CodingWindow
from app.file_browser import FlowBar
from unittest.mock import patch
from types import SimpleNamespace


def main():
    with tempfile.TemporaryDirectory() as temp:
        root=create_demo(Path(temp)/'demo')
        store=Store(workspace=root)
        app=App(store)
        errors=[]; completed=[False]
        def exception(kind,value,tb):errors.append(str(value))
        app.report_callback_exception=exception
        def check():
            try:
                with patch('webbrowser.open',return_value=True) as browser_open:
                    app.help()
                    browser_open.assert_called_once_with((ROOT/'docs/MANUAL_USUARIO.html').as_uri())
                    assert (ROOT/'docs/MANUAL_USUARIO.html').is_file()
                work=store.works()[0]['id']
                viewer=CodingWindow(app,work);app.coder=viewer
                app.update()
                viewer.first_file();app.update();viewer.canvas.focus_force();app.update()
                assert viewer.image is not None
                browser=viewer.files_table
                def toolbars(widget):
                    result=[widget] if isinstance(widget,FlowBar) else []
                    for child in widget.winfo_children():result.extend(toolbars(child))
                    return result
                for size in ('860x600','1024x680','1366x768'):
                    viewer.geometry(size);app.update();viewer.reset_layout();app.update()
                    for bar in toolbars(viewer):
                        bar.layout();app.update_idletasks()
                        assert all(b.winfo_x()+b.winfo_width()<=bar.winfo_width()+2 for b in bar.items), 'Herramientas fuera de la ventana '+size
                    assert viewer.canvas.winfo_height()>viewer.winfo_height()*.5, 'La imagen perdió prioridad vertical'
                    assert viewer.left_panel.winfo_width()>=200 and viewer.right_panel.winfo_width()>=200
                for mode in ('Lista','Detalles','Miniaturas'):
                    browser.mode.set(mode);browser.change_view();app.update();browser.layout()
                assert browser.photos, 'No se cargó la vista miniatura'
                old_size=browser.size.get();browser.wheel(SimpleNamespace(state=4),direction=1);browser.layout()
                assert browser.size.get()>old_size
                original=list(browser.rows);fixture=original[0]
                browser.fill(original+[dict(fixture,id=10000+i) for i in range(240)]);app.update();browser.layout()
                assert len(browser.cache)<=48 and len(browser.photos)<30, 'Las miniaturas deben cargar solo lo visible'
                browser.scroll('moveto',1);browser.draw();assert len(browser.cache)<=48
                viewer.refresh_files();viewer.first_file();app.update();browser.layout()
                viewer.add_op(('rotate',.2));chosen=viewer.current
                if len(browser.rows)>1:
                    target=next(r['id'] for r in browser.rows if r['id']!=chosen)
                    with patch('app.coding_ui.messagebox.askyesnocancel',return_value=None):
                        browser.tree.selection_set(str(target));viewer.select_file();app.update()
                    assert viewer.current==chosen and viewer.ops, 'Cancelar debe conservar selección y ajustes'
                viewer.ops=[];viewer.render()
                viewer.set_zoom(1);viewer.fit();viewer.only_image();viewer.reset_layout();viewer.save_layout()
                viewer.add_op(('rotate',.2));viewer.add_op(('rotate',-.2))
                before=list(viewer.ops)
                with patch('app.coding_ui.messagebox.askyesnocancel',return_value=None):
                    assert not viewer.close(), 'Cancelar no debe cerrar el visor'
                assert viewer.winfo_exists() and viewer.ops==before
                with patch('app.coding_ui.messagebox.askyesnocancel',return_value=False):
                    assert viewer.close()
                summary=app.summary_window(work);app.update();summary._reload_operational();summary.destroy()
                loan=app.loan_window(store.one('trabajos',work)['folio_id']);app.update();loan.destroy()
                assert len(app.boards)==5
                deliveries=store.rows("SELECT id FROM entregas WHERE trabajo_id=? AND estado='Publicada'",(work,))
                if deliveries:
                    window=app.delivery_view(deliveries[0]['id']);app.update();window.destroy()
                    from app.delivery import Deliveries
                    from app.operational_ui import SnapshotViewer
                    service=Deliveries(store);manifest=service.verify(deliveries[0]['id'])
                    image=SnapshotViewer(app,store.workspace.path(service.get(deliveries[0]['id'])['ruta'])/manifest['items'][0]['ruta'])
                    app.update();image.show();assert image.photo is not None;image.destroy()
                columns=app.works_table.tree['displaycolumns']
                assert 'total_tiff' in columns and 'total_paginas' in columns
                assert 'fuera_broche' not in columns and 'carpetas' not in columns
                def debounce():
                    done=tk.BooleanVar(app,value=False);app.after(300,lambda:done.set(True));app.wait_variable(done)
                with patch.object(app,'refresh_board',side_effect=AssertionError('No reconstruir Kanban al escribir')):
                    app.filters['folio'].set('DEMO-B');debounce()
                    assert len(app.works_table.tree.get_children())==1
                    app.filters['folio'].set('');app.filters['texto'].set('demostracion');debounce()
                    assert len(app.works_table.tree.get_children())==2
                    app.filters['desde'].set('2026-');debounce()
                    assert 'Completa la fecha' in app.status.get()
                    app.filters['desde'].set('');app.filters['texto'].set('');debounce()
                    assert len(app.works_table.tree.get_children())==3
                from app.intake_ui import ImportListWindow
                from app.intake import register_legajos
                intake=ImportListWindow(app,root/'ejemplos/lista_folio_sintetica.csv');app.update()
                assert intake.plan['validas']==3 and intake.plan['sin_legajo']==3
                intake.legajo.set('1');assert intake.plan is None
                intake.preview();assert intake.plan['sin_legajo']==0
                intake.legajo.set('');intake.preview()
                with patch('app.intake_ui.messagebox.showinfo'):
                    intake.commit()
                assert app.tabs.tab(app.tabs.select(),'text')=='Folios'
                assert intake.receipt_folio is not None and str(intake.next_button['state'])=='normal'
                intake.legajo.set('2');assert intake.receipt_folio is None and str(intake.next_button['state'])=='disabled'
                intake.destroy()
                folio=store.rows("SELECT id FROM folios WHERE numero='LISTA-DEMO/2026'")[0]['id']
                item=store.rows('SELECT id FROM prestamo_items WHERE folio_id=? ORDER BY id',(folio,))[0]['id']
                works=register_legajos(store,item,'1,2,3','Desglose físico ficticio');app.refresh()
                assert len(works)==3
                siblings=app.legajos_view(works[0]);app.update();siblings.destroy()
                loan=app.loan_window(folio);app.update()
                loan.query.set('lista 2');app.update();loan.select_visible()
                receipt=loan.accept_selected();app.update();assert len(receipt.rows)==1
                assert str(receipt.accept_button['state'])=='disabled'
                receipt.destroy();assert store.one('folios',folio)['recepcion_estado']=='Con pendientes'
                loan.query.set('');loan.select_visible();receipt=loan.accept_selected();app.update()
                assert len(receipt.rows)==5 and sum(r['legajo_nuevo'] for r in receipt.rows)==2
                receipt.confirmed.set(True);receipt.check();receipt.accept_button.invoke();app.update()
                assert not receipt.winfo_exists();assert store.one('folios',folio)['recepcion_estado']=='Aceptado'
                assert len(store.rows('SELECT * FROM trabajos WHERE folio_id=?',(folio,)))==5
                loan.destroy()
                app.tabs.select(app.pages['Indicadores']);app.update()
                with patch.object(app.bi.service,'snapshot',side_effect=AssertionError('No consultar la base al redimensionar')):
                    for size in ('880x620','1024x680','1366x768'):
                        app.geometry(size);app.update()
                        assert int(app.bi.scope_label['wraplength'])<=app.bi.winfo_width()
                        for chart in (app.bi.stages,app.bi.coverage):
                            chart.draw();values=chart.find_withtag('value');assert len(values)==len(chart.rows)
                            for value in values:
                                x1,y1,x2,y2=chart.bbox(value)
                                assert 0<=x1<x2<=chart.winfo_width() and 0<=y1<y2<=chart.winfo_height(), 'Valor de indicador fuera del gráfico '+size
                                assert chart.itemcget(value,'fill')=='#173c4c', 'Contraste explícito en Mac'
                with patch.object(app,'refresh_board',side_effect=AssertionError('No refrescar Kanban desde BI')),patch('app.delivery.Deliveries.current_validation',side_effect=AssertionError('No releer TIFF desde BI')):
                    app.filters['folio'].set('LISTA-DEMO');debounce();assert app.bi.data['metrica']['Trabajos activos']==5
                    app.filters['folio'].set('NO-EXISTE');debounce()
                    assert app.bi.data['metrica']['Trabajos activos']==0
                    assert all('Sin base' in app.bi.stages.itemcget(item,'text') for item in app.bi.stages.find_withtag('value'))
                    app.filters['folio'].set('');debounce()
                detail=app.bi.drill(app.bi.data['etapas'][0]);app.update();detail.destroy()
                app.bi.group.set('Digitalizador');app.bi.group_rows();assert app.bi.group_table.tree.get_children()
                destination=app.bi.service.export(app.bi.data,root/'reportes/indicadores-smoke');assert (destination/'contexto.json').exists()
                from app.ui import Form
                from app.directory_ui import DirectoryPicker
                from tkinter import ttk
                outer=Form(app,'Formulario sintético',[('persona','Responsable','',{'store':store,'kind':'persona'})],lambda values:None);app.update()
                picker=next(w for w in outer.winfo_children() if isinstance(w,DirectoryPicker))
                next(w for w in picker.winfo_children() if isinstance(w,ttk.Button)).invoke();app.update()
                catalog=app.grab_current();assert catalog is not outer
                def button(widget,title):
                    for child in widget.winfo_children():
                        if isinstance(child,ttk.Button) and child['text']==title:return child
                        found=button(child,title)
                        if found:return found
                button(catalog,'Nuevo').invoke();app.update()
                editor=app.grab_current();assert isinstance(editor,Form)
                editor.values['nombre'].set('Persona nueva del ensayo gráfico');button(editor,'Guardar').invoke();app.update()
                assert app.grab_current()==catalog and outer.values['persona'].get()=='Persona nueva del ensayo gráfico'
                assert 'Persona nueva del ensayo gráfico' in picker.combo['values']
                catalog.tk.call(catalog.protocol('WM_DELETE_WINDOW'));app.update()
                assert app.grab_current()==outer;outer.destroy();app.update()
                assert not errors, errors
                completed[0]=True
                print('OK: visor/miniaturas + importación/legajos/directorio + aceptación por selección sin recaptura y Cancelar + BI 880/1024/1366 con valores visibles, filtro vacío, detalle/exportación y sin releer TIFF.',flush=True)
            except BaseException as error:
                errors.append(str(error))
            finally:app.after(100,app.destroy)
        app.after(350,check)
        app.after(20000,app.destroy)
        try:app.mainloop()
        finally:store.db.close()
        if not completed[0]:errors.append('No se completó la comprobación gráfica.')
        if errors:raise RuntimeError('; '.join(errors))


if __name__=='__main__':main()
