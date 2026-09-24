import unittest
from app.reporting import Reporting
from app.operations import Operations,KANBAN
from app.delivery import Deliveries
from app.review import Reviews
from app.backup import create_backup,restore_backup,verify_backup
from app.core import Store,STATES
import test_coding as fixture


class ProjectionTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    load=fixture.CodingTests.load
    def test_received_360_has_no_invented_digital_metrics(self):
        report=Reporting(self.s).summary(self.w)
        self.assertIsNone(report['Digital vigente']['archivos'])
        self.assertEqual(report['Custodia física']['custodia'],'Registrado')
        self.assertIsNone(report['Custodia física']['validado_at'])
        self.assertIsNone(report['Dato legado declarado']['No_digitales'])
    def test_process_actions_update_card_without_drag(self):
        r=Reporting(self.s);self.assertEqual(r.card(self.w)['columna'],KANBAN[0])
        for stage in STATES[1:5]:self.s.change_state(self.w,stage,'Proceso ficticio')
        self.assertEqual(r.card(self.w)['estado'],'Expediente escaneado')
        self.s.change_state(self.w,'Codificación en curso','Iniciar codificación')
        self.assertEqual(r.card(self.w)['columna'],KANBAN[1]);self.assertEqual(r.card(self.w)['estado'],'Codificación en curso')
    def test_observation_and_resubmission_control_column(self):
        ident=self.load();self.c.assign(ident,'DP-01');d=Deliveries(self.s);v1=d.prepare(self.w);review=Reviews(self.s);session=review.begin(v1)
        obs=review.observe(session,'Conteo','Verificar referencia física','Operador')
        self.assertEqual(Reporting(self.s).card(self.w)['columna'],KANBAN[3])
        self.c.save_edit(ident,0,[('rotate',90)]);v2=d.prepare(self.w)
        review.update_observation(obs,'Resuelta','Corregido y enviado',v2)
        self.assertEqual(Reporting(self.s).card(self.w)['columna'],KANBAN[2])
    def test_final_360_contains_loan_history_manifest_and_changes(self):
        item=self.s.one('trabajos',self.w)['prestamo_item_id'];o=Operations(self.s)
        o.validate_item(item,'Aceptado','AAAA900101HYNBBB01',1,'Recibido');o.assign('Digitalizador ficticio','Inicio',work=self.w)
        ident=self.load();self.c.assign(ident,'DP-01');d=Deliveries(self.s);delivery=d.prepare(self.w);r=Reviews(self.s);r.begin(delivery);r.approve(delivery,'Validación final')
        summary=Reporting(self.s).summary(self.w)
        self.assertEqual(summary['Proceso']['Calidad'],'Aprobado');self.assertEqual(summary['Custodia física']['custodia'],'Prestado a Digitalización')
        self.assertTrue(summary['Asignaciones']);self.assertTrue(summary['Línea de tiempo']);self.assertTrue(summary['Entregas'][0]['manifest_hash'])
        self.assertEqual(len(summary['Cambios de última entrega']['agregados']),1)
        out=Reporting(self.s).export_summary(self.w);self.assertIn('Expediente 360',out.read_text())
    def test_kpi_counts_active_inventory_not_snapshots(self):
        ident=self.load();self.c.assign(ident,'DP-01');d=Deliveries(self.s);d.prepare(self.w);d.prepare(self.w)
        self.assertEqual(Reporting(self.s).facts()['tiff_activos'],1)
        self.assertEqual(self.s.dashboard(self.s.works())['Archivos TIFF'],1)
        self.c.exclude(ident,'Retiro');self.assertEqual(Reporting(self.s).facts()['tiff_activos'],0)
    def test_board_filters_responsible_loan_priority_and_observations(self):
        item=self.s.one('trabajos',self.w)['prestamo_item_id'];o=Operations(self.s)
        o.validate_item(item,'Aceptado','AAAA900101HYNBBB01',1,'Recibido');o.assign('Revisor ficticio','Inicio',work=self.w,role='Revisor')
        o.card_metadata(self.w,'Nota','Alta')
        r=Reporting(self.s)
        self.assertEqual(len(r.cards(responsable='Revisor',custodia='Prestado',prioridad='Alta',con_observaciones='No')),1)
        self.assertEqual(r.cards(con_observaciones='Sí'),[])
    def test_backup_restore_keeps_delivery_and_binary_versions(self):
        ident=self.load();self.c.assign(ident,'DP-01');d=Deliveries(self.s);v1=d.prepare(self.w)
        self.c.save_edit(ident,0,[('rotate',90)]);v2=d.prepare(self.w)
        backup=create_backup(self.s,self.root/'backup-completo');verify_backup(backup)
        restored=restore_backup(backup,self.root/'restaurado');s=Store(workspace=restored)
        try:
            service=Deliveries(s);service.verify(v1);service.verify(v2)
            self.assertEqual(len(service.diff(v1,v2)['reemplazados']),1)
        finally:s.db.close()
    def test_empty_denominator_is_unknown_and_csvs_are_relational(self):
        other=Store(workspace=self.root/'empty')
        try:self.assertIsNone(Reporting(other).facts()['porcentaje_ciclos_con_observaciones'])
        finally:other.db.close()
        folder=self.root/'exports';self.s.export(self.s.works(),folder)
        for table in ('expedientes','prestamo_items','entregas','observaciones_revision'):
            self.assertTrue((folder/(table+'.csv')).is_file())
    def test_legacy_cycle_has_explicit_unknown_folio_and_no_receipt(self):
        work=Operations(self.s).legacy_cycle('AAAA900101HYNBBB01',1,'Persona ficticia')
        row=self.s.one('trabajos',work);self.assertEqual(row['procedencia'],'Legado importado')
        self.assertIsNone(self.s.one('folios',row['folio_id'])['recepcion_at'])
        self.assertEqual(row['expediente_id'],self.s.one('trabajos',self.w)['expediente_id'])
