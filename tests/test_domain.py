import csv
import os
import json
import tempfile
import unittest
from pathlib import Path
from app.core import Store, ROOT, STATES
from app.importers import import_excel,import_csv,parse_csv,validate_metrics

A='AAAA900101HYNBBB01'

class DomainTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.s=Store(Path(self.temp.name)/'test.sqlite3','Prueba')
        self.f=self.s.save_folio('TEST/2026','2026-09-18')
        self.t=self.s.save_work(self.f,A,'Ejemplo',1)
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def count(self):
        self.s.add_count(self.t,10);self.s.add_count(self.t,5);self.s.confirm_count(self.t)
    def test_legajos_separate_and_identity_unique(self):
        t2=self.s.save_work(self.f,A,'Ejemplo',2)
        self.assertNotEqual(self.t,t2)
        with self.assertRaises(Exception):self.s.save_work(self.f,A,'Ejemplo',1)
        self.assertEqual(len(self.s.works()),2)
    def test_identity_cannot_be_silently_changed(self):
        with self.assertRaises(ValueError):self.s.save_work(self.f,A,'Ejemplo',2,ident=self.t)
    def test_count_correction_soft_delete(self):
        c1=self.s.add_count(self.t,10);c2=self.s.add_count(self.t,8)
        self.s.edit_count(c1,12,'Error de captura');self.s.edit_count(c2,8,'Duplicado',True)
        self.assertEqual(self.s.confirm_count(self.t),12)
        self.assertEqual(len(self.s.rows('SELECT * FROM conteos')),2)
    def test_count_must_be_positive_integer(self):
        for value in ('-1','1.2','abc','0'):
            with self.assertRaises(ValueError):self.s.add_count(self.t,value)
    def test_outside_is_subset_not_added(self):
        self.s.save_work(self.f,A,'Ejemplo',1,fuera_broche=3,ident=self.t)
        self.count();self.assertEqual(self.s.one('trabajos',self.t)['fisicos'],15)
    def test_outside_cannot_exceed_total(self):
        self.s.save_work(self.f,A,'Ejemplo',1,fuera_broche=20,ident=self.t)
        self.s.add_count(self.t,15)
        with self.assertRaises(ValueError):self.s.confirm_count(self.t)
    def test_stage_cannot_skip_or_close_without_checks(self):
        with self.assertRaises(ValueError):self.s.change_state(self.t,STATES[-1],'Prueba')
        self.count()
        for state in STATES[1:-1]:self.s.change_state(self.t,state,'Avance probado')
        with self.assertRaises(ValueError):self.s.change_state(self.t,STATES[-1],'Cerrar')
    def test_reopen_preserves_intervals(self):
        self.count();self.s.change_state(self.t,STATES[1],'Iniciar');self.s.change_state(self.t,STATES[2],'Completar')
        with self.assertRaises(ValueError):self.s.add_count(self.t,3)
        self.s.change_state(self.t,STATES[1],'Recontar');self.s.add_count(self.t,3)
        self.assertEqual(self.s.confirm_count(self.t),18)
        self.assertEqual(len(self.s.rows('SELECT * FROM historial WHERE fin IS NULL')),1)
    def test_audit_requires_reason_and_rolls_back(self):
        with self.assertRaises(ValueError):self.s.toggle('trabajos',self.t,'')
        self.assertEqual(self.s.one('trabajos',self.t)['activo'],1)
    def test_catalog_codes_immutable(self):
        c=self.s.save_catalog('documento','DP-1','PERSONALES','Ejemplo')
        self.assertEqual(self.s.one('catalogos',c)['codigo'],'DP-01')
        with self.assertRaises(ValueError):self.s.save_catalog('documento','DP-02','PERSONALES','Cambio',ident=c)
        self.s.toggle('catalogos',c,'Dejar de usar')
        self.assertEqual(self.s.one('catalogos',c)['activo'],0)
    def test_incident_lifecycle(self):
        cat=self.s.save_catalog('incidencia','ROTO','','Documento roto')
        inc=self.s.save_incident(self.t,cat,'DP-01','Esquina rota')
        self.s.save_incident(self.t,cat,'DP-01','Esquina rota','Reparado','Resuelta',inc,'Solucionado')
        self.assertIsNotNone(self.s.one('incidencias',inc)['resuelto'])
    def test_csv_formula_neutralized(self):
        out=Path(self.temp.name)/'x.csv';self.s.csv_write(out,[{'nombre':'=HYPERLINK("bad")'}])
        self.assertIn("'=HYPERLINK",out.read_text(encoding='utf-8-sig'))
    def test_empty_dashboard_has_no_fake_percentage(self):
        self.assertIsNone(self.s.dashboard([])['Avance de cierre (%)'])
    def test_backup_can_be_opened(self):
        from unittest.mock import patch
        self.count()
        with patch('app.core.ROOT',Path(self.temp.name)):
            backup=self.s.backup()
        import sqlite3
        restored=sqlite3.connect(str(backup))
        self.assertEqual(restored.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertEqual(restored.execute('SELECT fisicos FROM trabajos').fetchone()[0],15)
        restored.close()

    def test_filtered_dates(self):
        self.s.save_work(self.f,A,'Ejemplo',1,recibido='2026-09-18',ident=self.t)
        self.assertEqual(len(self.s.works(desde='2026-09-19')),0)
        self.assertEqual(len(self.s.works(desde='2026-09-18',hasta='2026-09-18')),1)
    def test_task_history(self):
        ident=self.s.save_task('Prueba',work=self.t)
        self.s.save_task('Prueba','Hecha',self.t,ident=ident)
        self.assertEqual(self.s.one('tareas',ident)['estado'],'Hecha')

@unittest.skipUnless(os.environ.get('DIGITALIZACION_PROBAR_FUENTES_PRIVADAS')=='1' and (ROOT/'CONTROL_EXPEDIENTES.xlsx').exists() and (ROOT/'fuentes'/'registro_digitalizacion_detallado.csv').exists(), 'Integración privada desactivada o fuentes ausentes; se usan fixtures sintéticos')
class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.s=Store(Path(self.temp.name)/'sources.sqlite3','Importador')
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def load(self):return import_excel(self.s,ROOT/'CONTROL_EXPEDIENTES.xlsx')
    def csv(self):return import_csv(self.s,ROOT/'fuentes'/'registro_digitalizacion_detallado.csv')
    def test_actual_workbook_and_reconciliation(self):
        report=self.load();self.assertEqual(report,{'trabajos':55,'catalogos':71,'bloques':97,'incidencias':12,'tareas':7})
        self.assertEqual(len(self.s.rows("SELECT * FROM pendientes WHERE tipo='Diferencia de conteo'")),0)
        self.assertEqual(self.s.dashboard(self.s.works())['Hojas físicas confirmadas'],2027)
        self.assertEqual(self.s.rows('SELECT fecha_recepcion FROM folios')[0]['fecha_recepcion'],None)
    def test_excel_cannot_overwrite_live_operations(self):
        self.load()
        with self.assertRaises(ValueError):self.load()
        self.assertEqual(len(self.s.works()),55)
    def test_actual_csv_and_idempotency(self):
        report=self.csv();self.assertEqual(report['ejecuciones'],11);self.assertEqual(report['rechazadas'],0)
        self.csv();self.assertEqual(len(self.s.rows('SELECT * FROM ejecuciones')),11)
        self.assertTrue(all(e['trabajo_id'] is None for e in self.s.rows('SELECT * FROM ejecuciones')))
    def test_normal_semicolon_csv_same_records_deduplicated(self):
        self.csv();headers,rows,_=parse_csv(ROOT/'fuentes'/'registro_digitalizacion_detallado.csv')
        path=Path(self.temp.name)/'normal.csv'
        with path.open('w',newline='',encoding='cp1252') as f:
            w=csv.writer(f,delimiter=';');w.writerow(headers);w.writerows(rows)
        report=import_csv(self.s,path);self.assertEqual(report['duplicadas'],11)
    def test_latest_snapshot_not_sum(self):
        self.load();self.csv();e=self.s.rows('SELECT * FROM ejecuciones LIMIT 1')[0]
        t=self.s.rows('SELECT id FROM trabajos WHERE curp=?',(e['curp'],))[0]['id']
        self.s.bind_execution(e['id'],t,'Legajo','Ruta verificada y alcance de un legajo confirmado')
        p=json.loads(e['payload']);p['TOTAL_DIGITALES_TIFF']=500
        with self.s.db:
            self.s.db.execute('INSERT INTO ejecuciones(huella,curp,fecha,payload,trabajo_id,ambito) VALUES(?,?,?,?,?,?)',('synthetic',e['curp'],'2099-01-01T10:00:00',json.dumps(p),t,'Legajo'))
        self.assertEqual(self.s.dashboard(self.s.works())['TIFF declarados en reportes legados'],500)
        self.assertEqual(self.s.dashboard(self.s.works())['Archivos TIFF'],0)
        self.s.bind_execution(e['id'],t,'CURP completa','Agrupado')
        self.assertEqual(self.s.dashboard(self.s.works())['TIFF declarados en reportes legados'],500)
    def test_different_curp_cannot_bind(self):
        self.load();self.csv();e=self.s.rows('SELECT * FROM ejecuciones LIMIT 1')[0]
        t=self.s.rows('SELECT id FROM trabajos WHERE curp<>? LIMIT 1',(e['curp'],))[0]['id']
        with self.assertRaises(ValueError):self.s.bind_execution(e['id'],t,'Legajo','Prueba')
    def test_legacy_report_does_not_replace_delivery_approval(self):
        self.load();self.csv();e=self.s.rows('SELECT * FROM ejecuciones LIMIT 1')[0]
        work=self.s.rows('SELECT * FROM trabajos WHERE curp=?',(e['curp'],))[0]
        t=work['id']
        self.s.bind_execution(e['id'],t,'Legajo','Verificado físicamente')
        with self.s.db:
            self.s.db.execute('UPDATE trabajos SET carpetas=1 WHERE id=?',(t,))
        incident=self.s.save_incident(t,None,'DP-01','Incidencia de prueba')
        for state in STATES[1:-1]:self.s.change_state(t,state,'Confirmación durante prueba')
        with self.assertRaises(ValueError):self.s.change_state(t,STATES[-1],'Intento con incidencia abierta')
        for i in self.s.rows("SELECT * FROM incidencias WHERE trabajo_id=? AND estado='Abierta'",(t,)):
            self.s.save_incident(t,i['catalogo_id'],i['documento'],i['problema'],'Solucionado','Resuelta',i['id'],'Resolución de prueba')
        with self.assertRaises(ValueError):self.s.change_state(t,STATES[-1],'Reporte legado sin entrega aprobada')
        self.assertNotEqual(self.s.one('trabajos',t)['estado'],STATES[-1])

    def test_bad_csv_row_retained_for_review(self):
        headers,rows,_=parse_csv(ROOT/'fuentes'/'registro_digitalizacion_detallado.csv');rows[0][headers.index('TOTAL_DIGITALES_TIFF')]='9999'
        path=Path(self.temp.name)/'bad.csv'
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f,delimiter=';');w.writerow(headers);w.writerow(rows[0])
        result=import_csv(self.s,path);self.assertEqual(result['rechazadas'],1)
        self.assertEqual(len(self.s.rows('SELECT * FROM origen')),1)
        self.assertEqual(len(self.s.rows('SELECT * FROM ejecuciones')),0)

if __name__=='__main__':unittest.main()
