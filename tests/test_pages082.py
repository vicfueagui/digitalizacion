import json
import sqlite3
import unittest
from unittest.mock import patch
import test_coding as fixture
from app.pages import PageOperations, ranges, signature, write_pages
from app.coding import digest, render_page, page_info


class PagesTests(unittest.TestCase):
    setUp=fixture.CodingTests.setUp
    tearDown=fixture.CodingTests.tearDown
    make=fixture.CodingTests.make
    def load(self,p=None):
        result=self.c.import_files(self.w,[p or self.make()],allow_duplicates=True)
        self.assertFalse(result['errores'])
        return self.s.rows('SELECT id FROM archivos_tiff ORDER BY id DESC LIMIT 1')[0]['id']

    def apply(self,ident,**kwargs):
        spec=dict(kind='split',ids=[ident],mode='each',disposition='replace',**kwargs)
        service=PageOperations(self.c);plan=service.plan(self.w,spec)
        return service.run(self.w,spec,signature(plan),'Ensayo ficticio'),plan

    def test_every_split_variant_pixels_provenance(self):
        variants=[('each',{},[1,1,1,1]),('before',{'page':3},[2,2]),('after',{'page':3},[3,1]),
                  ('cuts',{'ranges':'1,3'},[1,2,1]),('groups',{'size':3},[3,1]),('ranges',{'ranges':'1-2;3-4'},[2,2])]
        for mode,options,expected in variants:
            with self.subTest(mode=mode):
                ident=self.load(self.make(mode+'.tif',4));row=self.c.file(ident);old=digest(self.c.path(row['original']))
                spec=dict(kind='split',ids=[ident],mode=mode,disposition='replace',**options)
                service=PageOperations(self.c);plan=service.plan(self.w,spec)
                result=service.run(self.w,spec,signature(plan),'Prueba')
                self.assertEqual([self.c.file(i)['paginas'] for i in result['ids']],expected)
                self.assertFalse(self.c.file(ident)['activo']);self.assertEqual(digest(self.c.path(row['original'])),old)
                pages=self.s.rows('SELECT * FROM procedencia_paginas WHERE operacion_id=? ORDER BY archivo_id,pagina',(result['operation'],))
                self.assertEqual([p['pagina_fuente'] for p in pages],[1,2,3,4])
                self.assertTrue(all(p['version_fuente_id']==row['version_id'] for p in pages))
                self.assertTrue(all(not self.c.file(i)['codigo'] for i in result['ids']))
                self.assertEqual(self.s.one('trabajos',self.w)['fisicos'],10)

    def test_extract_copy_move_and_empty_remainder(self):
        for disposition,mode,selection,delta,counts in [('keep','multi','1,3-4',3,[3]),('replace','individual','1,3',0,[2,1,1]),('replace','multi','1-4',0,[4])]:
            ident=self.load(self.make(disposition+mode+selection+'.tif',4))
            # imports deduplicate identical content even when names differ
            spec=dict(kind='extract',ids=[ident],mode=mode,disposition=disposition,ranges=selection)
            svc=PageOperations(self.c);plan=svc.plan(self.w,spec)
            result=svc.run(self.w,spec,signature(plan),'Prueba')
            self.assertEqual(plan['extra_pages'],delta);self.assertEqual([self.c.file(i)['paginas'] for i in result['ids']],counts)
            self.assertEqual(bool(self.c.file(ident)['activo']),disposition=='keep')

    def test_mixed_modes_dimensions_dpi_merge_order(self):
        sources=[self.make('binary.tif',1,'1'),self.make('gray.tif',2,'L'),self.make('color.tif',3,'RGB')]
        from PIL import Image
        with Image.new('RGB',(77,93),(44,66,99)) as im: im.save(sources[-1],dpi=(203,407),compression='tiff_deflate')
        ids=[self.load(p) for p in sources]
        spec=dict(kind='merge',ids=list(reversed(ids)),disposition='replace',merge_pages={str(ids[1]):'2,1'})
        svc=PageOperations(self.c);plan=svc.plan(self.w,spec);result=svc.run(self.w,spec,signature(plan),'Unir ficticios')
        output=self.c.path(self.c.file(result['ids'][0])['ruta'])
        self.assertEqual([i['mode'] for i in page_info(output)],['RGB','L','L','1'])
        self.assertEqual(tuple(page_info(output)[0]['dpi']),(203,407))
        self.assertEqual(self.s.rows('SELECT archivo_fuente_id FROM procedencia_paginas WHERE archivo_id=? ORDER BY pagina',(result['ids'][0],))[0]['archivo_fuente_id'],ids[-1])
        self.assertEqual([r['pagina_fuente'] for r in self.s.rows('SELECT pagina_fuente FROM procedencia_paginas WHERE archivo_id=? ORDER BY pagina',(result['ids'][0],))],[1,2,1,1])

    def test_invalid_ranges_stale_scope_corruption_and_codes(self):
        ident=self.load(self.make(count=4));svc=PageOperations(self.c)
        for text in ('0','5','3-2','1,1','1-3,3-4','1,,2'):
            with self.assertRaises(ValueError): ranges(text,4)
        for text in ('1-2;4','1-3;3-4'):
            with self.assertRaises(ValueError):svc.plan(self.w,dict(kind='split',ids=[ident],mode='ranges',ranges=text,disposition='replace'))
        spec=dict(kind='extract',ids=[ident],mode='multi',ranges='1',disposition='keep')
        old=signature(svc.plan(self.w,spec));self.c.save_edit(ident,0,[('rotate',90)])
        with self.assertRaises(ValueError):svc.run(self.w,spec,old,'Prueba')
        other=self.s.save_work(self.f,'AAAA900101HYNBBB01','Prueba',2);self.c.import_files(other,[self.make('other.tif')]);foreign=self.c.files(other)[0]['id']
        with self.assertRaises(ValueError):svc.plan(self.w,dict(kind='merge',ids=[ident,foreign],disposition='keep'))
        second=self.load(self.make('second.tif',2));self.c.assign(ident,'DP-01');self.c.assign(second,'HL-01')
        with self.assertRaises(ValueError):svc.plan(self.w,dict(kind='merge',ids=[ident,second],disposition='keep',keep_code=True))
        self.c.path(self.c.file(second)['ruta']).write_bytes(b'corrupt')
        with self.assertRaises(ValueError):svc.plan(self.w,dict(kind='extract',ids=[second],ranges='1',mode='multi',disposition='keep'))

    def test_interruptions_sources_survive_no_partial_activation(self):
        class Cut(BaseException):pass
        for stage in ('prepared','file-1','verified','registered-1','retired','before-commit'):
            with self.subTest(stage=stage):
                ident=self.load(self.make(stage+'.tif',3));row=self.c.file(ident)
                spec=dict(kind='split',ids=[ident],mode='each',disposition='replace');svc=PageOperations(self.c)
                plan=svc.plan(self.w,spec)
                def interrupt(at):
                    if at==stage:raise Cut()
                with self.assertRaises(Cut):svc.run(self.w,spec,signature(plan),'Simular corte',interrupt)
                self.assertTrue(self.c.file(ident)['activo']);self.assertEqual(digest(self.c.path(row['ruta'])),row['hash_actual'])
                pending=self.s.rows("SELECT * FROM operaciones_tiff WHERE estado='Preparada'")
                self.assertEqual(len(pending),1)
                self.assertFalse(self.s.rows('SELECT * FROM procedencia_paginas WHERE operacion_id=?',(pending[0]['id'],)))
                with self.assertRaises(ValueError):self.c.assign(ident,'DP-01')
                self.assertEqual(self.c.recover(self.w),1);self.assertEqual(self.c.recover(self.w),0)
                self.c.active_work(self.w)

    def test_committed_interruption_does_not_roll_back_or_recover(self):
        ident=self.load(self.make(count=2));svc=PageOperations(self.c)
        spec=dict(kind='split',ids=[ident],mode='each',disposition='replace');plan=svc.plan(self.w,spec)
        def cut(stage):
            if stage=='committed':raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):svc.run(self.w,spec,signature(plan),'Prueba',cut)
        self.assertFalse(self.c.file(ident)['activo']);self.assertEqual(len(self.c.files(self.w)),2)
        self.assertEqual(self.c.recover(self.w),0)
        with self.assertRaises(ValueError):svc.run(self.w,spec,signature(plan),'No duplicar')

    def test_backup_restore_preserves_provenance_and_migration(self):
        from app.backup import create_backup,restore_backup
        from app.core import Store
        ident=self.load(self.make(count=2));self.apply(ident)
        before=self.s.rows('SELECT * FROM procedencia_paginas')
        target=self.root/'backup';create_backup(self.s,target)
        destination=self.root/'restored';restore_backup(target,destination)
        restored=Store(destination/'datos'/'digitalizacion.sqlite3')
        try:
            self.assertEqual(restored.rows('SELECT * FROM procedencia_paginas'),before)
            self.assertEqual(restored.db.execute("SELECT value FROM meta WHERE key='coding_schema_version'").fetchone()[0],'4')
            self.assertFalse(restored.db.execute('PRAGMA foreign_key_check').fetchall())
        finally:restored.db.close()

    def test_provenance_is_immutable_and_failure_leaves_source(self):
        ident=self.load(self.make(count=2));svc=PageOperations(self.c)
        spec=dict(kind='split',ids=[ident],mode='each',disposition='replace');plan=svc.plan(self.w,spec)
        with patch('app.pages.verify_pages',side_effect=ValueError('No coincide')):
            with self.assertRaises(ValueError):svc.run(self.w,spec,signature(plan),'Prueba')
        self.assertTrue(self.c.file(ident)['activo']);self.c.recover(self.w)
        self.apply(ident)
        with self.assertRaises(sqlite3.IntegrityError),self.s.db:self.s.db.execute('UPDATE procedencia_paginas SET pagina_fuente=99')

    def test_deliveries_originals_incidents_and_import_metrics(self):
        from app.analytics import Cube
        ident=self.load(self.make(count=3));self.c.assign(ident,'DP-01');self.c.organize(self.w)
        delivery=self.s.rows('SELECT * FROM entregas WHERE trabajo_id=?',(self.w,))[0]
        folder=self.c.path(delivery['ruta']);saved={str(p):digest(p) for p in folder.rglob('*') if p.is_file()}
        self.c.mark_correction(ident,1,'Hoja física por localizar','Ficticia')
        result,plan=self.apply(ident)
        self.assertIsNone(self.s.latest(self.w))
        self.assertEqual(self.s.rows('SELECT estado FROM correcciones_tiff WHERE archivo_id=?',(ident,))[0]['estado'],'Pendiente')
        self.assertEqual(saved,{str(p):digest(p) for p in folder.rglob('*') if p.is_file()})
        cube=Cube(self.s).snapshot(self.s.works(),source='Ingresos TIFF')
        self.assertEqual(cube['totales']['tiff'],1) # los derivados no se atribuyen a otros escaneos
        self.assertEqual(self.s.one('trabajos',self.w)['fisicos'],10)

    def test_additive_migration_preserves_prior_tables(self):
        from app.migrations import migrate
        self.load(self.make(count=2))
        with self.s.db:
            self.s.db.execute('DROP TABLE procedencia_paginas')
            self.s.db.execute("UPDATE meta SET value='3' WHERE key='coding_schema_version'")
        tables=[r['name'] for r in self.s.rows("SELECT name FROM sqlite_master WHERE type='table' AND name!='meta'")]
        before={t:self.s.rows('SELECT * FROM "'+t+'"') for t in tables}
        migrate(self.s)
        self.assertEqual({t:self.s.rows('SELECT * FROM "'+t+'"') for t in tables},before)
        self.assertEqual(self.s.rows('SELECT * FROM procedencia_paginas'),[])
        self.assertFalse(self.s.db.execute('PRAGMA foreign_key_check').fetchall())

    def test_no_cross_integration_and_confirmation_of_common_code(self):
        ident=self.load(self.make(count=2));self.c.assign(ident,'DP-01')
        svc=PageOperations(self.c)
        spec=dict(kind='split',ids=[ident],mode='each',disposition='replace',keep_code=True)
        plan=svc.plan(self.w,spec);result=svc.run(self.w,spec,signature(plan),'Código confirmado')
        self.assertTrue(all(self.c.file(i)['codigo']=='DP-01' for i in result['ids']))
        # Simular un contexto anterior únicamente en esta base ficticia.
        current=self.s.one('trabajos',self.w)['integracion_actual_id']
        with patch('app.pages.Integrations.current',return_value={'id':current+100}):
            with self.assertRaises(ValueError):svc.plan(self.w,dict(spec,ids=[result['ids'][0]]))
