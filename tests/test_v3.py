import unittest
from PIL import Image
from app.coding_v3 import preview_image,NumericInput,default_shortcut
import test_coding as legacy_coding
import test_domain as legacy_domain

class VisualTests(unittest.TestCase):
    def test_binary_preview_antialiases_without_editing_original(self):
        image=Image.new('1',(100,100),'white')
        for x in range(0,100,2):
            for y in range(100):image.putpixel((x,y),0)
        before=image.tobytes();preview=preview_image(image,(23,23))
        self.assertEqual(preview.mode,'L');self.assertTrue(any(0<v<255 for v in preview.tobytes()))
        self.assertEqual(image.mode,'1');self.assertEqual(image.tobytes(),before)
    def test_numeric_release_disambiguates_1_15_100(self):
        for digits in ('1','15','100','120'):
            n=NumericInput()
            for d in digits:n.digit(d)
            self.assertEqual(n.finish(),('Ctrl',int(digits)));self.assertIsNone(n.finish())
    def test_shift_and_overflow(self):
        n=NumericInput();n.digit('1',True);n.digit('0',True);self.assertEqual(n.finish(),('Ctrl+Shift',10))
        for d in '1000':n.digit(d)
        self.assertIsNone(n.finish())
    def test_code_defaults(self):
        self.assertEqual(default_shortcut('DP-15'),('Ctrl',15));self.assertEqual(default_shortcut('FP-01'),('Ctrl',101));self.assertEqual(default_shortcut('FP-20'),('Ctrl',120));self.assertEqual(default_shortcut('HL-99'),('Ctrl+Shift',99))

class CorrectionTests(unittest.TestCase):
    setUp=legacy_coding.CodingTests.setUp
    tearDown=legacy_coding.CodingTests.tearDown
    make=legacy_coding.CodingTests.make
    load=legacy_coding.CodingTests.load
    def test_mark_block_replace_recalculate(self):
        old=self.load(self.make('old.tif'));self.c.assign(old,'DP-01');self.c.organize(self.w)
        cid=self.c.mark_correction(old,1,'Hoja física 8, después de acta','Texto cortado')
        self.assertIsNone(self.s.latest(self.w))
        with self.assertRaises(ValueError):self.c.organize(self.w)
        p=self.make('new.tif');im=Image.open(p);copy=im.copy();im.close();copy.putpixel((0,0),0);copy.save(p);copy.close()
        new=self.load(p);self.c.replace_correction(cid,new,'Todas las páginas revisadas')
        self.assertEqual(self.c.file(old)['activo'],0);self.assertEqual(self.c.file(new)['codigo'],'DP-01')
        self.c.organize(self.w);metrics=self.s.dashboard(self.s.works());self.assertEqual(metrics['Archivos TIFF'],1);self.assertEqual(metrics['Incidencias abiertas'],0)
    def test_remove_restore_and_empty_inventory(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.c.organize(self.w)
        self.c.exclude(ident,'Duplicado');self.assertEqual(self.c.files(self.w),[])
        self.c.organize(self.w);self.assertEqual(self.s.dashboard(self.s.works())['Archivos TIFF'],0)
        self.c.restore_removed(ident,'Retirado por error');self.c.organize(self.w);self.assertEqual(self.s.dashboard(self.s.works())['Archivos TIFF'],1)
    def test_multipage_cannot_be_replaced_by_single_page(self):
        old=self.load(self.make('multi.tif',3));new=self.load(self.make('single.tif'))
        cid=self.c.mark_correction(old,2,'Hoja 20','Borrosa')
        with self.assertRaises(ValueError):self.c.replace_correction(cid,new,'Revisión')
        self.assertEqual(self.c.file(old)['activo'],1)
    def test_single_rescan_replaces_one_page_in_multi(self):
        from app.coding import render_page
        old=self.load(self.make('multi.tif',3));new=self.load(self.make('single.tif'))
        row=self.c.file(old);before=render_page(self.c.path(row['ruta']),0).tobytes()
        cid=self.c.mark_correction(old,2,'Hoja 9','Cortada')
        self.c.replace_scanned_page(cid,new,'Hoja correcta revisada')
        path=self.c.path(self.c.file(old)['ruta'])
        self.assertEqual(self.c.file(old)['paginas'],3)
        self.assertEqual(render_page(path,0).tobytes(),before)
        self.assertEqual(render_page(path,1).tobytes(),render_page(self.c.path(self.c.file(new)['ruta']),0).tobytes())
        self.assertEqual(self.c.file(new)['activo'],0)
        self.assertEqual(self.c.corrections(self.w)[0]['estado'],'Página sustituida')

    def test_numeric_up_to_999_unique(self):
        self.c.set_numeric(self.dp,'Ctrl',120);self.c.set_numeric(self.hl,'Ctrl+Shift',120)
        self.assertEqual(next(c for c in self.c.catalog() if c['id']==self.dp)['numero'],120)
        with self.assertRaises(ValueError):self.c.set_numeric(self.dp,'Ctrl',1000)
    def test_resolve_retired_bad_scan_with_reason(self):
        ident=self.load();cid=self.c.mark_correction(ident,1,'Separador 2','Reverso ajeno')
        self.c.exclude(ident,'No corresponde al expediente');self.c.resolve_without_replacement(cid,'No forma parte del expediente; confirmado')
        self.c.organize(self.w);self.assertEqual(self.s.dashboard(self.s.works())['Incidencias abiertas'],0)

class IdentityTests(unittest.TestCase):
    setUp=legacy_domain.DomainTests.setUp
    tearDown=legacy_domain.DomainTests.tearDown
    def test_same_curp_legajo_new_cycle_across_folios(self):
        f2=self.s.save_folio('OTRO/2026','2026-09-21')
        new=self.s.save_work(f2,'AAAA900101HYNBBB01','Prueba',1)
        self.assertEqual(self.s.one('trabajos',new)['expediente_id'],self.s.one('trabajos',self.t)['expediente_id'])
        self.s.save_work(f2,'AAAA900101HYNBBB01','Prueba',2);self.assertEqual(len(self.s.works()),2)
    def test_old_duplicates_grouped_preserved_and_selectable(self):
        f2=self.s.save_folio('OTRO/2026','2026-09-21')
        self.s.db.execute('DROP TRIGGER IF EXISTS no_nueva_identidad_duplicada')
        with self.s.db:
            second=self.s.db.execute("INSERT INTO trabajos(folio_id,curp,legajo,estado_desde) VALUES(?,?,?,?)",(f2,'AAAA900101HYNBBB01',1,'2026-09-21')).lastrowid
        rows=self.s.works();self.assertEqual(len(rows),1);self.assertEqual(rows[0]['registros'],2)
        self.assertEqual(len(self.s.associated(self.t)),2)
        self.s.prefer(second,'Este es el registro que contiene el trabajo actual');self.assertEqual(self.s.works()[0]['id'],second)
    def test_change_folio_requires_new_cycle_preserving_original(self):
        f2=self.s.save_folio('OTRO/2026','2026-09-21')
        with self.assertRaisesRegex(ValueError,'nuevo ciclo'):
            self.s.save_work(f2,'AAAA900101HYNBBB01','Prueba',1,ident=self.t,motivo='Reasignación de folio')
        self.assertEqual(self.s.one('trabajos',self.t)['folio_id'],self.f);self.assertEqual(len(self.s.works()),1)
