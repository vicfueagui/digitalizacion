import io
import json
import unittest
from unittest.mock import patch
from webtests import test_ux081 as ux
from webtests import test_web as fixture


class StationTests(unittest.TestCase):
    setUpClass=classmethod(fixture.WebTests.setUpClass.__func__)
    tearDownClass=classmethod(fixture.WebTests.tearDownClass.__func__)
    setUp=fixture.WebTests.setUp
    call=fixture.WebTests.call
    desk=ux.UXTests.desk
    fixture=ux.UXTests.fixture
    execute=ux.UXTests.execute

    def test_pages_preview_commit_repeat_and_stale(self):
        from django.test import Client
        _,work,ids=self.fixture(files=2,count=True)
        url='/expedientes/{}/codificacion/'.format(work)
        spec=dict(kind='split',ids=ids[:1],mode='each',disposition='replace')
        before=self.desk(work)
        preview=self.client.post(url+'plan-paginas/',json.dumps(spec),content_type='application/json')
        self.assertEqual(preview.status_code,200,preview.content)
        values=dict(spec=spec,fingerprint=preview.json()['fingerprint'],confirmado='on')
        first=self.execute(work,'pages',values,before)
        self.assertEqual(first.status_code,200,first.content)
        repeat=self.execute(work,'pages',values,before)
        self.assertEqual(first.json()['result'],repeat.json()['result'])
        self.assertEqual(len(first.json()['result']['ids']),3)
        self.assertEqual(self.execute(work,'pages',values).status_code,409)
        reader=Client();reader.force_login(self.reader)
        self.assertEqual(reader.post(url+'plan-paginas/',json.dumps(spec),content_type='application/json').status_code,403)
        strict=Client(enforce_csrf_checks=True);strict.force_login(self.user)
        self.assertEqual(strict.post(url+'plan-paginas/',json.dumps(spec),content_type='application/json').status_code,403)

    def test_pending_edit_preview_is_readonly_version_conflict_restore_revision(self):
        _,work,ids=self.fixture(files=1)
        ident=ids[0];state=self.desk(work);before=state['files'][0]
        url='/expedientes/{}/codificacion/ajuste/{}/1/'.format(work,ident)
        reply=self.client.post(url,json.dumps(dict(operations=[['rotate',90],['crop',0,0,50,50]],version=before['version'])),content_type='application/json')
        self.assertEqual(reply.status_code,200,reply.content);self.assertEqual(reply.json()['width'],50)
        self.assertEqual(self.desk(work)['files'][0]['version'],before['version'])
        r=self.execute(work,'edit_pending',dict(archivo=ident,pagina=1,operations=[['rotate',90]]),state)
        self.assertEqual(r.status_code,200,r.content)
        self.assertEqual(self.execute(work,'code',dict(archivo=ident,codigo='DP-01'),state).status_code,409)
        revision=self.call(lambda s:s.rows('SELECT id FROM revisiones_tiff WHERE archivo_id=?',(ident,))[0]['id'])
        restored=self.execute(work,'revision',dict(archivo=ident,revision=revision,confirmado='on'))
        self.assertEqual(restored.status_code,200,restored.content)
        self.assertEqual(self.desk(work)['files'][0]['version'],before['version'])
        self.assertEqual(self.client.post(url,json.dumps(dict(operations=[['replace_page','C:/no.tif',0]],version=before['version'])),content_type='application/json').status_code,400)

    def upload(self,name='scan.tif',bad=False):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        blob=io.BytesIO()
        with Image.new('RGB',(60,80),'red') as im:im.save(blob,format='TIFF')
        return SimpleUploadedFile(name,b'not tiff' if bad else blob.getvalue(),content_type='image/tiff')

    def test_import_preview_cancel_duplicates_validation_and_repeat(self):
        _,work,_=self.fixture()
        base='/expedientes/{}/codificacion/importar/'.format(work)
        response=self.client.post(base+'preparar/',dict(files=[self.upload(),self.upload()],metadata=json.dumps([{'modified':1000000000000}]*2)))
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual([e['duplicate'] for e in response.json()['entries']],[False,True])
        self.assertEqual(self.desk(work)['files'],[]) # cancelar aquí no cambia inventario
        data=dict(token=response.json()['token'],confirmado='on')
        result=self.client.post(base+'confirmar/',json.dumps(data),content_type='application/json')
        self.assertEqual(result.status_code,200,result.content);self.assertEqual(len(result.json()['state']['files']),1)
        repeat=self.client.post(base+'confirmar/',json.dumps(data),content_type='application/json')
        self.assertEqual(result.json()['result'],repeat.json()['result'])
        bad=self.client.post(base+'preparar/',dict(files=[self.upload(bad=True)],metadata='[{}]'))
        self.assertTrue(bad.json()['entries'][0]['error'])
        blocked=self.client.post(base+'confirmar/',json.dumps(dict(token=bad.json()['token'],confirmado='on')),content_type='application/json')
        self.assertEqual(blocked.status_code,409)
        self.assertEqual(len(self.desk(work)['files']),1)

    def test_import_cancel_revokes_confirmation_and_cleans_bytes(self):
        _,work,_=self.fixture()
        base='/expedientes/{}/codificacion/importar/'.format(work)
        response=self.client.post(base+'preparar/',dict(files=[self.upload()],metadata='[{}]'))
        token=response.json()['token']
        cancelled=self.client.post(base+'cancelar/',json.dumps(dict(token=token)),content_type='application/json')
        self.assertEqual(cancelled.status_code,200,cancelled.content)
        late=self.client.post(base+'confirmar/',json.dumps(dict(token=token,confirmado='on')),content_type='application/json')
        self.assertEqual(late.status_code,200,late.content)
        self.assertEqual(self.desk(work)['files'],[])
        self.assertIn('cancelada',late.json()['result']['message'])
        from django.core import signing
        folder=self.root/'.web'/'incoming'/signing.loads(token,salt='import-preview')[2]
        self.assertEqual(list(folder.rglob('*.tif')),[])

    def test_work_scope_units_query_count_and_no_decoding(self):
        from webapp.work_table import build
        folio,work,ids=self.fixture(files=2,count=True)
        def inspect(s):
            queries=[];s.db.set_trace_callback(queries.append)
            try:
                with patch('app.coding.render_page',side_effect=AssertionError('No decoding')):
                    rows,summary=build(s,{'folio':s.one('folios',folio)['numero']})
                return rows,summary,len([q for q in queries if q.startswith('SELECT')])
            finally:s.db.set_trace_callback(None)
        rows,summary,count=self.call(inspect)
        self.assertEqual(summary['works'],1);self.assertEqual(summary['uncoded'],2)
        self.assertEqual((rows[0]['hojas_confirmadas'],rows[0]['total_tiff'],rows[0]['total_paginas']),(5,2,6))
        self.assertLess(count,10)
        reply=self.client.get('/expedientes/',{'folio':self.call(lambda s:s.one('folios',folio)['numero']),'orden':'uncoded','desc':'1'})
        self.assertEqual(reply.status_code,200,reply.content[:300]);self.assertIn(b'Codificar',reply.content)

    def test_four_views_preferences_and_dto_metadata(self):
        _,work,_=self.fixture(files=1)
        data=self.desk(work)
        self.assertIn('bytes',data['files'][0]);self.assertIn('version_id',data['files'][0])
        for view in ('icons','list','details','thumbs'):
            reply=self.client.post('/preferencias/mesa/',json.dumps(dict(kind='layout',layout=dict(view=view,thumb_size=150))),content_type='application/json')
            self.assertEqual(reply.status_code,200,reply.content);self.assertEqual(self.desk(work)['preferences']['layout']['view'],view)
