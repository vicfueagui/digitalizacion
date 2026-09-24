import unittest
import os
from unittest.mock import patch
from app.legacy import LegacyImport
from app.backup import sha256
from app.coding import CodingService
import test_coding as fixture


class LegacyTests(unittest.TestCase):
    make=fixture.CodingTests.make
    tearDown=fixture.CodingTests.tearDown
    def setUp(self):
        fixture.CodingTests.setUp(self)
        self.source=self.input/'AAAA900101HYNBBB01'
        (self.source/'PERSONALES').mkdir(parents=True);(self.source/'FEDERAL').mkdir()
        self.legacy=LegacyImport(self.s)
    def put(self,name='DP-01.tif',folder='PERSONALES',count=1):
        p=self.make('incoming.tif',count);dest=self.source/folder/name;dest.write_bytes(p.read_bytes());return dest
    def test_valid_folder_readonly_and_snapshot_does_not_adopt(self):
        p=self.put();before=(sha256(p),p.stat().st_mtime_ns,sha256(self.s.path))
        report=self.legacy.preflight(self.w,self.source)
        self.assertTrue(report['pasa']);self.assertEqual(report['totales']['paginas_conocidas'],1)
        self.assertEqual(before,(sha256(p),p.stat().st_mtime_ns,sha256(self.s.path)))
        ident=self.legacy.register(self.w,report)
        self.assertEqual(self.s.rows('SELECT estado FROM importaciones_legado WHERE id=?',(ident,))[0]['estado'],'Externa / no gestionada')
        self.assertFalse(self.c.files(self.w));self.assertEqual(sha256(p),before[0])
    def test_txt_warns_and_is_never_adopted(self):
        self.put();(self.source/'PERSONALES/notas.txt').write_text('Contexto ficticio')
        report=self.legacy.preflight(self.w,self.source)
        self.assertTrue(report['pasa']);self.assertEqual(len(report['no_tiff']),1)
        self.legacy.register(self.w,report,adopt=True);self.assertEqual(len(self.c.files(self.w)),1)
    def test_unknown_and_inactive_codes_fail_preflight(self):
        self.put('DP-99.tif');report=self.legacy.preflight(self.w,self.source)
        self.assertFalse(report['pasa']);self.assertTrue(any(i['regla']=='codigo_desconocido' for i in report['problemas']))
        with self.assertRaises(ValueError):self.legacy.register(self.w,report,True)
    def test_correct_code_wrong_folder_detected(self):
        self.put(folder='FEDERAL');report=self.legacy.preflight(self.w,self.source)
        self.assertFalse(report['pasa']);self.assertTrue(any(i['regla']=='ubicacion' for i in report['problemas']))
    def test_same_name_different_content_collision(self):
        self.put('DP-01.tif','PERSONALES',1);self.put('dp-01.TIF','FEDERAL',2)
        report=self.legacy.preflight(self.w,self.source)
        self.assertFalse(report['pasa']);self.assertEqual(len(report['colisiones']),1)
    def test_same_content_different_names_preserved_in_adoption(self):
        p=self.put();self.put('DP-01 copia.tif');before=sha256(p)
        report=self.legacy.preflight(self.w,self.source)
        self.assertTrue(report['pasa']);self.assertEqual(len(report['duplicados_exactos']),1)
        self.legacy.register(self.w,report,True)
        self.assertEqual(len(self.c.files(self.w)),2);self.assertEqual(sha256(p),before)
    def test_unreadable_pages_remain_unknown(self):
        self.put();(self.source/'PERSONALES/DP-01 malo.tif').write_bytes(b'no tiff')
        report=self.legacy.preflight(self.w,self.source)
        self.assertFalse(report['pasa']);self.assertEqual(report['totales']['paginas_conocidas'],1)
        self.assertEqual(report['totales']['paginas_desconocidas'],1)
    def test_adoption_hashes_match_and_source_unchanged(self):
        p=self.put(count=3);before=sha256(p);report=self.legacy.preflight(self.w,self.source)
        ident=self.legacy.register(self.w,report,True);row=self.c.files(self.w)[0]
        self.assertEqual(sha256(self.c.path(row['original'])),before);self.assertEqual(sha256(self.c.path(row['ruta'])),before)
        self.assertEqual(sha256(p),before);self.assertEqual(row['paginas'],3)
        self.assertEqual(self.s.rows('SELECT estado FROM importaciones_legado WHERE id=?',(ident,))[0]['estado'],'Completada')
    def test_changed_source_requires_new_preflight(self):
        p=self.put();report=self.legacy.preflight(self.w,self.source);p.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'cambiaron'):self.legacy.register(self.w,report,True)
        self.assertFalse(self.c.files(self.w))
    def test_partial_adoption_resume_does_not_duplicate(self):
        self.put();report=self.legacy.preflight(self.w,self.source)
        with patch.object(CodingService,'assign',side_effect=OSError('Error tras copiar')):
            with self.assertRaises(OSError):self.legacy.register(self.w,report,True)
        self.assertEqual(len(self.c.files(self.w)),1)
        self.legacy.register(self.w,report,True)
        self.assertEqual(len(self.c.files(self.w)),1)
        self.assertEqual(len(self.s.rows('SELECT * FROM importaciones_legado')),1)
    @unittest.skipIf(os.name=='nt','Crear symlink requiere privilegios en Windows; verificar junctions en oficina')
    def test_source_link_is_reported_without_descending(self):
        self.put();(self.source/'bucle').symlink_to(self.source,target_is_directory=True)
        report=self.legacy.preflight(self.w,self.source)
        self.assertFalse(report['pasa']);self.assertEqual(report['totales']['tiff'],1)
        self.assertTrue(any(i['regla']=='enlace' for i in report['problemas']))
