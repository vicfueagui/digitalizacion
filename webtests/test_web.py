import gc
import hashlib
import html
import io
import json
import re
import tempfile
import threading
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.gettempdir()).parent / ('web-' + uuid.uuid4().hex[:8])
        from app.demo import create_demo
        create_demo(cls.root)
        from iniciar_web import configure, checked_workspace
        configure(checked_workspace(cls.root))
        from django.contrib.auth.models import User, Group
        cls.user = User.objects.create_superuser('operador_ficticio', password='ClaveFicticiaWeb_2026!')
        cls.reader = User.objects.create_user('consulta_ficticia', password='ClaveFicticiaWeb_2026!')
        cls.reader.groups.add(Group.objects.get_or_create(name='Consulta')[0])
        from webapp.engine import start
        cls.engine = start(cls.root)

    @classmethod
    def tearDownClass(cls):
        from webapp.engine import stop
        stop()
        from django.db import connections
        connections.close_all()

    def setUp(self):
        from django.test import Client
        self.client = Client()
        self.client.force_login(self.user)

    def call(self, fn, ticket=None):
        return self.engine.call('Operador ficticio de pruebas', fn, ticket)

    def ticket(self, url, client=None):
        response = (client or self.client).get(url)
        self.assertEqual(response.status_code, 200, response.content[:250])
        found = re.search(r'name="ticket" value="([^"]+)"', response.content.decode())
        self.assertIsNotNone(found)
        return html.unescape(found.group(1))

    def post(self, action, data=None, work=0):
        url = '/expedientes/{}/accion/{}/'.format(work, action) if work else '/accion/{}/'.format(action)
        values = dict(data or {}, ticket=self.ticket(url))
        values.setdefault('motivo', 'Evidencia ficticia cotejada en prueba')
        response = self.client.post(url, values)
        self.assertEqual(response.status_code, 302, response.content.decode()[-5000:])
        return response

    def test_pages_and_all_action_forms_render(self):
        from webapp.forms import LABELS
        work = self.call(lambda s: s.works()[0]['id'])
        for url in ['/', '/expedientes/', '/kanban/', '/folios/', '/indicadores/', '/ayuda/', '/administracion/', '/importar-lista/', '/expedientes/{}/'.format(work)]:
            with self.subTest(url=url):
                result = self.client.get(url)
                self.assertEqual(result.status_code, 200)
                self.assertIn('no-store', result['Cache-Control'])
                self.assertIn(b'DEMOSTRACI', result.content)
        standalone = {'folio', 'expected', 'receipt', 'accept', 'difference', 'legajos', 'catalog', 'directory', 'backup'}
        for action in LABELS:
            with self.subTest(action=action):
                self.ticket('/accion/{}/'.format(action) if action in standalone else '/expedientes/{}/accion/{}/'.format(work, action))

    def test_auth_csrf_host_and_loopback(self):
        from django.test import Client
        anonymous = Client()
        self.assertEqual(anonymous.get('/expedientes/').status_code, 302)
        self.assertEqual(anonymous.get('/static/../datos/digitalizacion.sqlite3').status_code, 404)
        self.assertEqual(self.client.get('/', REMOTE_ADDR='192.0.2.8').status_code, 403)
        self.assertEqual(self.client.get('/', HTTP_HOST='sitio-no-autorizado.invalid').status_code, 400)
        strict = Client(enforce_csrf_checks=True); strict.force_login(self.user)
        self.assertEqual(strict.post('/accion/folio/', {'numero': 'NO-CREAR'}).status_code, 403)
        self.assertEqual(self.call(lambda s: len(s.rows("SELECT id FROM folios WHERE numero='NO-CREAR'"))), 0)

    def test_consultation_cannot_write_and_get_does_not_count(self):
        from django.test import Client
        reader = Client(); reader.force_login(self.reader)
        work = self.call(lambda s: s.works()[0]['id'])
        before = self.call(lambda s: s.rows('SELECT COUNT(*) AS n FROM conteos')[0]['n'])
        self.assertEqual(reader.get('/expedientes/{}/'.format(work)).status_code, 200)
        self.assertEqual(reader.post('/expedientes/{}/accion/count/'.format(work), {'cantidad': 8}).status_code, 403)
        self.ticket('/expedientes/{}/accion/count/'.format(work))
        self.assertEqual(self.call(lambda s: s.rows('SELECT COUNT(*) AS n FROM conteos')[0]['n']), before)

    def test_action_token_bound_to_user_and_operation(self):
        ticket = self.ticket('/accion/folio/')
        self.assertEqual(self.client.post('/accion/catalog/', {'ticket': ticket}).status_code, 403)
        self.assertEqual(self.client.post('/accion/folio/', {'ticket': 'inventado'}).status_code, 403)

    def test_duplicate_post_creates_one_folio(self):
        url = '/accion/folio/'
        data = {'ticket': self.ticket(url), 'numero': 'DOBLE-CLIC-FICTICIO', 'motivo': 'Prueba doble clic'}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(self.call(lambda s: len(s.rows('SELECT * FROM folios WHERE numero=?', (data['numero'],)))), 1)

    def test_ledger_serializes_concurrent_requests_and_preserves_incomplete(self):
        key = 'ticket-paralelo-' + uuid.uuid4().hex
        ids = []; errors = []
        def operation(store): return {'id': store.save_folio('PARALELO-' + key, '')}
        def worker():
            try: ids.append(self.call(operation, key)['id'])
            except Exception as e: errors.append(str(e))
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(errors, []); self.assertEqual(len(set(ids)), 1)
        def interrupted(store):
            store.save_folio('INTERRUMPIDO-' + key, '')
            raise OSError('Corte ficticio después de confirmar')
        with self.assertRaises(OSError): self.call(interrupted, key + '-corte')
        with self.assertRaises(ValueError): self.call(interrupted, key + '-corte')
        self.assertEqual(self.call(lambda s: len(s.rows('SELECT id FROM folios WHERE numero=?', ('INTERRUMPIDO-' + key,)))), 1)

    def test_workspace_lock_blocks_desktop_and_real_workspace(self):
        from app.core import Store
        from iniciar_web import checked_workspace
        with self.assertRaises(ValueError): Store(workspace=self.root)
        with self.assertRaises(ValueError): checked_workspace('C:/Digitalizacion')

    def test_html_escapes_names_and_filters_do_not_read_images(self):
        folio = self.call(lambda s: s.save_folio('XSS-FICTICIO', ''))
        self.call(lambda s: s.save_work(folio, 'XXXX900101HYNBBB09', '<script>window.inventado=1</script>', 1))
        from app.coding import page_info
        with patch('app.coding.page_info', side_effect=AssertionError('Búsqueda no debe leer TIFF')):
            response = self.client.get('/expedientes/', {'q': 'XXXX'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'&lt;script&gt;', response.content)
        self.assertNotIn(b'<script>window.inventado', response.content)
        self.assertNotIn(b'<html', response.content)

    def test_foreign_file_and_delivery_rejected(self):
        works, files, deliveries = self.call(lambda s: (s.works(), s.rows('SELECT * FROM archivos_tiff'), s.rows('SELECT * FROM entregas')))
        foreign = next(w['id'] for w in works if w['id'] != files[0]['trabajo_id'])
        self.assertEqual(self.client.get('/expedientes/{}/imagen/{}/1/'.format(foreign, files[0]['id'])).status_code, 404)
        from webapp.domain import act
        with self.assertRaises(ValueError): self.call(lambda s: act(s, 'Administrador', 'code', foreign, {'archivo': files[0]['id'], 'codigo': 'DP-01', 'motivo': 'Prueba'}))
        d = deliveries[0]
        foreign = next(w['id'] for w in works if w['id'] != d['trabajo_id'])
        self.assertEqual(self.client.get('/expedientes/{}/entrega/{}/'.format(foreign, d['id'])).status_code, 409)

    def test_import_preview_commit_and_repeated_commit(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        upload = SimpleUploadedFile('lista.csv', b'CURP;Nombre completo;Folio;Legajo\nAAAA900101HYNBBB01;Persona ficticia;LISTA-WEB;3\n', content_type='text/csv')
        result = self.client.post('/importar-lista/', {'archivo': upload, 'folio': '', 'legajo': ''})
        self.assertEqual(result.status_code, 302, result.content[-3000:])
        preview = self.client.get('/importar-lista/vista-previa/')
        self.assertEqual(preview.status_code, 200)
        token = self.client.session['plan_actual']
        data = {'plan': token, 'paso': 'confirmar', 'confirmado': 'on'}
        self.assertEqual(self.client.post('/importar-lista/', data).status_code, 302)
        self.assertEqual(self.client.post('/importar-lista/', data).status_code, 302)
        self.assertEqual(self.call(lambda s: len(s.rows("SELECT * FROM folios WHERE numero='LISTA-WEB'"))), 1)
        self.assertEqual(self.call(lambda s: s.rows("SELECT i.validacion FROM prestamo_items i JOIN folios f ON f.id=i.folio_id WHERE f.numero='LISTA-WEB'")[0]['validacion']), 'Pendiente')

    def test_operational_cycle_delivery_integration_and_historical_images(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        from app.core import STATES
        self.post('folio', {'numero': 'FLUJO-WEB', 'fecha': '2026-10-05'})
        f = self.call(lambda s: s.rows("SELECT id FROM folios WHERE numero='FLUJO-WEB'")[0]['id'])
        self.post('expected', {'folio': f, 'curp': 'AAAB900101HYNBBB02', 'nombre': 'Persona ficticia WEB', 'legajo': 1})
        item = self.call(lambda s: s.rows('SELECT id FROM prestamo_items WHERE folio_id=?', (f,))[0]['id'])
        self.post('accept', {'folio': f, 'seleccion': [item], 'confirmado': 'on'})
        work = self.call(lambda s: s.rows('SELECT id FROM trabajos WHERE folio_id=?', (f,))[0]['id'])
        self.post('assign', {'persona': 'Digitalizador ficticio', 'rol': 'Digitalizador'}, work)
        self.post('count', {'cantidad': 1}, work); self.post('confirm_count', {'confirmado': 'on'}, work)
        def upload(color):
            data = io.BytesIO(); Image.new('RGB', (24, 32), color).save(data, format='TIFF')
            self.post('upload', {'archivos': SimpleUploadedFile('escaneo.tif', data.getvalue())}, work)
            return self.call(lambda s: s.rows('SELECT id FROM archivos_tiff WHERE trabajo_id=? ORDER BY id DESC', (work,))[0]['id'])
        file_id = upload('white'); self.post('code', {'archivo': file_id, 'codigo': 'DP-01'}, work)
        for state in STATES[1:8]: self.post('state', {'estado': state}, work)
        self.post('deliver', {'confirmado': 'on'}, work)
        first = self.call(lambda s: s.rows('SELECT * FROM entregas WHERE trabajo_id=? ORDER BY numero', (work,))[0])
        self.post('begin_review', {'entrega': first['id']}, work); self.post('approve', {'entrega': first['id'], 'confirmado': 'on'}, work)
        self.post('integration', {'folio': f, 'fecha': '2026-10-05', 'acuse': 'ACUSE FICTICIO NUEVO', 'persona': 'Digitalizador ficticio', 'confirmado': 'on'}, work)
        self.post('count', {'cantidad': 2}, work); self.post('confirm_count', {'confirmado': 'on'}, work)
        self.post('catalog', {'codigo': 'DP-02', 'carpeta': 'PERSONALES', 'titulo': 'Documento ficticio adicional'})
        second_file = upload('gray'); self.post('code', {'archivo': second_file, 'codigo': 'DP-02'}, work)
        for state in STATES[1:8]: self.post('state', {'estado': state}, work)
        self.post('deliver', {'confirmado': 'on'}, work)
        def check(store):
            from app.delivery import Deliveries
            from app.integrations import Integrations
            rows = store.rows('SELECT * FROM entregas WHERE trabajo_id=? ORDER BY numero', (work,))
            return rows, Deliveries(store).verify(rows[-1]['id']), Integrations(store).totals(work)
        deliveries, manifest, totals = self.call(check)
        self.assertEqual(len(deliveries), 2); self.assertEqual(deliveries[0]['manifest_hash'], first['manifest_hash'])
        self.assertEqual(totals['hojas_confirmadas'], 3); self.assertEqual(totals['tiff'], 2)
        self.assertEqual(len(manifest['items']), 2); self.assertEqual(len(manifest['integraciones']), 2)
        for delivery in deliveries:
            self.assertEqual(self.client.get('/expedientes/{}/entrega/{}/'.format(work, delivery['id'])).status_code, 200)
        frozen = self.client.get('/expedientes/{}/entrega/{}/imagen/{}/1/'.format(work, first['id'], file_id))
        self.assertEqual(frozen.status_code, 200); self.assertEqual(frozen['Content-Type'], 'image/png')
        with self.assertRaises(ValueError):
            self.call(lambda s: __import__('app.review', fromlist=['Reviews']).Reviews(s).begin(first['id']))

    def test_bi_csv_units_and_formula_escape(self):
        from webapp.views import safe_csv
        self.assertEqual(safe_csv('=1+1'), "'=1+1")
        self.assertEqual(safe_csv('  @SUM(A1)'), "'  @SUM(A1)")
        response = self.client.get('/indicadores/', {'exportar': 'csv', 'folio': 'FOLIO-QUE-NO-EXISTE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.content.decode('utf-8-sig').splitlines()), 1)

    def test_tiff_batch_and_backup_verified(self):
        from webapp.domain import act
        from webapp.backup import verify_web_backup, restore_web_backup
        from app.backup import sha256
        import sqlite3
        work = self.call(lambda s: next(w['id'] for w in s.works() if w['estado'] != 'Expediente cerrado' and w['total_tiff']))
        ident = self.call(lambda s: s.rows('SELECT id FROM archivos_tiff WHERE trabajo_id=? AND activo=1', (work,))[0]['id'])
        data = {'seleccion': [ident], 'tipo': 'retirar', 'motivo': 'Retiro ficticio de prueba'}
        self.call(lambda s: act(s, 'Administrador', 'batch', work, data))
        self.assertEqual(self.call(lambda s: s.rows('SELECT activo FROM archivos_tiff WHERE id=?', (ident,))[0]['activo']), 0)
        data['tipo'] = 'recuperar'; self.call(lambda s: act(s, 'Administrador', 'batch', work, data))
        self.assertEqual(self.call(lambda s: s.rows('SELECT activo FROM archivos_tiff WHERE id=?', (ident,))[0]['activo']), 1)
        self.call(lambda s: act(s, 'Administrador', 'backup', 0, {'motivo': 'Respaldo ficticio de prueba'}))
        backups = list((self.root / 'respaldos').glob('web-*')); self.assertTrue(backups)
        backup = backups[-1]
        manifest = verify_web_backup(backup)
        self.assertEqual(manifest['runtime']['python'], '3.14.8')
        self.assertIn('webapp/engine.py', manifest['runtime']['code'])
        exact = self.call(lambda s: s.rows('SELECT * FROM trabajos ORDER BY id'))
        original = sqlite3.connect(str(backup / 'privado' / 'origen.sqlite3'))
        original.row_factory = sqlite3.Row
        try:
            self.assertEqual([dict(r) for r in original.execute('SELECT * FROM trabajos ORDER BY id')], exact)
        finally: original.close()
        restored = restore_web_backup(backup, self.root.parent / ('restaurado-' + uuid.uuid4().hex))
        from iniciar_web import checked_workspace
        self.assertEqual(checked_workspace(restored), restored)
        auth = sqlite3.connect(str(restored / '.web' / 'acceso.sqlite3'))
        try:
            self.assertEqual(auth.execute('SELECT password FROM auth_user WHERE username=?', (self.user.username,)).fetchone()[0], self.user.password)
            self.assertEqual(auth.execute('SELECT COUNT(*) FROM django_session').fetchone()[0], 0)
            self.assertTrue(auth.execute('SELECT COUNT(*) FROM auth_user_groups').fetchone()[0])
        finally: auth.close()
        self.assertEqual(sha256(restored / '.web' / 'solicitudes.sqlite3'), manifest['private']['solicitudes.sqlite3'])
        self.assertEqual(sha256(restored / '.web' / 'origen.sqlite3'), manifest['private']['origen.sqlite3'])
        self.assertFalse((restored / '.restauracion_web_incompleta').exists())
        with self.assertRaises(FileExistsError): restore_web_backup(backup, restored)
        config = backup / 'privado' / 'config.json'
        before = config.read_bytes()
        config.write_bytes(before + b' ')
        with self.assertRaises(ValueError): verify_web_backup(backup)
        config.write_bytes(before)
        extra = backup / 'privado' / 'archivo-no-previsto.txt'
        extra.write_text('Contenido ficticio', encoding='utf-8')
        with self.assertRaises(ValueError): verify_web_backup(backup)
        extra.unlink()
        incomplete = backup / 'INCOMPLETO.txt'
        incomplete.write_text('Fallo ficticio', encoding='utf-8')
        with self.assertRaises(ValueError): verify_web_backup(backup)

    def test_uploaded_names_are_preserved_and_count_requires_positive(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        from webapp.forms import action_form
        work = self.call(lambda s: next(w['id'] for w in s.works() if w['estado'] != 'Expediente cerrado'))
        blob = io.BytesIO()
        with Image.new('RGB', (31, 43), '#1a3347') as img: img.save(blob, format='TIFF')
        self.post('upload', {'archivos': SimpleUploadedFile('origen_ficticio_cotejado.tif', blob.getvalue())}, work)
        row = self.call(lambda s: s.rows('SELECT * FROM archivos_tiff WHERE trabajo_id=? ORDER BY id DESC', (work,))[0])
        self.assertTrue(Path(row['ruta']).name.endswith('_origen_ficticio_cotejado.tif'))
        self.assertFalse(list((self.root / '.web' / 'incoming').glob('*/origen_ficticio_cotejado.tif')))
        self.assertFalse(action_form('count', {}, {'cantidad': 0, 'motivo': 'Ficticio'}).is_valid())
