import datetime
import json
import unittest
from unittest.mock import patch
from app.analytics import Cube,bucket
import test_coding as fixture


class CubeTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    load=fixture.CodingTests.load

    def test_iso_week_crosses_calendar_year(self):
        self.assertEqual(bucket(datetime.date(2021,1,1),'Semana ISO'),'2020-S53')
        self.assertEqual(bucket(datetime.date(2021,1,4),'Semana ISO'),'2021-S01')
        self.assertEqual(bucket(None,'Día'),'Sin fecha')

    def test_unknown_dates_never_become_current_period(self):
        data=Cube(self.s).snapshot(self.s.works())
        self.assertEqual(data['sin_fecha'],1);self.assertEqual(data['filas'][0]['periodo'],'Sin fecha')
        filtered=Cube(self.s).snapshot(self.s.works(),start='2020-01-01')
        self.assertEqual(filtered['sin_fecha_excluidos'],1);self.assertEqual(filtered['filas'],[])

    def test_retired_inventory_separate_from_import_activity(self):
        ident=self.load(self.make('example.tif',2));self.c.exclude(ident,'Prueba ficticia')
        with self.s.db:self.s.db.execute("UPDATE archivos_tiff SET importado='2021-01-01T10:00:00-06:00'")
        with patch('app.delivery.Deliveries.basis',side_effect=AssertionError('No leer TIFF')):
            stock=Cube(self.s).snapshot(self.s.works())
            activity=Cube(self.s).snapshot(self.s.works(),source='Ingresos TIFF',period='Semana ISO')
        self.assertEqual(stock['totales']['tiff'],0);self.assertEqual(activity['totales']['paginas'],2)
        self.assertIsNone(activity['totales']['hojas']);self.assertIsNone(activity['filas'][0]['integraciones'])
        self.assertEqual(activity['filas'][0]['periodo'],'2020-S53')

    def test_empty_scope_dates_export(self):
        service=Cube(self.s);data=service.snapshot([])
        self.assertEqual(data['totales']['expedientes_distintos'],0);self.assertEqual(data['filas'],[])
        with self.assertRaises(ValueError):service.snapshot(self.s.works(),start='2026-10-01',end='2026-01-01')
        path=service.export(data,self.root/'cube-export')
        self.assertEqual(json.loads((path/'contexto.json').read_text(encoding='utf-8'))['totales'],data['totales'])
