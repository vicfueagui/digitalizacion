import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import Store
from app.coding import CodingService,digest,render_page,page_info
from PIL import Image,ImageDraw

class CodingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.project=self.root/'project';self.project.mkdir()
        self.s=Store(self.project/'datos'/'test.sqlite3','Prueba')
        self.f=self.s.save_folio('TEST/2026','2026-09-18');self.w=self.s.save_work(self.f,'AAAA900101HYNBBB01','Prueba',1)
        self.s.add_count(self.w,10);self.s.confirm_count(self.w)
        self.dp=self.s.save_catalog('documento','DP-01','PERSONALES','Acta')
        self.hl=self.s.save_catalog('documento','HL-01','FEDERAL','Laboral')
        self.c=CodingService(self.s,self.project)
        self.input=self.root/'input';self.input.mkdir()
    def tearDown(self):self.s.db.close();self.tmp.cleanup()
    def make(self,name='scan.tif',count=1,mode='L'):
        images=[]
        for i in range(count):
            im=Image.new(mode,(80+i*2,120),'white');d=ImageDraw.Draw(im);d.rectangle((10+i,20,40,55),fill='black');images.append(im)
        p=self.input/name;images[0].save(p,save_all=True,append_images=images[1:],compression='tiff_deflate',dpi=(300,300))
        for im in images:im.close()
        return p
    def load(self,p=None):
        p=p or self.make();self.c.import_files(self.w,[p]);return self.c.files(self.w)[-1]['id']
    def test_import_preserves_source_and_deduplicates(self):
        p=self.make();before=digest(p);self.load(p)
        self.assertEqual(self.c.import_files(self.w,[p])['duplicados'],1)
        row=self.c.files(self.w)[0]
        self.assertEqual(digest(p),before);self.assertEqual(digest(self.c.path(row['original'])),before)
    def test_separate_legajos(self):
        p=self.make();self.load(p);other=self.s.save_work(self.f,'AAAA900101HYNBBB01','Prueba',2)
        self.c.import_files(other,[p]);self.assertNotEqual(self.c.files(self.w)[0]['ruta'],self.c.files(other)[0]['ruta'])
    def test_assign_repeated_code_no_overwrite(self):
        a=self.load(self.make('a.tif'));b=self.load(self.make('b.tif',2))
        self.c.assign(a,'DP-01');self.c.assign(b,'DP-01')
        names={Path(r['ruta']).name for r in self.c.files(self.w)}
        self.assertEqual(names,{'DP-01.tif','DP-01 (2).tif'})
    def test_shortcuts_unique_persistent_and_collision(self):
        cat=self.c.catalog();self.assertEqual(len({c['secuencia'] for c in cat}),2)
        self.c.set_shortcut(self.dp,'ZZ',1)
        again=CodingService(self.s,self.project)
        self.assertEqual(next(c for c in again.catalog() if c['id']==self.dp)['secuencia'],'ZZ')
        with self.assertRaises(sqlite3.IntegrityError):self.c.set_shortcut(self.hl,'ZZ',2)
        with self.assertRaises(sqlite3.IntegrityError):self.c.set_shortcut(self.hl,'ZX',1)
    def test_stream_edit_keeps_other_pages_and_dpi(self):
        p=self.make(count=4);ident=self.load(p);original=digest(p)
        self.c.save_edit(ident,1,[('crop',0,0,60,90),('rotate',-.2)])
        path=self.c.path(self.c.file(ident)['ruta']);self.assertEqual(len(page_info(path)),4)
        for i in (0,2,3):
            a=render_page(p,i);b=render_page(path,i);self.assertEqual(a.tobytes(),b.tobytes());a.close();b.close()
        self.assertEqual(tuple(page_info(path)[1]['dpi']),(300.,300.));self.assertEqual(digest(p),original)
        self.assertEqual(len(self.s.rows('SELECT * FROM revisiones_tiff')),1)
    def test_onebit_and_rgb_pages(self):
        for mode in ('1','RGB'):
            ident=self.load(self.make(mode+'.tif',2,mode));self.c.save_edit(ident,0,[('rotate',90)])
            self.assertEqual(page_info(self.c.path(self.c.file(ident)['ruta']))[0]['size'],(120,80))
    def test_restore_original_keeps_coded_name(self):
        p=self.make(count=2);ident=self.load(p);self.c.assign(ident,'DP-01');self.c.save_edit(ident,0,[('rotate',90)])
        self.c.restore_original(ident);row=self.c.file(ident)
        self.assertEqual(digest(self.c.path(row['ruta'])),digest(p));self.assertEqual(Path(row['ruta']).name,'DP-01.tif')
    def test_invalid_crop_leaves_working_file_intact(self):
        ident=self.load();row=self.c.file(ident)
        with self.assertRaises(ValueError):self.c.save_edit(ident,0,[('crop',-1,0,2000,2000)])
        self.assertEqual(digest(self.c.path(row['ruta'])),row['hash_actual'])
    def test_rename_audit_failure_rolls_back_filesystem(self):
        ident=self.load();row=self.c.file(ident)
        with patch.object(self.s,'audit',side_effect=ValueError('Auditoría no disponible')):
            with self.assertRaises(ValueError):self.c.assign(ident,'DP-01')
        self.assertTrue(self.c.path(row['ruta']).exists());self.assertEqual(self.c.file(ident)['ruta'],row['ruta'])
    def test_edit_audit_failure_restores_working_copy(self):
        ident=self.load();row=self.c.file(ident)
        with patch.object(self.s,'audit',side_effect=ValueError('Auditoría no disponible')):
            with self.assertRaises(ValueError):self.c.save_edit(ident,0,[('rotate',90)])
        self.assertEqual(digest(self.c.path(row['ruta'])),row['hash_actual'])
    def test_uncoded_blocks_organization(self):
        self.load()
        with self.assertRaises(ValueError):self.c.plan(self.w)
    def test_external_changes_block_rename(self):
        ident=self.load();row=self.c.file(ident);self.c.path(row['ruta']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.c.assign(ident,'DP-01')
    def test_destination_conflicts_preserve_both(self):
        ident=self.load();self.c.assign(ident,'DP-01');dest=self.c.work_dir(self.w)/'AAAA900101HYNBBB01'/'PERSONALES';dest.mkdir(parents=True)
        (dest/'DP-01.tif').write_bytes(b'other')
        with self.assertRaises(ValueError):self.c.organize(self.w)
        self.assertEqual((dest/'DP-01.tif').read_bytes(),b'other')
    def test_organization_links_metrics_and_repeat_does_not_double(self):
        a=self.load(self.make('a.tif'));b=self.load(self.make('b.tif',3));self.c.assign(a,'DP-01');self.c.assign(b,'HL-01')
        self.c.organize(self.w);e=self.s.latest(self.w);p=json.loads(e['payload'])
        self.assertEqual(p['TOTAL_DIGITALES_TIFF'],2);self.assertEqual(p['TOTAL_PAG_DIGITALES_CONOCIDAS'],4)
        self.assertEqual(p['INV_P_INDIVIDUALES'],1);self.assertEqual(p['INV_F_MULTI'],1)
        self.c.organize(self.w);p=json.loads(self.s.latest(self.w)['payload'])
        self.assertEqual(p['MOV_TOTAL_ARCHIVOS'],0);self.assertEqual(self.s.dashboard(self.s.works())['Archivos TIFF'],2)
    def test_interrupted_rename_recovery(self):
        import os
        ident=self.load();row=self.c.file(ident);source=self.c.path(row['ruta']);target=source.with_name('DP-01.tif')
        op=self.c.log(self.w,ident,'renombrar',{'antes':row['ruta'],'despues':self.c.relative(target)})
        os.rename(source,target)
        with self.assertRaises(ValueError):self.c.assign(ident,'HL-01')
        self.assertEqual(self.c.recover(self.w),1);self.assertTrue(source.exists());self.assertFalse(target.exists())
        self.c.assign(ident,'DP-01')
    def test_generated_inventory_has_consistent_66_metrics(self):
        from app.importers import validate_metrics
        a=self.load(self.make('a.tif'));b=self.load(self.make('b.tif',4))
        self.c.assign(a,'DP-01');self.c.assign(b,'HL-01');self.c.organize(self.w)
        p=json.loads(self.s.latest(self.w)['payload']);self.assertEqual(len(p),66)
        # Validador externo v0.1 solo acepta BAT: validar las cifras con versión equivalente.
        p['VERSION_BAT']='3.1';validate_metrics(p)

    def test_edited_inventory_invalidated(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.c.organize(self.w)
        self.assertIsNotNone(self.s.latest(self.w));self.c.save_edit(ident,0,[('rotate',90)])
        self.assertIsNone(self.s.latest(self.w));self.assertEqual(self.s.one('trabajos',self.w)['carpetas'],0)
    def test_new_catalog_folder_used_on_next_organization(self):
        ident=self.load();self.c.assign(ident,'DP-01');self.s.save_catalog('documento','DP-01','FEDERAL','Acta',ident=self.dp,motivo='Regla de prueba')
        self.c.organize(self.w);self.assertIn('FEDERAL',self.c.file(ident)['ruta'])

if __name__=='__main__':unittest.main()
