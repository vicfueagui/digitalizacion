"""Tk real sobre fixture sintético; no sustituye aceptación visual humana."""
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import test_coding as fixture


class InterfaceTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    load=fixture.CodingTests.load

    def tick(self,app,seconds=.3):
        end=time.monotonic()+seconds
        while time.monotonic()<end:app.update();time.sleep(.02)

    def test_real_windows_multiselect_filters_help_and_cube(self):
        from app.ui import App
        from app.coding_ui import CodingWindow
        from app.help_ui import HelpWindow
        ids=[self.load(self.make(str(n)+'.tif',n)) for n in (1,2,3)]
        errors=[]
        app=App(self.s);app.report_callback_exception=lambda *args:errors.append(str(args[1]));coder=None
        try:
            app.geometry('1120x650+10+10');self.tick(app)
            from tkinter import font as tkfont,ttk
            from app.theme import fonts
            typography=fonts(app)
            self.assertEqual(typography['AppBodyFont'].actual('family'),'Segoe UI')
            self.assertEqual(typography['AppStrongFont'].actual('family'),'Segoe UI Semibold')
            self.assertGreaterEqual(ttk.Style(app).lookup('Treeview','rowheight'),typography['AppBodyFont'].metrics('linespace')+10)
            with patch('app.delivery.Deliveries.basis',side_effect=AssertionError('Kanban no debe releer binarios')):
                app.board_filters['texto'].set('pru');app.board_filters['texto'].set('prueba');self.tick(app)
                self.assertIn('1 expedientes',app.board_status.cget('text'))
            app.bi.cube.refresh(self.s.works());self.assertEqual(app.bi.cube.data['totales']['paginas'],6)
            app.tabs.select(app.pages['Indicadores']);app.bi.tabs.select(app.bi.cube);self.tick(app)
            # La captura del escritorio puede incluir ventanas ajenas. La
            # revisión visual usa una captura dirigida por handle, fuera del test.
            helpwin=HelpWindow(app)
            self.assertEqual(set(helpwin.documents), {'Integraciones, entregas y atajos', 'Recepción e indicadores', 'Operación paso a paso'})
            self.assertIn('Recepción',helpwin.documents['Operación paso a paso'])
            helpwin.query.set('integración');self.tick(app)
            self.assertTrue(helpwin.matches);self.assertIn('Integraciones',helpwin.matches[0]);helpwin.destroy()
            integrations=app.integrations(self.w);self.tick(app);self.assertIn('Prueba',integrations.title());integrations.destroy()
            coder=CodingWindow(app,self.w);app.coder=coder;coder.geometry('1120x650+20+20');self.tick(app,.5)
            self.assertIn('Prueba',coder.title());self.assertIsNotNone(coder.image)
            coder.files_table.select_all();self.tick(app);self.assertEqual(set(coder.files_table.selected_ids()),set(ids))
            coder.refresh_files();self.tick(app);self.assertEqual(set(coder.files_table.selected_ids()),set(ids))
            with patch('app.coding_ui_v3.simpledialog.askstring',return_value='Retiro sintético'),patch('app.coding_ui_v3.messagebox.askyesno',return_value=False):coder.remove_file()
            self.assertEqual(len(self.c.files(self.w)),3)
            with patch('app.coding_ui_v3.simpledialog.askstring',return_value='Retiro sintético'),patch('app.coding_ui_v3.messagebox.askyesno',return_value=True),patch('app.coding_ui_v3.messagebox.showinfo'):
                coder.remove_file()
            self.tick(app);self.assertEqual(len(self.c.files(self.w)),0)
            from app.batch_tiff import BatchTiff
            BatchTiff(self.c).run(self.w,ids,'recuperar','Recuperación sintética');coder.refresh_files();coder.first_file();self.tick(app)
            widget=coder.search_entry
            with patch.object(coder,'save') as save:
                coder.key_press(SimpleNamespace(keysym='s',state=4,widget=widget,keycode=83));self.assertFalse(save.called)
                coder.pressed.clear();coder.key_press(SimpleNamespace(keysym='s',state=4,widget=coder.canvas,keycode=83));self.assertTrue(save.called);coder.pressed.clear()
            for width,height in ((880,620),(1024,650),(1280,650)):
                coder.geometry('{}x{}+20+20'.format(width,height));self.tick(app)
                self.assertGreater(coder.canvas.winfo_width(),220);self.assertGreater(coder.canvas.winfo_height(),120)
            coder.files_table.mode.set('Miniaturas');coder.files_table.change_view();self.tick(app)
            coder.files_table.select_all();self.tick(app)
            coder.close();coder=None;self.tick(app)
            self.assertEqual(errors,[])
        finally:
            if coder is not None:coder.close()
            app.close()
