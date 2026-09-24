"""Fuentes mínimas inventadas; complementan las 8 pruebas históricas privadas."""
import csv
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
from app.core import Store, STATES
from app.coding import CodingService
from app.importers import import_excel, import_csv

PERSON='AAAA900101HYNBBB01'


def workbook(path):
    sheets={
        'bd':[['Curp','Nombre','Folio','legajo','No_fisicos','f_broche','carpetas'],[PERSON.lower(),'Persona ficticia',833,1,5,1,0],[PERSON,'Persona ficticia',833,2,2,0,0],[PERSON,'Duplicado de prueba',834,1,99,0,0]],
        'f833':[['CURP O RFC','folio','APELLIDO PATERNO, MATERNO, NOMBRE'],[PERSON,'833/2026','Persona ficticia'],[PERSON,'834/2026','Persona ficticia']],
        'cat_datos':[['Catálogo sintético'],[],['CONCAT','ORDEN','DOCUMENTO'],['HL-100','FEDERAL','Documento inventado']],
        'cat_incid':[['INCIDENCIA','PROBLEMA'],['REVISAR','Escaneo sintético']],
        'cont':[['CURP','Legajo','DIV1','DIV2'],[PERSON,1,3,2],[PERSON,2,2]],
        'incid':[['Incidencias ficticias'],['CURP','INCIDENCIA','DOCUMENTO','PROBLEMA'],[PERSON,'REVISAR','HL-100','Sin legajo: requiere revisión']],
        'kanban':[['Pendiente'],['Revisar expediente ficticio']]
    }
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(str(path),'w') as z:
        z.writestr('xl/workbook.xml','<workbook xmlns="'+ns+'" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join('<sheet name="'+name+'" sheetId="'+str(i)+'" r:id="r'+str(i)+'"/>' for i,name in enumerate(sheets,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships>'+''.join('<Relationship Id="r'+str(i)+'" Target="worksheets/sheet'+str(i)+'.xml"/>' for i in range(1,len(sheets)+1))+'</Relationships>')
        for i,rows in enumerate(sheets.values(),1):
            xml='<worksheet xmlns="'+ns+'"><sheetData>'
            for n,values in enumerate(rows,1):
                xml+='<row r="'+str(n)+'">'
                for c,value in enumerate(values):
                    ref=chr(65+c)+str(n)
                    xml+='<c r="'+ref+'" t="inlineStr"><is><t>'+escape(str(value))+'</t></is></c>'
                xml+='</row>'
            z.writestr('xl/worksheets/sheet'+str(i)+'.xml',xml+'</sheetData></worksheet>')


class SyntheticSources(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.s=Store(self.root/'test.sqlite3')
    def tearDown(self):self.s.db.close();self.temp.cleanup()
    def test_xlsx_normalization_legajos_duplicates_relationships(self):
        path=self.root/'sintético.xlsx';workbook(path)
        result=import_excel(self.s,path)
        self.assertEqual(result['trabajos'],3);self.assertEqual(result['bloques'],1)
        self.assertEqual(self.s.dashboard(self.s.works())['Hojas físicas confirmadas'],7)
        self.assertEqual(self.s.rows('SELECT codigo FROM catalogos WHERE tipo="documento"')[0]['codigo'],'HL-100')
        self.assertTrue(self.s.rows("SELECT * FROM pendientes WHERE tipo='Conteo por revisar'"))
        self.assertEqual(len(self.s.rows('SELECT * FROM expedientes')),2)
        self.assertTrue(self.s.rows("SELECT * FROM pendientes WHERE tipo='Incidencia por revisar'"))
        self.assertEqual(self.s.rows('SELECT COUNT(*) AS n FROM historial')[0]['n'],3)
        with self.assertRaises(ValueError):import_excel(self.s,path)
    def payload(self):
        folio=self.s.save_folio('CSV/2026','');work=self.s.save_work(folio,PERSON,'Ficticia',1)
        self.s.add_count(work,4);self.s.confirm_count(work)
        service=CodingService(self.s)
        p=service.metrics(work,[],[],self.root);p['VERSION_BAT']='3.1'
        return work,p
    def write(self,path,payload):
        with path.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(payload),delimiter=';');w.writeheader();w.writerow(payload)
    def test_csv_idempotency_unknown_pages_and_latest_snapshot(self):
        work,p=self.payload();p.update(INV_P_ARCHIVOS=1,INV_P_NO_CLASIFICADOS=1,INV_TOTAL_ARCHIVOS_CARPETAS=1,INV_TOTAL_NO_CLASIFICADOS=1,TOTAL_DIGITALES_TIFF=1,ESTADO_CONTEO_PAGINAS='PARCIAL',RESULTADO='REVISAR',ERRORES_LECTURA_TIFF=1)
        first=self.root/'uno.csv';self.write(first,p)
        self.assertEqual(import_csv(self.s,first)['ejecuciones'],1)
        second=self.root/'dos.csv';second.write_text(first.read_text()+'\n')
        self.assertEqual(import_csv(self.s,second)['duplicadas'],1)
        e=self.s.rows('SELECT * FROM ejecuciones')[0];self.s.bind_execution(e['id'],work,'Legajo','Revisión sintética')
        self.assertEqual(self.s.dashboard(self.s.works())['Inventarios parciales'],1)
        for state in STATES[1:-1]:self.s.change_state(work,state,'Avance sintético')
        with self.assertRaises(ValueError):self.s.change_state(work,STATES[-1],'No debe cerrar')
    def test_invalid_csv_preserved_in_origin(self):
        _,p=self.payload();p['TOTAL_DIGITALES_TIFF']=99
        path=self.root/'error.csv';self.write(path,p)
        self.assertEqual(import_csv(self.s,path)['rechazadas'],1)
        self.assertEqual(len(self.s.rows('SELECT * FROM origen')),1)
        self.assertFalse(self.s.rows('SELECT * FROM ejecuciones'))
