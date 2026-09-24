"""Métricas de BI del ámbito seleccionado, sin releer documentos ni snapshots."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from app.core import Store
from app.coding import CodingService
from app.operations import Operations
from app.dashboard import Dashboard


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.s=Store(workspace=self.root/'demo');self.d=Dashboard(self.s)
        self.f=self.s.save_folio('UNO/2026','');self.other=self.s.save_folio('DOS/2026','')
        self.a=self.s.save_work(self.f,'AAAA900101HYNBBB01','Persona ficticia',1)
        self.b=self.s.save_work(self.f,'AAAA900101HYNBBB01','Persona ficticia',2)
        self.c=self.s.save_work(self.other,'AAAB900101HYNBBB02','Otra ficticia',1)
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def test_empty_scope_has_zero_counts_and_no_fake_percent(self):
        data=self.d.snapshot([])
        self.assertEqual(data['metrica']['Trabajos activos'],0);self.assertIsNone(data['metrica']['Avance de cierre (%)'])
        self.assertTrue(all(r['value']==0 and r['percent'] is None for r in data['etapas']+data['cobertura']))
    def test_stage_totals_groups_and_legajos_use_same_denominator(self):
        with self.s.db:
            self.s.db.execute("UPDATE trabajos SET estado='Revisión en curso',digitalizador='Persona A' WHERE id=?",(self.b,))
            self.s.db.execute("UPDATE trabajos SET estado='Expediente cerrado',digitalizador='Persona A' WHERE id=?",(self.c,))
        data=self.d.snapshot(self.s.works())
        self.assertEqual(data['metrica']['CURP distintas'],2);self.assertEqual(data['metrica']['Trabajos activos'],3)
        self.assertEqual(sum(r['value'] for r in data['etapas']),3)
        self.assertEqual(data['metrica']['Avance de cierre (%)'],33.3)
        self.assertEqual(sum(r['expedientes'] for r in data['grupos']['folio']),3)
        self.assertEqual(sum(r['expedientes'] for r in data['grupos']['digitalizador']),3)
    def test_filtered_and_inactive_records_do_not_leak_into_metrics(self):
        self.s.toggle('trabajos',self.b,'Baja de prueba')
        data=self.d.snapshot(self.s.works(folio='UNO/2026',activos=False),{'folio':'UNO/2026'})
        self.assertEqual(data['metrica']['Trabajos activos'],1);self.assertEqual(data['expedientes'][0]['id'],self.a)
        self.assertEqual(data['filtros']['folio'],'UNO/2026');self.assertEqual(len(data['grupos']['folio']),1)
    def test_tiff_counts_are_active_metadata_without_hashing_or_reading_files(self):
        p=self.root/'multipagina.tif';a=Image.new('L',(40,50),'white');b=Image.new('L',(40,50),'black');a.save(p,save_all=True,append_images=[b]);a.close();b.close()
        coding=CodingService(self.s);coding.import_files(self.a,[p]);self.s.save_catalog('documento','DP-01','PERSONALES','Prueba')
        self.s.add_count(self.a,2);self.s.confirm_count(self.a)
        file=coding.files(self.a)[0];coding.assign(file['id'],'DP-01');coding.organize(self.a)
        with patch('app.delivery.Deliveries.current_validation',side_effect=AssertionError('BI no valida binarios')),patch('app.backup.sha256',side_effect=AssertionError('BI no hace hashes')):
            data=self.d.snapshot(self.s.works())
        self.assertEqual(data['metrica']['Archivos TIFF'],1);self.assertEqual(data['metrica']['Páginas conocidas'],2)
        coding.exclude(file['id'],'Retiro de prueba');data=self.d.snapshot(self.s.works())
        self.assertEqual(data['metrica']['Archivos TIFF'],0);self.assertEqual(data['metrica']['Páginas conocidas'],0)
    def test_coverage_counts_confirmed_receipt_and_count(self):
        item=self.s.one('trabajos',self.a)['prestamo_item_id'];Operations(self.s).validate_item(item,'Aceptado','AAAA900101HYNBBB01',1,'Cotejado')
        self.s.add_count(self.a,3);self.s.confirm_count(self.a)
        data=self.d.snapshot(self.s.works());rows={r['label']:r for r in data['cobertura']}
        self.assertEqual(rows['Recepción aceptada']['value'],1);self.assertEqual(rows['Conteo confirmado']['percent'],33.3)
        self.assertEqual(rows['Con TIFF registrados']['value'],0)
    def test_pending_without_cycle_is_global_and_separate_from_filtered_totals(self):
        Operations(self.s).expect(self.other,'AAAC900101HYNBBB03',2)
        data=self.d.snapshot(self.s.works(folio='UNO/2026'))
        self.assertEqual(data['sin_ciclo_global'],1);self.assertEqual(data['metrica']['Trabajos activos'],2)
    def test_export_preserves_scope_values_and_zero_denominators(self):
        data=self.d.snapshot([],{'folio':'NO EXISTE'});dest=self.d.export(data,self.root/'export')
        context=json.loads((dest/'contexto.json').read_text());self.assertEqual(context['filtros']['folio'],'NO EXISTE')
        self.assertIn('Cerrados', (dest/'etapas.csv').read_text(encoding='utf-8-sig'))
        self.assertTrue((dest/'por_digitalizador.csv').exists())
        with self.assertRaises(FileExistsError):self.d.export(data,dest)
