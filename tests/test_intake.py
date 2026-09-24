"""Listas y directorio con identidades exclusivamente ficticias."""
import csv
import hashlib
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from xml.sax.saxutils import escape
from app.core import Store
from app.directory import Directory
from app.intake import LoanLists,read_tables,infer_mapping,confirm_legajo,register_legajos
from app.operations import Operations
from app.coding import CodingService
from PIL import Image

PEOPLE=['AAAA900101HYNBBB01','AAAB900101HYNBBB02','AAAC900101HYNBBB03']
HEADERS=['CURP O RFC','No.','APELLIDO PATERNO, MATERNO, NOMBRE','CURP O RFC2','Integra','folio','sistema','fecha solicitud','TRABAJADOS']


def write_list(path,rows=None,headers=None,encoding='utf-8-sig',delimiter=','):
    headers=headers or HEADERS
    if rows is None:rows=[[p,str(i),'Persona ficticia '+str(i),p,'Responsable de prueba','833/2026','FEDERAL','18/8/2026','NO TRABAJADO<br><br>'] for i,p in enumerate(PEOPLE,1)]
    with Path(path).open('w',encoding=encoding,newline='') as f:
        writer=csv.writer(f,delimiter=delimiter);writer.writerow(headers);writer.writerows(rows)
    return Path(path)


