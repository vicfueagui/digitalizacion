"""Aceptación del modelo maestro/préstamo/ciclo con datos ficticios."""
import tempfile
import unittest
from pathlib import Path
from app.core import Store
from app.operations import Operations

PERSON='AAAA900101HYNBBB01'


class LoanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.s=Store(workspace=self.root/'datos ficticios',operador='Revisor ficticio');self.o=Operations(self.s)
        self.f=self.s.save_folio('PRUEBA/1','')
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def accepted(self,folio=None,legajo=1):
        item=self.o.expect(folio or self.f,PERSON,legajo,'Caja ficticia')
        self.o.validate_item(item,'Aceptado',PERSON,legajo,'Comprobación física de prueba')
        return self.o.create_cycle(item)
    def test_same_identity_new_folio_reuses_master_new_cycle(self):
        first=self.accepted();other=self.s.save_folio('PRUEBA/2','');second=self.accepted(other)
        a=self.s.one('trabajos',first);b=self.s.one('trabajos',second)
        self.assertEqual(a['expediente_id'],b['expediente_id']);self.assertNotEqual(a['id'],b['id'])
        self.assertNotEqual(a['prestamo_item_id'],b['prestamo_item_id'])
        self.assertEqual(len(self.s.rows('SELECT * FROM expedientes')),1)
    def test_legajo_two_is_separate_master(self):
        self.accepted();self.accepted(legajo=2)
        self.assertEqual(len(self.s.rows('SELECT * FROM expedientes')),2)
    def test_twenty_items_partial_receipt_and_no_false_acceptance(self):
        items=[self.o.expect(self.f,PERSON,legajo) for legajo in range(1,21)]
        self.o.validate_item(items[0],'Aceptado',PERSON,1,'Revisado')
        self.o.validate_item(items[1],'Faltante',reason='No se entregó físicamente')
        self.o.validate_item(items[2],'Discrepancia',PERSON,4,'El legajo recibido no coincide')
        with self.assertRaises(ValueError):self.o.validate_item(items[3],'Aceptado',PERSON,99,'No coincide')
        self.assertEqual(self.s.one('folios',self.f)['recepcion_estado'],'Aceptado parcialmente')
        self.assertEqual(len(self.s.rows("SELECT * FROM prestamo_items WHERE validacion='Pendiente'")),17)
        with self.assertRaises(ValueError):self.o.create_cycle(items[1])
        row=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(items[0],))[0]
        self.assertEqual(row['validado_por'],'Revisor ficticio');self.assertTrue(row['validado_at'])
    def test_reassignment_keeps_history_and_collaboration(self):
        work=self.accepted();self.o.assign('Persona A','Inicio',work=work)
        self.o.assign('Persona B','Reasignación',work=work)
        self.o.assign('Persona C','Apoyo',work=work,collaborate=True)
        rows=self.s.rows('SELECT * FROM asignaciones ORDER BY id')
        self.assertIsNotNone(rows[0]['fin']);self.assertIsNone(rows[1]['fin']);self.assertIsNone(rows[2]['fin'])
        self.assertEqual(self.s.one('trabajos',work)['digitalizador'],'Persona B')
    def test_custody_is_independent_of_process(self):
        work=self.accepted();item=self.s.one('trabajos',work)['prestamo_item_id']
        with self.s.db:self.s.db.execute("UPDATE trabajos SET estado='Expediente cerrado' WHERE id=?",(work,))
        self.assertEqual(self.s.rows('SELECT custodia FROM prestamo_items WHERE id=?',(item,))[0]['custodia'],'Prestado a Digitalización')
        self.o.custody(item,'En devolución','Salida física')
        self.o.custody(item,'Devuelto','Entrega física','Archivo ficticio')
        self.o.custody(item,'Devolución aceptada','Acuse revisado','Archivo ficticio')
        self.assertEqual(self.s.one('trabajos',work)['estado'],'Expediente cerrado')
    def test_readonly_role_cannot_mutate(self):
        with self.assertRaises(ValueError):Operations(self.s,'Consulta').expect(self.f,PERSON,1)
    def test_note_priority_does_not_change_stage(self):
        work=self.accepted();before=self.s.one('trabajos',work)
        self.o.card_metadata(work,'Nota ficticia','Alta','Ensayo')
        after=self.s.one('trabajos',work)
        self.assertEqual(before['estado'],after['estado']);self.assertEqual(before['estado_desde'],after['estado_desde'])
    def test_unlisted_receipt_preserves_original_list_and_needs_confirmation(self):
        item=self.o.unlisted(self.f,PERSON,1,'Llegó un expediente no relacionado')
        with self.assertRaises(ValueError):self.o.create_cycle(item)
        with self.assertRaises(ValueError):self.o.validate_item(item,'Aceptado',PERSON,1,'Sin aceptación de extra')
        self.o.validate_item(item,'Aceptado',PERSON,1,'Origen confirmó el extra',accept_unlisted=True)
        work=self.o.create_cycle(item)
        row=self.s.rows('SELECT * FROM prestamo_items WHERE id=?',(item,))[0]
        self.assertEqual(row['curp_esperada'],'');self.assertEqual(row['curp_recibida'],PERSON)
        self.assertEqual(self.s.one('trabajos',work)['prestamo_item_id'],item)
    def test_adding_expected_item_reopens_partial_receipt(self):
        self.accepted();self.assertEqual(self.s.one('folios',self.f)['recepcion_estado'],'Aceptado')
        self.o.expect(self.f,PERSON,2)
        self.assertEqual(self.s.one('folios',self.f)['recepcion_estado'],'Aceptado parcialmente')

    def test_registering_draft_cycle_reopens_partial_receipt(self):
        self.accepted()
        self.s.save_work(self.f,PERSON,'Persona ficticia',2)
        self.assertEqual(self.s.one('folios',self.f)['recepcion_estado'],'Aceptado parcialmente')
