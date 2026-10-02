import json
import unittest
from unittest.mock import patch
from app.integrations import Integrations
from app.batch_tiff import BatchTiff
from app.delivery import Deliveries
from app.review import Reviews
from app.operations import Operations
from app.reporting import Reporting
import test_coding as fixture


class IntegrationTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    load=fixture.CodingTests.load

    def add(self,n):
        ident=self.load(self.make(str(n)+'.tif',n));self.c.assign(ident,'DP-01');return ident

    def close(self):
        item=Integrations(self.s).current(self.w)['prestamo_item_id']
        Operations(self.s).validate_item(item,'Aceptado','AAAA900101HYNBBB01',1,'Cotejo ficticio')
        d=Deliveries(self.s).prepare(self.w);r=Reviews(self.s);r.begin(d);r.approve(d,'Aprobación sintética')
        return d

    def start(self,**kw):return Integrations(self.s).start(self.w,'Documentos adicionales ficticios','2026-10-01',reference='Acuse sintético',confirmed=True,**kw)

    def test_two_integrations_complete_totals_immutable_delivery(self):
        initial=self.add(1);v0=self.close();d=Deliveries(self.s);before=d.verify(v0)
        block=self.s.rows('SELECT id FROM conteos')[0]['id']
        for number in (1,2):
            ident=self.start();self.assertIsNone(self.s.count_total(self.w));self.assertIsNone(self.s.one('trabajos',self.w)['fisicos'])
            with self.assertRaises(ValueError):self.s.edit_count(block,100,'No debe alterar historia')
            with self.assertRaises(ValueError):self.c.organize(self.w)
            self.s.add_count(self.w,number+1);self.s.confirm_count(self.w);added=self.add(number+1)
            self.assertEqual(self.c.file(added)['integracion_id'],ident)
            receipt=Integrations(self.s).current(self.w)['prestamo_item_id']
            self.assertEqual(Operations(self.s).create_cycle(receipt),self.w)
            delivered=self.close();manifest=d.verify(delivered)
            self.assertEqual(len(manifest['items']),number+1)
            self.assertEqual(len(manifest['integraciones']),number+1)
            self.assertEqual(d.verify(v0),before)
        totals=Integrations(self.s).totals(self.w)
        self.assertEqual((totals['hojas_totales'],totals['tiff'],totals['paginas']),(15,3,6))
        self.assertEqual(self.c.file(initial)['integracion_id'],Integrations(self.s).list(self.w)[0]['id'])
        self.assertEqual(self.s.db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertEqual(self.s.rows('PRAGMA foreign_key_check'),[])

    def test_start_rejects_unapproved_and_rolls_back(self):
        with self.assertRaises(ValueError):self.start()
        self.add(1);self.close();before=self.s.rows('SELECT * FROM integraciones')
        def fail():raise OSError('Interrupción sintética')
        with self.assertRaises(OSError):self.start(checkpoint=fail)
        self.assertEqual(before,self.s.rows('SELECT * FROM integraciones'))
        self.assertEqual(self.s.one('trabajos',self.w)['estado'],'Expediente cerrado')

    def test_start_rejects_external_change(self):
        ident=self.add(1);self.close();self.c.path(self.c.file(ident)['ruta']).write_bytes(b'corrupto ficticio')
        with self.assertRaises(ValueError):self.start()

    def test_count_edits_invalidate_confirmation(self):
        self.s.add_count(self.w,2)
        self.assertIsNone(self.s.one('trabajos',self.w)['fisicos'])
        self.assertIsNone(Integrations(self.s).current(self.w)['fisicos'])

    def test_batch_preflight_partial_and_restore(self):
        ids=[self.add(n) for n in (1,2,3)];batch=BatchTiff(self.c)
        with self.assertRaises(ValueError):batch.run(self.w,ids,'retirar','')
        def fail(i):
            if i==ids[1]:raise OSError('Corte ficticio')
        report=batch.run(self.w,ids,'retirar','Duplicados ficticios',fail)
        self.assertEqual(report['completados'],ids[:1]);self.assertEqual(report['pendientes'],ids[1:])
        self.assertEqual(batch.run(self.w,ids[1:],'retirar','Continuación')['estado'],'Completado')
        self.assertEqual(batch.run(self.w,ids,'recuperar','Restitución')['completados'],ids)
        self.assertEqual(len(self.c.files(self.w)),3)

    def test_live_cards_use_metadata_and_accent_search(self):
        self.s.save_work(self.f,'AAAA900101HYNBBB01','Ejemplo ÁRBOL',1,ident=self.w)
        with patch('app.delivery.Deliveries.basis',side_effect=AssertionError('No leer TIFF al filtrar')):
            cards=Reporting(self.s).cards(texto='arbol')
        self.assertEqual(len(cards),1);self.assertEqual(cards[0]['nombre'],'Ejemplo ÁRBOL')

    def test_replacement_preserves_document_integration_and_ingress(self):
        old=self.add(1);initial=self.c.file(old)['integracion_id'];self.close();new_group=self.start()
        correction=self.c.mark_correction(old,1,'Hoja ficticia','Reescaneo ficticio')
        path=self.make('reemplazo.tif',1)
        with fixture.Image.open(path) as image:copy=image.copy()
        copy.putpixel((0,0),0);copy.save(path,compression='tiff_deflate');copy.close()
        replacement=self.load(path)
        self.c.replace_correction(correction,replacement,'Cotejo completo de prueba')
        row=self.c.file(replacement)
        self.assertEqual(row['integracion_id'],initial);self.assertEqual(row['integracion_ingreso_id'],new_group)
        self.assertEqual(row['documento_id'],self.c.file(old)['documento_id'])

    def test_other_folio_receipt_is_current_and_idempotent(self):
        self.add(1);self.close();other=self.s.save_folio('NUEVO-FOLIO-FICTICIO','2026-10-01')
        self.start(folio=other);current=Integrations(self.s).current(self.w)
        from app.reception import Reception
        from app.dashboard import Dashboard
        row=Reception(self.s).preview(other,[current['prestamo_item_id']])[0]
        self.assertEqual(row['errores'],[])
        result=Reception(self.s).accept(other,[current['prestamo_item_id']],'Cotejo repetido',True)
        self.assertEqual(result['ciclos'],[self.w]);self.assertEqual(len(self.s.works(folio='NUEVO-FOLIO-FICTICIO')),1)
        Operations(self.s).assign('Persona ficticia reasignada','Prueba',folio=other)
        self.assertEqual(Integrations(self.s).current(self.w)['digitalizador'],'Persona ficticia reasignada')
        self.assertEqual(Dashboard(self.s).snapshot(self.s.works())['sin_ciclo_global'],0)

    def test_changed_name_requires_new_delivery_before_approval(self):
        self.add(1);self.close();self.s.change_state(self.w,'Listo para aprobación','Corrección de nombre ficticio')
        delivery=Deliveries(self.s).prepare(self.w);reviews=Reviews(self.s);reviews.begin(delivery)
        self.s.save_work(self.f,'AAAA900101HYNBBB01','Nombre ficticio corregido',1,ident=self.w)
        with self.assertRaisesRegex(ValueError,'nombre, conteo'):reviews.approve(delivery,'No debe aprobar metadatos obsoletos')

    def test_previous_delivery_cannot_reopen_current_integration(self):
        self.add(1);delivery=self.close();self.start();reviews=Reviews(self.s)
        with self.assertRaisesRegex(ValueError,'integración anterior'):reviews.begin(delivery)
        with self.assertRaisesRegex(ValueError,'integración anterior'):reviews.approve(delivery,'No debe aprobar la integración nueva')
        self.assertEqual(self.s.one('trabajos',self.w)['estado'],'Recibido')
        self.assertEqual(Deliveries(self.s).get(delivery)['estado'],'Aprobada')
        self.assertIsNone(Integrations(self.s).current(self.w)['fisicos'])