def xlsx(path,rows):
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(str(path),'w') as z:
        z.writestr('xl/workbook.xml','<workbook xmlns="'+ns+'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Entrega" sheetId="1" r:id="r1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
        xml='<worksheet xmlns="'+ns+'"><sheetData>'
        for n,values in enumerate(rows,1):
            xml+='<row r="'+str(n)+'">'
            for i,value in enumerate(values):
                ref=chr(65+i)+str(n)
                xml+=('<c r="'+ref+'"><v>'+str(value)+'</v></c>') if isinstance(value,(int,float)) else ('<c r="'+ref+'" t="inlineStr"><is><t>'+escape(str(value))+'</t></is></c>')
            xml+='</row>'
        z.writestr('xl/worksheets/sheet1.xml',xml+'</sheetData></worksheet>')


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.s=Store(workspace=self.root/'trabajo');self.service=LoanLists(self.s)
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def source(self):return write_list(self.root/'lista.csv')
    def test_given_header_imports_folio_curps_without_inventing_legajo_or_receipt(self):
        path=self.source();before=hashlib.sha256(path.read_bytes()).hexdigest()
        plan=self.service.preview(path);self.assertEqual((plan['validas'],plan['sin_legajo']),(3,3))
        self.assertFalse(self.s.rows('SELECT * FROM folios'))
        result=self.service.commit(plan);self.assertEqual(result['elementos_nuevos'],3);self.assertEqual(result['ciclos_nuevos'],0)
        self.assertEqual(len(self.s.rows('SELECT * FROM personas')),3)
        folio=self.s.rows('SELECT * FROM folios')[0];self.assertEqual(folio['numero'],'833/2026');self.assertIsNone(folio['fecha_recepcion']);self.assertIsNone(folio['recepcion_at'])
        for row in self.s.rows('SELECT * FROM prestamo_items'):
            self.assertIsNone(row['legajo_esperado']);self.assertIsNone(row['expediente_id']);self.assertEqual(row['fecha_solicitud'],'2026-08-18')
            self.assertEqual(row['trabajado_declarado'],'NO TRABAJADO');self.assertEqual(row['validacion'],'Pendiente')
        self.assertFalse(self.s.rows('SELECT * FROM asignaciones'))
        self.assertIn('<br>',self.s.rows('SELECT contenido FROM origen')[0]['contenido'])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
    def test_reordered_aliases_cp1252_and_explicit_legajo(self):
        path=write_list(self.root/'lista.csv',[[PEOPLE[0],'JOSÉ, PERSONA FICTICIA','834/2026','TRABAJADO','18/8/2026']],['curp','Nombre completo','Número de folio','Trabajado','Fecha de solicitud'],encoding='cp1252',delimiter=';')
        result=self.service.commit(self.service.preview(path,default_legajo=1,area='Área de prueba'))
        self.assertEqual(result['ciclos_nuevos'],1);w=self.s.works()[0]
        self.assertEqual(w['legajo'],1);self.assertEqual(w['estado'],'Recibido');self.assertEqual(w['total_tiff'],0);self.assertIsNone(w['recibido'])
        self.assertEqual(w['nombre'],'JOSÉ, PERSONA FICTICIA');self.assertEqual(w['recepcion'],'Pendiente')
        self.assertTrue(self.s.rows('SELECT * FROM directorio WHERE tipo="area"'))
    def test_xlsx_offset_header_numeric_dates_and_real_legajo(self):
        path=self.root/'lista.xlsx';xlsx(path,[['Listado de prueba'],[],['Folio','CURP','Legajo','Fecha solicitud','Nombre'],['9/2026',PEOPLE[0],2,46252,'Persona ficticia']])
        plan=self.service.preview(path);self.assertEqual(plan['config']['header_row'],3)
        self.service.commit(plan);self.assertEqual(self.s.works()[0]['legajo'],2)
        self.assertEqual(self.s.rows('SELECT fecha_solicitud FROM prestamo_items')[0]['fecha_solicitud'],'2026-08-18')
    def test_utf16_tab_csv(self):
        path=write_list(self.root/'unicode.csv',encoding='utf-16',delimiter='\t')
        self.assertEqual(self.service.preview(path)['validas'],3)
    def test_reimport_is_idempotent_and_does_not_overwrite_operational_state(self):
        path=self.source();plan=self.service.preview(path,default_legajo=1);result=self.service.commit(plan)
        ops=Operations(self.s);item=self.s.rows('SELECT * FROM prestamo_items ORDER BY id')[0]
        ops.validate_item(item['id'],'Aceptado',PEOPLE[0],1,'Comprobado');ops.assign('Digitalizador A','Asignación',work=self.s.works()[0]['id'])
        again=self.service.commit(plan);self.assertTrue(again['ya_importado']);self.assertEqual(result['lista_id'],again['lista_id'])
        other=self.root/'otra.csv';other.write_bytes(path.read_bytes()+b'\n');self.service.commit(self.service.preview(other,default_legajo=1))
        self.assertEqual(len(self.s.rows('SELECT * FROM trabajos')),3);self.assertEqual(len(self.s.rows('SELECT * FROM prestamo_items')),3)
        self.assertEqual(self.s.rows('SELECT validacion FROM prestamo_items WHERE id=?',(item['id'],))[0]['validacion'],'Aceptado')
        self.assertEqual(self.s.works()[0]['digitalizador'],'Digitalizador A')
    def test_same_curp_in_new_folio_reuses_master_but_new_cycle(self):
        one=write_list(self.root/'uno.csv',[[PEOPLE[0],'1/2026',1]],['CURP','Folio','Legajo'])
        two=write_list(self.root/'dos.csv',[[PEOPLE[0],'2/2026',1]],['CURP','Folio','Legajo'])
        for path in (one,two):self.service.commit(self.service.preview(path))
        self.assertEqual(len(self.s.rows('SELECT * FROM expedientes')),1);self.assertEqual(len(self.s.rows('SELECT * FROM trabajos')),2)
    def test_register_multiple_legajos_shares_curp_and_preserves_each_inventory(self):
        self.service.commit(self.service.preview(self.source()));item=self.s.rows('SELECT * FROM prestamo_items ORDER BY id')[0]
        works=register_legajos(self.s,item['id'],'1,2,3','Tres físicos comprobados')
        self.assertEqual(len(works),3);self.assertEqual(len(self.s.rows('SELECT * FROM expedientes WHERE curp=?',(PEOPLE[0],))),3)
        self.assertEqual(self.s.one('trabajos',works[0])['prestamo_item_id'],item['id'])
        self.assertEqual(len(self.s.rows('SELECT * FROM trabajos')),3)
        register_legajos(self.s,item['id'],'2,3,4','Cuarto físico recibido');self.assertEqual(len(self.s.rows('SELECT * FROM trabajos')),4)
        im=Image.new('L',(20,30),'white');p=self.root/'prueba.tif';im.save(p);im.close()
        CodingService(self.s).import_files(works[1],[p]);rows=self.s.works()
        self.assertEqual([(r['legajo'],r['total_tiff'],r['total_paginas']) for r in rows],[(1,0,0),(2,1,1),(3,0,0),(4,0,0)])
        self.assertTrue(all(r['recepcion']=='Pendiente' for r in rows))
        from app.reporting import Reporting
        for row in rows:
            source=Reporting(self.s).summary(row['id'])['Lista de origen']
            self.assertEqual(len(source),1);self.assertEqual(source[0]['fila'],2)
    def test_confirmation_of_one_legajo_keeps_source_and_no_false_acceptance(self):
        result=self.service.commit(self.service.preview(self.source()));item=self.s.rows('SELECT id FROM prestamo_items')[0]['id']
        work=confirm_legajo(self.s,item,2,'Físico comprobado');self.assertEqual(self.s.one('trabajos',work)['legajo'],2)
        self.assertTrue(self.s.rows('SELECT * FROM lista_registros WHERE lista_id=? AND prestamo_item_id=?',(result['lista_id'],item)))
        with self.assertRaises(ValueError):Operations(self.s).assign('Persona A','Aún no recibido',work=work)
    def test_bad_curp_mismatch_rfc_invalid_date_preserved_for_review(self):
        rows=[[PEOPLE[0],PEOPLE[1],'1/2026','18/8/2026'],['RFC900101XX1','RFC900101XX1','1/2026','18/8/2026'],[PEOPLE[2],PEOPLE[2],'1/2026','31/02/2026']]
        p=write_list(self.root/'bad.csv',rows,['CURP','CURP O RFC2','Folio','Fecha solicitud'])
        report=self.service.commit(self.service.preview(p));self.assertEqual(report['por_revisar'],3)
        self.assertEqual(len(self.s.rows('SELECT * FROM origen')),3);self.assertEqual(len(self.s.rows('SELECT * FROM pendientes')),3)
        self.assertFalse(self.s.rows('SELECT * FROM expedientes'));self.assertFalse(self.s.rows('SELECT * FROM prestamo_items'))
    def test_manual_mapping_and_default_folio(self):
        p=write_list(self.root/'manual.csv',[[PEOPLE[0],'Ficticia']],['Clave especial','Beneficiario'])
        with self.assertRaises(ValueError):self.service.preview(p)
        plan=self.service.preview(p,mapping={'curp':0,'nombre':1},default_folio='100/2026');self.service.commit(plan)
        self.assertEqual(self.s.rows('SELECT numero FROM folios')[0]['numero'],'100/2026')
    def test_changed_source_rejected_before_any_write(self):
        path=self.source();plan=self.service.preview(path);path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'cambió'):self.service.commit(plan)
        self.assertFalse(self.s.rows('SELECT * FROM fuentes'));self.assertFalse(self.s.rows('SELECT * FROM folios'))
    def test_failure_rolls_back_entire_batch_including_directory(self):
        plan=self.service.preview(self.source(),default_legajo=1,area='Área nueva');original=self.s.audit
        def fail(entity,*args):
            if entity=='listas_importadas':raise OSError('Fallo de escritura simulado')
            return original(entity,*args)
        with patch.object(self.s,'audit',side_effect=fail):
            with self.assertRaises(OSError):self.service.commit(plan)
        for table in ('folios','personas','trabajos','directorio','fuentes','origen','prestamo_items','listas_importadas'):
            self.assertFalse(self.s.rows('SELECT * FROM '+table),table)
    def test_bulk_legajo_failure_is_atomic(self):
        self.service.commit(self.service.preview(self.source()));item=self.s.rows('SELECT id FROM prestamo_items')[0]['id']
        with self.assertRaises(ValueError):register_legajos(self.s,item,'1,0,3','Prueba inválida')
        self.assertFalse(self.s.rows('SELECT * FROM trabajos'));self.assertIsNone(self.s.rows('SELECT legajo_esperado FROM prestamo_items WHERE id=?',(item,))[0]['legajo_esperado'])
    def test_partial_search_and_metrics_do_not_read_tiff_content(self):
        self.service.commit(self.service.preview(self.source(),default_legajo=1))
        with self.s.db:self.s.db.execute("UPDATE trabajos SET digitalizador='José de prueba'")
        with patch('app.backup.sha256',side_effect=AssertionError('No leer TIFF para buscar')):
            rows=self.s.works(texto='ficticia',folio='833',digitalizador='jose',partial=True)
        self.assertEqual(len(rows),3);self.assertEqual(self.s.works(folio='833'),[])
    def test_no_column_does_not_map_to_legajo(self):
        mapping=infer_mapping(HEADERS);self.assertEqual(mapping['numero'],1);self.assertNotIn('legajo',mapping)


class DirectoryTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.s=Store(workspace=Path(self.temp.name));self.d=Directory(self.s)
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def test_crud_preserves_ids_aliases_and_historical_names(self):
        ident=self.d.save('persona','José de Prueba');folio=self.s.save_folio('1/2026','',responsable='JOSÉ DE PRUEBA')
        self.assertEqual(self.s.one('folios',folio)['responsable_id'],ident)
        self.d.save('persona','José Pérez de Prueba',ident=ident,reason='Nombre actualizado')
        self.assertEqual(self.s.one('folios',folio)['responsable'],'JOSÉ DE PRUEBA')
        with self.s.db:self.assertEqual(self.d.ensure('persona','jose de prueba'),ident)
        with self.assertRaises(ValueError):self.d.save('persona','José de Prueba')
        self.d.toggle(ident,'Baja');self.assertFalse(self.d.entries('persona'));self.assertEqual(len(self.d.entries('persona',inactive=True)),1)
        with self.assertRaises(ValueError):self.s.save_folio('2/2026','',responsable='José Pérez de Prueba')
        self.assertEqual(len(self.s.rows('SELECT * FROM folios')),1)
        self.d.toggle(ident,'Reactivación');self.assertEqual(self.d.get(ident)['id'],ident)
    def test_names_learned_from_receipt_assignment_return_and_observation(self):
        ops=Operations(self.s);folio=self.s.save_folio('1/2026','');ops.receive_folio(folio,'Área Ficticia','Entrega Ficticia','Recibe Ficticia')
        item=ops.expect(folio,PEOPLE[0],1,'Estante de prueba');ops.validate_item(item,'Aceptado',PEOPLE[0],1,'Cotejado');work=ops.create_cycle(item)
        ops.assign('Digitalizador Ficticio','Inicio',work=work);ops.custody(item,'En devolución','Se devuelve');ops.custody(item,'Devuelto','Acuse','Archivo Ficticio')
        self.assertEqual(len(self.d.entries('area')),1);self.assertEqual(len(self.d.entries('ubicacion')),1)
        self.assertEqual(len(self.d.entries('persona')),4)
        self.assertIsNotNone(self.s.rows('SELECT persona_id FROM asignaciones')[0]['persona_id'])
        self.assertIsNotNone(self.s.rows('SELECT devolucion_recibe_id FROM prestamo_items')[0]['devolucion_recibe_id'])
