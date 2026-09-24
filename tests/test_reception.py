"""Recepción práctica por selección, siempre con confirmación y trazabilidad."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.core import Store
from app.intake import LoanLists,register_legajos
from app.operations import Operations
from app.reception import Reception


class ReceptionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.s=Store(workspace=self.root/'demo',operador='Receptor ficticio');self.service=Reception(self.s)
        path=self.root/'lista.csv'
        with path.open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow(['CURP','Nombre','Folio','No.'])
            for n,p in enumerate(('AAAA900101HYNBBB01','AAAB900101HYNBBB02','AAAC900101HYNBBB03'),7):w.writerow([p,'Persona ficticia '+str(n),'PRUEBA/2026',n])
        source=LoanLists(self.s);source.commit(source.preview(path))
        self.folio=self.s.rows('SELECT id FROM folios')[0]['id'];self.ids=[r['id'] for r in self.s.rows('SELECT id FROM prestamo_items ORDER BY id')]
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def accept(self,ids=None,leg=1):return self.service.accept(self.folio,ids or self.ids,'Físicos cotejados en ensayo',True,leg)
    def test_preview_preserves_pending_and_uses_imported_curps(self):
        before=self.s.db.total_changes;rows=self.service.preview(self.folio,self.ids,1)
        self.assertEqual(self.s.db.total_changes,before);self.assertTrue(all(r['legajo_propuesto']==1 and r['legajo_esperado'] is None for r in rows))
        self.assertTrue(all(r['resultado']=='Listo para aceptar' for r in rows));self.assertFalse(self.s.rows('SELECT * FROM trabajos'))
    def test_bulk_accept_creates_visible_cycles_without_retyping_curps(self):
        result=self.accept();self.assertEqual(result['aceptados'],3);self.assertEqual(len(self.s.works()),3)
        self.assertEqual(self.s.one('folios',self.folio)['recepcion_estado'],'Aceptado')
        self.assertIsNone(self.s.one('folios',self.folio)['recepcion_at'])
        for row in self.s.rows('SELECT * FROM prestamo_items'):
            self.assertEqual(row['curp_esperada'],row['curp_recibida']);self.assertEqual(row['legajo_recibido'],1)
            self.assertEqual(row['validado_por'],'Receptor ficticio');self.assertTrue(row['validado_at'])
            self.assertEqual(row['custodia'],'Prestado a Digitalización')
        self.assertTrue(all(w['recibido'] and w['recepcion']=='Aceptado' for w in self.s.works()))
        self.assertFalse(self.s.rows("SELECT * FROM pendientes WHERE tipo='Legajo de lista por confirmar' AND estado!='Revisado'"))
    def test_known_legajo_kept_when_common_default_applied_to_missing(self):
        register_legajos(self.s,self.ids[0],'2','Legajo confirmado')
        self.accept();self.assertEqual([w['legajo'] for w in self.s.works()],[2,1,1])
    def test_partial_selection_keeps_other_items_pending(self):
        self.accept([self.ids[1]])
        self.assertEqual(self.s.one('folios',self.folio)['recepcion_estado'],'Aceptado parcialmente')
        self.assertEqual(len(self.s.works()),1);self.assertEqual(len(self.s.rows("SELECT * FROM prestamo_items WHERE validacion='Pendiente'")),2)
    def test_requires_confirmation_and_explicit_legajo_for_unknown(self):
        with self.assertRaises(ValueError):self.service.accept(self.folio,self.ids,'Ensayo',False,1)
        with self.assertRaises(ValueError):self.accept(leg=None)
        with self.assertRaises(ValueError):self.accept(leg=0)
        self.assertFalse(self.s.rows('SELECT * FROM trabajos'));self.assertFalse(self.s.rows('SELECT * FROM expedientes'))
    def test_duplicate_selection_and_repeat_are_idempotent(self):
        result=self.accept(self.ids+self.ids);self.assertEqual(result['aceptados'],3)
        before=self.s.rows('SELECT * FROM prestamo_items');audit=self.s.rows('SELECT * FROM auditoria')
        result=self.accept();self.assertEqual(result['aceptados'],0);self.assertEqual(result['ya_aceptados'],3)
        self.assertEqual(self.s.rows('SELECT * FROM prestamo_items'),before);self.assertEqual(self.s.rows('SELECT * FROM auditoria'),audit)
    def test_late_failure_rolls_back_entire_selection(self):
        original=self.s.audit;before=self.s.rows('SELECT * FROM prestamo_items')
        def fail(entity,ident,action,*args):
            if entity=='prestamo_items' and ident==self.ids[1] and action=='validación':raise OSError('Escritura interrumpida')
            return original(entity,ident,action,*args)
        with patch.object(self.s,'audit',side_effect=fail):
            with self.assertRaises(OSError):self.accept()
        self.assertEqual(before,self.s.rows('SELECT * FROM prestamo_items'));self.assertFalse(self.s.rows('SELECT * FROM trabajos'));self.assertFalse(self.s.rows('SELECT * FROM expedientes'))
    def test_discrepancy_and_unlisted_require_individual_review(self):
        ops=Operations(self.s);ops.validate_item(self.ids[1],'Faltante',reason='No llegó')
        with self.assertRaisesRegex(ValueError,'individual'):self.accept()
        extra=ops.unlisted(self.folio,'AAAA900101HYNBBB01',4,'No está en lista')
        with self.assertRaises(ValueError):self.accept([extra])
        self.assertFalse(self.s.rows('SELECT * FROM trabajos'))
    def test_returned_and_inactive_cycle_not_reactivated(self):
        result=self.accept([self.ids[0]]);ops=Operations(self.s);ops.custody(self.ids[0],'En devolución','Salida')
        with self.assertRaisesRegex(ValueError,'custodia'):self.accept([self.ids[0]])
        self.accept([self.ids[1]])
        work=self.s.rows('SELECT id FROM trabajos WHERE prestamo_item_id=?',(self.ids[1],))[0]['id'];self.s.toggle('trabajos',work,'Baja')
        with self.assertRaisesRegex(ValueError,'inactivo'):self.accept([self.ids[1]])
    def test_empty_cross_folio_and_readonly_selections_rejected(self):
        with self.assertRaises(ValueError):self.service.preview(self.folio,[],1)
        other=self.s.save_folio('OTRO/2026','')
        with self.assertRaises(ValueError):self.service.accept(other,self.ids,'Ensayo',True,1)
        with self.assertRaises(ValueError):Reception(self.s,'Consulta').accept(self.folio,self.ids,'Ensayo',True,1)
        self.assertFalse(self.s.rows('SELECT * FROM trabajos'))
    def test_existing_physical_identity_cannot_be_overwritten(self):
        Operations(self.s).expect(self.folio,'AAAA900101HYNBBB01',1)
        with self.assertRaisesRegex(ValueError,'Ya existe'):self.accept()
        self.assertFalse(self.s.rows('SELECT * FROM trabajos'))
