import unittest
from pathlib import Path
from app.assets import canonical
from app.backup import create_backup,verify_backup
from app.coding import digest,render_page
import test_coding as fixture


class AssetTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    load=fixture.CodingTests.load
    def test_rename_keeps_logical_and_binary_ids(self):
        ident=self.load();before=self.c.file(ident)
        self.c.assign(ident,'DP-01');self.c.rename(ident,'DP-01 prueba.tif')
        after=self.c.file(ident)
        self.assertEqual(before['documento_id'],after['documento_id']);self.assertEqual(before['version_id'],after['version_id'])
        self.assertEqual(after['nombre_origen'],'scan.tif')
        self.assertNotIn('(',canonical(self.s,after))
    def test_distinct_content_same_source_name_preserved(self):
        p=self.make('igual.tif');first=self.load(p)
        p=self.make('igual.tif',3);second=self.load(p)
        a=self.c.file(first);b=self.c.file(second)
        self.assertNotEqual(a['documento_id'],b['documento_id']);self.assertNotEqual(a['ruta'],b['ruta'])
        self.assertEqual(digest(self.c.path(a['ruta'])),a['hash_actual'])
    def test_explicit_duplicate_adoption_preserves_both(self):
        p=self.make();first=self.load(p);second=p.with_name('otra copia.tif');second.write_bytes(p.read_bytes())
        result=self.c.import_files(self.w,[second],allow_duplicates=True)
        self.assertEqual(result['duplicados'],1);self.assertEqual(result['importados'],1)
        self.assertEqual(len(self.c.files(self.w)),2);self.assertTrue(p.exists());self.assertTrue(second.exists())
    def test_edit_creates_new_immutable_version_keeps_other_pages(self):
        ident=self.load(self.make(count=3));old=self.c.file(ident)
        before=render_page(self.c.path(old['ruta']),2).tobytes()
        self.c.save_edit(ident,0,[('rotate',90)])
        new=self.c.file(ident)
        self.assertEqual(new['documento_id'],old['documento_id']);self.assertNotEqual(new['version_id'],old['version_id'])
        self.assertEqual(render_page(self.c.path(new['ruta']),2).tobytes(),before)
        for v in self.s.rows('SELECT * FROM versiones_archivo'):
            self.assertEqual(digest(self.c.path(v['ruta'])),v['sha256'])
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            with self.s.db:self.s.db.execute("UPDATE versiones_archivo SET sha256='alterado' WHERE id=?",(old['version_id'],))
    def test_rescan_links_same_document(self):
        first=self.load();self.c.assign(first,'DP-01');old=self.c.file(first)
        p=self.make('rescan.tif');from PIL import Image
        with Image.open(p) as im:changed=im.copy()
        changed.putpixel((0,0),0);changed.save(p);changed.close()
        second=self.load(p);correction=self.c.mark_correction(first,1,'Hoja física de prueba','Borrosa')
        self.c.replace_correction(correction,second,'Comprobación explícita de la nueva imagen')
        new=self.c.file(second)
        self.assertEqual(new['documento_id'],old['documento_id']);self.assertNotEqual(new['version_id'],old['version_id'])
        with self.assertRaises(ValueError):self.c.restore_removed(first,'No debe crear dos versiones activas')
    def test_retirement_restore_retains_identity_and_history(self):
        ident=self.load();old=self.c.file(ident)
        self.c.exclude(ident,'Prueba');self.c.restore_removed(ident,'Retiro equivocado')
        self.assertEqual(self.c.file(ident)['documento_id'],old['documento_id'])
        self.assertEqual(len(self.s.rows("SELECT * FROM auditoria WHERE entidad='archivos_tiff' AND registro=? AND accion IN ('retirar','restaurar retirado')",(str(ident),))),2)
    def test_backup_verifies_all_versions(self):
        ident=self.load();self.c.save_edit(ident,0,[('rotate',90)])
        output=create_backup(self.s,self.root/'allversions');verify_backup(output)
        for v in self.s.rows('SELECT * FROM versiones_archivo'):
            self.assertTrue((output/v['ruta']).exists())
