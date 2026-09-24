import json
import unittest
from unittest.mock import patch
from app.delivery import Deliveries,content_hash
from app.review import Reviews
from app.operations import Operations
from app.backup import sha256
import test_coding as fixture


class DeliveryTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    load=fixture.CodingTests.load
    def add(self,name,count=1):
        ident=self.load(self.make(name,count));self.c.assign(ident,'DP-01');return ident
    def latest_delivery(self):return self.s.rows('SELECT * FROM entregas ORDER BY numero DESC LIMIT 1')[0]
    def test_clean_v2_excludes_removed_and_keeps_v1_intact(self):
        ids=[self.add(name,n) for n,name in enumerate(('A.tif','B.tif','C.tif'),1)]
        d=Deliveries(self.s);v1=d.prepare(self.w);first=d.verify(v1)
        root1=self.s.workspace.path(d.get(v1)['ruta']);before={p.name:sha256(p) for p in root1.rglob('*') if p.is_file()}
        self.c.exclude(ids[1],'No corresponde');new=self.add('D.tif',4);v2=d.prepare(self.w)
        second=d.verify(v2);doc_b=self.c.file(ids[1])['documento_id'];doc_d=self.c.file(new)['documento_id']
        self.assertNotIn(doc_b,{i['document_asset_id'] for i in second['items']})
        self.assertIn(doc_b,{i['document_asset_id'] for i in first['items']})
        diff=d.diff(v1,v2);self.assertEqual(diff['retirados'],[doc_b]);self.assertEqual(diff['agregados'],[doc_d])
        self.assertEqual(len(diff['sin_cambios']),2)
        self.assertEqual(before,{p.name:sha256(p) for p in root1.rglob('*') if p.is_file()})
        self.assertEqual(len(list(self.s.workspace.path(d.get(v2)['ruta']).rglob('*.tif'))),3)
    def test_rename_not_added_and_removed(self):
        ident=self.add('A.tif');d=Deliveries(self.s);v1=d.prepare(self.w)
        self.c.rename(ident,'DP-01 nombre corregido.tif');v2=d.prepare(self.w);diff=d.diff(v1,v2)
        self.assertEqual(diff['agregados'],[]);self.assertEqual(diff['retirados'],[])
        self.assertEqual(diff['renombrados'],[self.c.file(ident)['documento_id']])
    def test_external_edit_makes_validation_obsolete_and_preserves_export(self):
        ident=self.add('A.tif');d=Deliveries(self.s);delivery=d.prepare(self.w)
        self.assertIsNotNone(d.current_validation(self.w))
        self.c.path(self.c.file(ident)['ruta']).write_bytes(b'external corruption')
        self.assertIsNone(d.current_validation(self.w));self.assertEqual(d.inventory(self.w)['resultado'],'BLOQUEANTE')
        d.verify(delivery)
    def test_manifest_corruption_and_extra_output_rejected(self):
        self.add('A.tif');d=Deliveries(self.s);delivery=d.prepare(self.w);root=self.s.workspace.path(d.get(delivery)['ruta'])
        extra=root/'PERSONALES/archivo viejo.tif';extra.write_bytes(b'residuo')
        with self.assertRaises(ValueError):d.verify(delivery)
        extra.unlink();p=root/'manifest.json';old=p.read_text();obj=json.loads(old);obj['numero']=999;p.write_text(json.dumps(obj))
        with self.assertRaises(ValueError):d.verify(delivery)
    def test_copy_failure_never_publishes_or_merges_retry(self):
        self.add('A.tif');d=Deliveries(self.s)
        with patch('app.coding.CodingService.copy_new',side_effect=OSError('Disco lleno simulado')):
            with self.assertRaises(OSError):d.prepare(self.w)
        first=self.latest_delivery();self.assertEqual(first['estado'],'Incompleta')
        second=d.prepare(self.w);self.assertEqual(d.get(second)['numero'],2)
        self.assertNotEqual(first['ruta'],d.get(second)['ruta']);self.assertTrue((self.s.workspace.path(first['ruta'])/'INCOMPLETA.txt').exists())
    def test_catalogue_folder_controls_diff(self):
        self.add('A.tif');d=Deliveries(self.s);first=d.prepare(self.w)
        self.s.save_catalog('documento','DP-01','FEDERAL','Acta',ident=self.dp,motivo='Cambio de catálogo')
        second=d.prepare(self.w);self.assertEqual(len(d.diff(first,second)['movidos']),1)
        self.assertEqual(d.verify(second)['items'][0]['carpeta'],'FEDERAL')
    def test_manifest_hash_deterministic_and_inventory_hash_separate(self):
        self.add('A.tif');d=Deliveries(self.s);one=d.prepare(self.w);two=d.prepare(self.w)
        self.assertNotEqual(d.get(one)['manifest_hash'],d.get(two)['manifest_hash'])
        self.assertEqual(d.get(one)['inventario_hash'],d.get(two)['inventario_hash'])
        self.assertEqual(content_hash(d.verify(one)),d.get(one)['manifest_hash'])
    def test_organize_creates_snapshot_and_links_metrics(self):
        self.add('A.tif');self.c.organize(self.w)
        self.assertTrue(self.s.latest(self.w));self.assertEqual(self.latest_delivery()['trabajo_id'],self.w)
    def test_duplicate_content_is_warning_and_not_deleted(self):
        p=self.make('A.tif');self.c.import_files(self.w,[p,p],allow_duplicates=True)
        for row in self.c.files(self.w):self.c.assign(row['id'],'DP-01')
        d=Deliveries(self.s);report=d.inventory(self.w)
        self.assertEqual(report['resultado'],'OK con advertencias');self.assertEqual(report['totales']['archivos'],2)
        self.assertEqual(len(d.verify(d.prepare(self.w))['items']),2)
    def test_export_is_new_independent_and_verifiable_without_database(self):
        from app.delivery import verify_folder
        ident=self.add('A.tif');d=Deliveries(self.s);delivery=d.prepare(self.w)
        out=d.export_copy(delivery,self.root/'export independiente')
        self.assertEqual(verify_folder(out,d.get(delivery)['manifest_hash'])['entrega_id'],delivery)
        with self.assertRaises(FileExistsError):d.export_copy(delivery,out)
        with self.assertRaises(ValueError):verify_folder(out,'0'*64)
        self.c.exclude(ident,'Retirado después de exportar')
        verify_folder(out,d.get(delivery)['manifest_hash'])


class ReviewTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    load=fixture.CodingTests.load
    add=DeliveryTests.add
    def receipt(self):
        item=self.s.one('trabajos',self.w)['prestamo_item_id']
        Operations(self.s).validate_item(item,'Aceptado','AAAA900101HYNBBB01',1,'Recepción ficticia comprobada')
        return item
    def case(self):
        ident=self.add('A.tif',2);d=Deliveries(self.s);delivery=d.prepare(self.w);r=Reviews(self.s);session=r.begin(delivery)
        row=self.c.file(ident)
        observation=r.observe(session,'Calidad de imagen','Página inclinada','Digitalizador ficticio',row['documento_id'],row['version_id'],2,'Hoja física 7')
        return ident,d,delivery,r,observation
    def test_observation_page_scope_and_history(self):
        ident,d,delivery,r,obs=self.case();row=self.s.rows('SELECT * FROM observaciones_revision WHERE id=?',(obs,))[0]
        self.assertEqual(row['pagina'],2);self.assertEqual(row['entrega_detectada'],delivery)
        with self.assertRaises(ValueError):r.observe(row['sesion_id'],'Conteo','Error','Persona',row['documento_id'],page=3)
        self.assertEqual(self.s.one('trabajos',self.w)['calidad'],'Con observaciones')
    def test_edit_does_not_resolve_observation(self):
        ident,d,v1,r,obs=self.case();self.c.save_edit(ident,1,[('rotate',90)]);v2=d.prepare(self.w)
        self.assertEqual(self.s.rows('SELECT estado FROM observaciones_revision WHERE id=?',(obs,))[0]['estado'],'Abierta')
        self.assertEqual(len(d.diff(v1,v2)['reemplazados']),1)
        with self.assertRaises(ValueError):r.approve(v2,'No debe aprobar observaciones abiertas')
    def test_explicit_response_validation_and_approval_leave_loan_open(self):
        item=self.receipt();ident,d,v1,r,obs=self.case()
        r.update_observation(obs,'En corrección','Atendiendo la página')
        self.c.save_edit(ident,1,[('rotate',90)]);v2=d.prepare(self.w)
        r.update_observation(obs,'Resuelta','Página corregida y cotejada',v2)
        self.assertEqual(self.s.one('trabajos',self.w)['estado'],'Revisión en curso')
        r.begin(v2)
        with self.assertRaises(ValueError):r.approve(v2,'Falta validar la observación')
        r.update_observation(obs,'Validada','Responsable cotejó la nueva entrega')
        r.approve(v2,'Revisión completa de la entrega exacta')
        self.assertEqual(self.s.one('trabajos',self.w)['estado'],'Expediente cerrado')
        self.assertEqual(self.s.one('trabajos',self.w)['calidad'],'Aprobado')
        self.assertEqual(self.s.rows('SELECT custodia FROM prestamo_items WHERE id=?',(item,))[0]['custodia'],'Prestado a Digitalización')
        self.assertEqual(len(self.s.rows('SELECT * FROM observacion_historial WHERE observacion_id=?',(obs,))),4)
    def test_no_approval_after_unexported_changes(self):
        self.receipt();ident=self.add('A.tif');d=Deliveries(self.s);delivery=d.prepare(self.w);r=Reviews(self.s);r.begin(delivery)
        self.c.save_edit(ident,0,[('rotate',90)])
        with self.assertRaises(ValueError):r.approve(delivery,'Debe generar nueva entrega')
        self.assertNotEqual(self.s.one('trabajos',self.w)['calidad'],'Aprobado')
    def test_digitalizer_cannot_approve_or_validate_observation(self):
        ident,d,v1,r,obs=self.case()
        with self.assertRaises(ValueError):Reviews(self.s,'Digitalizador').approve(v1,'No autorizado por rol')
        with self.assertRaises(ValueError):Reviews(self.s,'Digitalizador').update_observation(obs,'Anulada','No autorizado por rol')
