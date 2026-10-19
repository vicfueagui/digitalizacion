"""Regresión funcional 0.8.1: workspace nuevo con identidades y TIFF inventados."""
import html
import io
import json
import re
import sqlite3
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from webtests import test_web as fixture_web


class UXTests(unittest.TestCase):
    setUpClass = classmethod(fixture_web.WebTests.setUpClass.__func__)
    tearDownClass = classmethod(fixture_web.WebTests.tearDownClass.__func__)
    setUp = fixture_web.WebTests.setUp
    call = fixture_web.WebTests.call
    ticket = fixture_web.WebTests.ticket

    def fixture(self, count=False, files=0):
        def create(s):
            from app.coding import CodingService
            from app.operations import Operations
            from PIL import Image
            folio=s.save_folio('UX-FICTICIO-'+uuid.uuid4().hex[:10],'2026-09-01')
            legajo=100+s.rows('SELECT COUNT(*) AS n FROM trabajos')[0]['n']
            work=s.save_work(folio,'AAAA900101HYNBBB01','Persona ficticia ÁRBOL',legajo,recibido='2026-09-01')
            row=s.one('trabajos',work)
            Operations(s).validate_item(row['prestamo_item_id'],'Aceptado',row['curp'],legajo,'Cotejo sintético')
            if count:s.add_count(work,5);s.confirm_count(work)
            coder=CodingService(s);ids=[]
            for n in range(files):
                target=self.root/'muestras'/('ux-'+uuid.uuid4().hex+'.tif')
                frames=[Image.new('RGB',(80,120),(n*40+20,p*70+20,80)) for p in range(3)]
                frames[0].save(target,save_all=True,append_images=frames[1:]);[f.close() for f in frames]
                result=coder.import_files(work,[target]);self.assertFalse(result['errores'])
                ids.append(coder.files(work)[-1]['id'])
            return folio,work,ids
        return self.call(create)

    def desk(self, work, client=None):
        result=(client or self.client).get('/expedientes/{}/codificacion/'.format(work))
        self.assertEqual(result.status_code,200)
        match=re.search(r'<script id="desk-data" type="application/json">(.*?)</script>',result.content.decode(),re.S)
        return json.loads(match.group(1))

    def execute(self, work, action, values, state=None, client=None):
        data=state or self.desk(work,client)
        values=dict(values)
        values.setdefault('versions',{str(f['id']):[f['version_id'],f['version'],f['code'] or None,int(f['active'])] for f in data['files']})
        return (client or self.client).post('/expedientes/{}/codificacion/accion/'.format(work),
            data=json.dumps(dict(action=action,ticket=data['tokens'].get(action,''),data=dict(motivo='Prueba ficticia',**values))),content_type='application/json')

    def count(self, work, action, **values):
        url='/expedientes/{}/conteo/'.format(work)
        return self.client.post(url,dict(ticket=self.ticket(url),operacion=action,motivo='Bloque ficticio',**values))

    def test_count_blocks_confirmation_correction_and_audit(self):
        _,w,_=self.fixture()
        for n in (12,8):self.assertEqual(self.count(w,'agregar',cantidad=n).status_code,302)
        self.assertEqual(self.count(w,'confirmar',confirmado='on').status_code,302)
        self.assertEqual(self.call(lambda s:s.one('trabajos',w)['fisicos']),20)
        self.assertEqual(self.count(w,'agregar',cantidad=50).status_code,200)
        self.assertEqual(self.call(lambda s:s.one('trabajos',w)['fisicos']),20)
        self.assertEqual(self.count(w,'reabrir',confirmado='on').status_code,302)
        block=self.call(lambda s:s.rows('SELECT id FROM conteos WHERE trabajo_id=?',(w,))[0]['id'])
        self.assertEqual(self.count(w,'corregir',bloque=block,cantidad=10).status_code,302)
        self.assertEqual(self.count(w,'confirmar',confirmado='on').status_code,302)
        self.assertEqual(self.call(lambda s:s.one('trabajos',w)['fisicos']),18)
        self.assertTrue(self.call(lambda s:s.rows("SELECT id FROM auditoria WHERE accion='reabrir conteo'")))

    def test_count_duplicate_and_stale_tab_do_not_overwrite(self):
        _,w,_=self.fixture();url='/expedientes/{}/conteo/'.format(w)
        token,stale=self.ticket(url),self.ticket(url)
        values=dict(ticket=token,operacion='agregar',cantidad=7,motivo='Ficticio')
        for _ in range(2):self.assertEqual(self.client.post(url,values).status_code,302)
        rejected=self.client.post(url,dict(ticket=stale,operacion='confirmar',confirmado='on',motivo='Ficticio'))
        self.assertIn('cambiaron',rejected.content.decode())
        self.assertEqual(self.call(lambda s:s.count_total(w)),7)
        self.assertIsNone(self.call(lambda s:s.one('trabajos',w)['fisicos']))

    def integrate(self,w):
        def run(s):
            from app.coding import CodingService
            from app.delivery import Deliveries
            from app.review import Reviews
            from app.integrations import Integrations
            c=CodingService(s)
            for f in c.files(w):c.assign(f['id'],'DP-01')
            d=Deliveries(s).prepare(w);r=Reviews(s);r.begin(d);r.approve(d,'Aprobación ficticia')
            folio=s.save_folio('ADICIONAL-FICTICIO-'+uuid.uuid4().hex[:8],'2026-10-01')
            integration=Integrations(s).start(w,'Documentación ficticia nueva','2026-10-01',folio=folio,reference='Acuse ficticio',confirmed=True)
            return folio,integration,d
        return self.call(run)

    def test_folio_historical_receipt_count_separation_and_units(self):
        f,w,ids=self.fixture(count=True,files=1);f2,i,d=self.integrate(w)
        from webapp.folio_context import folio_view
        old,new=self.call(lambda s:(folio_view(s,f),folio_view(s,f2)))
        self.assertTrue(old['items'][0]['historica']);self.assertFalse(new['items'][0]['historica'])
        self.assertEqual((old['items'][0]['fisicos'],old['items'][0]['tiff'],old['items'][0]['paginas']),(5,1,3))
        self.assertIsNone(new['items'][0]['fisicos']);self.assertEqual(new['items'][0]['tiff'],0)
        self.count(w,'agregar',cantidad=2);self.count(w,'confirmar',confirmado='on')
        from webapp.counting import snapshot
        state=self.call(lambda s:snapshot(s,w));self.assertEqual((state['historical'],state['total']),(5,2))
        oldblock=self.call(lambda s:s.rows('SELECT id FROM conteos WHERE trabajo_id=? ORDER BY id',(w,))[0]['id'])
        self.count(w,'reabrir',confirmado='on')
        self.assertIn('no pertenece',self.count(w,'corregir',bloque=oldblock,cantidad=900).content.decode())
        from app.delivery import Deliveries
        self.assertEqual(len(self.call(lambda s:Deliveries(s).verify(d))['items']),1)
        oldid=old['items'][0]['integracion_id']
        self.assertEqual(self.client.get('/expedientes/{}/?recepcion={}'.format(w,oldid)).status_code,200)
        self.assertEqual(self.client.get('/expedientes/{}/?recepcion=999999'.format(w)).status_code,404)

    def test_folio_search_legajos_summary_and_ajax(self):
        f,w,_=self.fixture()
        from app.operations import Operations
        self.call(lambda s:Operations(s).expect(f,'EEEE900102MYNCCC02',2,name='Persona ficticia segunda'))
        response=self.client.get('/folios/',dict(folio=f,q='ARBOL'),HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code,200);self.assertNotIn(b'<html',response.content)
        from webapp.folio_context import folio_view
        state=self.call(lambda s:folio_view(s,f,condition='Esperado'))
        self.assertEqual(len(state['items']),1);self.assertEqual(state['items'][0]['legajo_visible'],2)
        self.assertEqual({r['label']:r['value'] for r in state['summary']}['Pendientes'],1)
        self.assertIn('ÁRBOL',response.content.decode())
        self.assertIn('2026-09-01',response.content.decode())

    def test_historical_folio_never_selects_old_principal(self):
        f,w,_=self.fixture()
        def newer(s):
            old=s.one('trabajos',w);f2=s.save_folio('CICLO-FICTICIO-'+uuid.uuid4().hex[:7],'')
            return s.save_work(f2,old['curp'],'Persona ficticia ÁRBOL',old['legajo'])
        current=self.call(newer)
        from webapp.domain import listing
        number=self.call(lambda s:s.one('folios',f)['numero'])
        ids=self.call(lambda s:[r['id'] for r in listing(s,dict(folio=number))])
        self.assertNotIn(w,ids)
        # El folio sigue mostrando su recepción original de forma explícita.
        from webapp.folio_context import folio_view
        self.assertEqual(self.call(lambda s:folio_view(s,f)['items'][0]['ciclo']),w)
        self.assertTrue(self.call(lambda s:folio_view(s,f)['items'][0]['ciclo_historico']))
        self.assertEqual(self.call(lambda s:[r['id'] for r in s.works() if r['id']==current]),[current])

    def test_desk_list_catalog_shortcuts_no_images_or_paths(self):
        _,w,ids=self.fixture(count=True,files=2)
        with patch('webapp.desk.render_page',side_effect=AssertionError('No abrir al listar')):state=self.desk(w)
        self.assertEqual([f['id'] for f in state['files']],ids)
        self.assertNotIn('ruta',json.dumps(state));self.assertTrue(all(c['number'] for c in state['catalog']))
        combinations=[(c['combo'],c['number']) for c in state['catalog']]
        self.assertEqual(len(combinations),len(set(combinations)))

    def test_batch_code_idempotent_names_ids_originals_preserved(self):
        _,w,ids=self.fixture(count=True,files=2)
        before=self.call(lambda s:s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=?',(w,)))
        state=self.desk(w);values=dict(seleccion=ids,codigo='DP-01',confirmado='on')
        for _ in range(2):self.assertEqual(self.execute(w,'batch_code',values,state).status_code,200)
        after=self.call(lambda s:s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=?',(w,)))
        self.assertEqual([r['id'] for r in before],[r['id'] for r in after])
        self.assertEqual(len({r['ruta'] for r in after}),2)
        self.assertEqual([r['hash_original'] for r in before],[r['hash_original'] for r in after])
        self.assertTrue(all(r['codigo']=='DP-01' for r in after))
        self.assertEqual(len(self.call(lambda s:s.rows('SELECT id FROM lotes_tiff WHERE trabajo_id=?',(w,)))),1)

    def test_batch_confirm_foreign_and_partial_result(self):
        _,w,ids=self.fixture(count=True,files=2);_,other,foreign=self.fixture(count=True,files=1)
        self.assertEqual(self.execute(w,'batch_code',dict(seleccion=ids,codigo='DP-01')).status_code,409)
        self.assertEqual(self.execute(w,'batch_code',dict(seleccion=ids+foreign,codigo='DP-01',confirmado='on')).status_code,409)
        from app.batch_tiff import BatchTiff
        from app.coding import CodingService
        def fail(ident):
            if ident==ids[1]:raise OSError('Corte sintético')
        result=self.call(lambda s:BatchTiff(CodingService(s)).run(w,ids,'codificar','Ensayo parcial',fail,code='DP-01'))
        self.assertEqual(result['completados'],ids[:1]);self.assertEqual(result['pendientes'],ids[1:])
        self.assertEqual(result['estado'],'Parcial')
        continued=self.execute(w,'batch_code',dict(seleccion=ids[1:],codigo='DP-01',confirmado='on'))
        self.assertEqual(continued.status_code,200)

    def test_retire_recover_batch_keeps_original_hashes(self):
        _,w,ids=self.fixture(count=True,files=2)
        before=self.call(lambda s:[r['hash_original'] for r in s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=?',(w,))])
        for action,active in [('retirar',0),('recuperar',1)]:
            answer=self.execute(w,'batch',dict(seleccion=ids,tipo=action,confirmado='on'))
            self.assertEqual(answer.status_code,200,answer.content)
            self.assertEqual(self.call(lambda s:[r['activo'] for r in s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=?',(w,))]),[active,active])
        self.assertEqual(before,self.call(lambda s:[r['hash_original'] for r in s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=?',(w,))]))

    def test_fine_rotation_crop_multipage_history_original_preview(self):
        _,w,ids=self.fixture(count=True,files=1);ident=ids[0]
        original=self.call(lambda s:s.rows('SELECT * FROM archivos_tiff WHERE id=?',(ident,))[0]['hash_original'])
        for values in [dict(tipo='girar',angulo=.4),dict(tipo='recortar',x1=1,y1=1,x2=60,y2=90)]:
            answer=self.execute(w,'edit',dict(archivo=ident,pagina=2,**values));self.assertEqual(answer.status_code,200,answer.content)
        row=self.call(lambda s:s.rows('SELECT * FROM archivos_tiff WHERE id=?',(ident,))[0]);self.assertEqual(row['paginas'],3);self.assertEqual(row['hash_original'],original)
        base='/expedientes/{}/codificacion/'.format(w)
        history=self.client.get(base+'historial/{}/2/'.format(ident)).json();self.assertEqual(len(history['versions']),2)
        for query in ['', '?original=1','?revision='+str(history['versions'][0]['id'])]:
            self.assertEqual(self.client.get(base+'imagen/{}/3/'.format(ident)+query).status_code,200)
        self.assertEqual(self.client.get(base+'imagen/{}/4/'.format(ident)).status_code,404)
        answer=self.execute(w,'original',dict(archivo=ident,confirmado='on'));self.assertEqual(answer.status_code,200,answer.content)
        self.assertEqual(self.call(lambda s:s.rows('SELECT * FROM archivos_tiff WHERE id=?',(ident,))[0]['hash_actual']),original)

    def test_thumbnail_lazy_cache_bounded_and_private(self):
        _,w,ids=self.fixture(count=True,files=2)
        from webapp import desk
        desk.THUMBNAILS.clear()
        with patch('webapp.desk.render_page',wraps=desk.render_page) as render:
            self.desk(w);self.assertEqual(render.call_count,0)
            for _ in range(2):
                response=self.client.get('/expedientes/{}/codificacion/imagen/{}/1/?miniatura=1'.format(w,ids[0]))
                self.assertEqual(response.status_code,200);self.assertIn('no-store',response['Cache-Control'])
            self.assertEqual(render.call_count,1)
        from PIL import Image
        with Image.open(io.BytesIO(response.content)) as image:self.assertLessEqual(max(image.size),240)
        with patch.object(desk,'THUMB_LIMIT',1):
            self.client.get('/expedientes/{}/codificacion/imagen/{}/1/?miniatura=1'.format(w,ids[1]))
        self.assertEqual(len(desk.THUMBNAILS),1)
        _,foreign,_=self.fixture()
        self.assertEqual(self.client.get('/expedientes/{}/codificacion/imagen/{}/1/'.format(foreign,ids[0])).status_code,404)

    def test_preferences_two_users_persist_after_login_no_global_change(self):
        from django.test import Client
        from webapp.preferences import read
        _,w,_=self.fixture();data=self.desk(w);code=data['catalog'][0]['id']
        baseline=self.call(lambda s:s.rows('SELECT * FROM atajos_numericos'))
        def pref(client,values):return client.post('/preferencias/mesa/',json.dumps(values),content_type='application/json')
        self.assertEqual(pref(self.client,dict(kind='favorite',catalog_id=code,enabled=True)).status_code,200)
        self.assertEqual(pref(self.client,dict(kind='layout',layout=dict(left=290,advance=False,view='thumbs'))).status_code,200)
        second=Client();second.force_login(self.reader)
        self.assertNotIn(code,read(self.reader)['favorites'])
        self.client.logout();self.assertTrue(self.client.login(username='operador_ficticio',password='ClaveFicticiaWeb_2026!'))
        again=self.desk(w);self.assertIn(code,again['preferences']['favorites']);self.assertEqual(again['preferences']['layout']['left'],290)
        self.assertFalse(again['preferences']['layout']['advance'])
        self.assertEqual(pref(second,dict(kind='layout',layout=dict(left=9999))).status_code,400)
        self.assertEqual(baseline,self.call(lambda s:s.rows('SELECT * FROM atajos_numericos')))

    def test_preferences_migration_backup_restore(self):
        from django.core.management import call_command
        from django.db import connection
        from webapp.preferences import update,read
        from webapp.backup import create_web_backup,restore_web_backup
        _,w,_=self.fixture();code=self.desk(w)['catalog'][0]['id'];update(self.user,dict(kind='favorite',catalog_id=code,enabled=True),{code})
        call_command('makemigrations','webapp',check=True,dry_run=True,verbosity=0)
        self.assertIn('webapp_deskpreferences',connection.introspection.table_names())
        folder=self.root.parent/('respaldo-ux-'+uuid.uuid4().hex[:8])
        self.call(lambda s:create_web_backup(s,folder))
        restored=restore_web_backup(folder,self.root.parent/('restaurado-ux-'+uuid.uuid4().hex[:8]))
        db=sqlite3.connect(str(restored/'.web'/'acceso.sqlite3'))
        try:row=db.execute('SELECT favorites FROM webapp_deskpreferences WHERE user_id=?',(self.user.pk,)).fetchone()
        finally:db.close()
        self.assertIn(code,json.loads(row[0]))

    def test_concurrent_favorites_preserve_both_and_layout(self):
        import threading
        from django.contrib.auth.models import User
        from django.db import connections
        from webapp.preferences import update,read
        account=User.objects.create_user('preferencias_'+uuid.uuid4().hex[:8])
        _,w,_=self.fixture();ids=[c['id'] for c in self.desk(w)['catalog'][:2]]
        update(account,dict(kind='layout',layout=dict(left=310,advance=False)),set(ids))
        gate=threading.Barrier(2);errors=[]
        def save(ident):
            try:
                gate.wait();update(account,dict(kind='favorite',catalog_id=ident,enabled=True),set(ids))
            except Exception as error:errors.append(str(error))
            finally:connections.close_all()
        threads=[threading.Thread(target=save,args=(i,)) for i in ids]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        self.assertFalse(errors);value=read(account)
        self.assertEqual(set(value['favorites']),set(ids));self.assertEqual(value['layout']['left'],310)
        self.assertFalse(value['layout']['advance'])

    def test_partial_http_batch_identifies_completed_and_pending(self):
        from app.coding import CodingService
        _,w,ids=self.fixture(count=True,files=2);original=CodingService.assign
        def interrupted(coder,ident,code):
            if ident==ids[1]:raise OSError('Interrupción ficticia')
            return original(coder,ident,code)
        with patch.object(CodingService,'assign',interrupted):
            response=self.execute(w,'batch_code',dict(seleccion=ids,codigo='DP-01',confirmado='on'))
        self.assertEqual(response.status_code,200)
        result=response.json()['result'];self.assertTrue(result['warning'])
        self.assertEqual(result['batch']['completados'],ids[:1]);self.assertEqual(result['batch']['pendientes'],ids[1:])

    def test_preferences_migration_reversible_without_business_change(self):
        from django.core.management import call_command
        from django.db import connection
        # Solo tabla de preferencias de esta base de acceso enteramente ficticia.
        before=self.call(lambda s:s.rows('SELECT * FROM integraciones'))
        try:
            call_command('migrate','webapp','zero',interactive=False,verbosity=0)
            self.assertNotIn('webapp_deskpreferences',connection.introspection.table_names())
        finally:call_command('migrate','webapp',interactive=False,verbosity=0)
        self.assertIn('webapp_deskpreferences',connection.introspection.table_names())
        self.assertEqual(before,self.call(lambda s:s.rows('SELECT * FROM integraciones')))

    def test_permissions_csrf_ticket_binding_and_get_only(self):
        from django.test import Client
        _,w,ids=self.fixture(count=True,files=1);reader=Client();reader.force_login(self.reader)
        state=self.desk(w);self.assertFalse(self.desk(w,reader)['tokens'])
        self.assertEqual(self.execute(w,'code',dict(archivo=ids[0],codigo='DP-01'),state,reader).status_code,403)
        self.assertEqual(reader.get('/expedientes/{}/conteo/'.format(w)).status_code,403)
        strict=Client(enforce_csrf_checks=True);strict.force_login(self.user)
        self.assertEqual(self.execute(w,'code',dict(archivo=ids[0],codigo='DP-01'),state,strict).status_code,403)
        self.assertEqual(strict.post('/preferencias/mesa/',json.dumps(dict(kind='layout',layout={})),content_type='application/json').status_code,403)
        _,other,_=self.fixture();self.assertEqual(self.execute(other,'code',dict(archivo=ids[0],codigo='DP-01'),state).status_code,403)

    def analytics(self,filters=None,**config):
        from webapp.analytics_view import build
        options=dict(period='Mes',dimension='Folio',source='Inventario por recepción',start='',end='');options.update(config)
        return self.call(lambda s:build(s,filters or {},options))

    def test_bi_unique_curps_legajos_empty_percent_and_six_stages(self):
        f,w,_=self.fixture(count=True,files=1)
        self.call(lambda s:s.save_work(f,'AAAA900101HYNBBB01','Persona ficticia',999,recibido='2026-09-01'))
        number=self.call(lambda s:s.one('folios',f)['numero']);data=self.analytics(dict(folio=number))
        self.assertEqual(data['snapshot']['metrica']['CURP distintas'],1)
        self.assertEqual(data['snapshot']['metrica']['Trabajos activos'],2)
        self.assertEqual(len(data['snapshot']['etapas']),6)
        self.assertEqual([r['label'] for r in data['snapshot']['etapas']][-2:],['Por aprobar','Cerrados'])
        empty=self.analytics(dict(folio='INEXISTENTE-FICTICIO'));self.assertIsNone(empty['coding_percent'])
        self.assertTrue(all(r['percent'] is None for r in empty['snapshot']['etapas']))

    def test_bi_dates_folio_scope_integrations_csv_no_image_reads(self):
        f,w,ids=self.fixture(count=True,files=1);f2,i,d=self.integrate(w)
        number=self.call(lambda s:s.one('folios',f2)['numero'])
        self.count(w,'agregar',cantidad=2);self.count(w,'confirmar',confirmado='on')
        with patch('app.coding.page_info',side_effect=AssertionError('Indicadores no abren TIFF')):
            data=self.analytics(dict(folio=number),start='2026-10-01',end='2026-10-31')
            response=self.client.get('/indicadores/',dict(folio=number,desde='2026-10-01',hasta='2026-10-31',exportar='csv'))
        self.assertEqual(data['cube']['totales']['hojas'],2);self.assertEqual(data['cube']['totales']['tiff'],0)
        self.assertEqual(data['series'],[dict(label='2026-10',initial=0,additional=1)])
        self.assertEqual(response.status_code,200);self.assertIn(number,response.content.decode('utf-8-sig'))
        self.assertNotIn(self.call(lambda s:s.one('folios',f)['numero']),response.content.decode('utf-8-sig'))
        self.assertEqual(self.analytics(dict(folio=number,estado='Expediente cerrado'))['cube']['filas'],[])
        self.assertEqual(self.analytics(dict(folio=number,digitalizador='INEXISTENTE'))['cube']['filas'],[])

    def test_bi_unknown_dates_not_fabricated_and_markup(self):
        f,w,_=self.fixture()
        def unknown(s):
            with s.db:s.db.execute('UPDATE integraciones SET recibido=NULL WHERE trabajo_id=?',(w,));s.db.execute('UPDATE trabajos SET recibido=NULL WHERE id=?',(w,))
        self.call(unknown);number=self.call(lambda s:s.one('folios',f)['numero'])
        data=self.analytics(dict(folio=number),start='2026-01-01')
        self.assertEqual(data['cube']['sin_fecha_excluidos'],1);self.assertEqual(data['series'],[])
        response=self.client.get('/indicadores/',dict(folio='INEXISTENTE-FICTICIO'))
        self.assertEqual(response.status_code,200);self.assertIn('Sin base',response.content.decode())
        self.assertIn(b'chart-reception',response.content);self.assertIn(b'<table',response.content)
