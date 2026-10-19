"""Formularios nativos: origen, cookie y token comprobados por Django real."""
import html
import re
import unittest
from django.test import Client
from webtests import test_web as support


class CsrfTests(unittest.TestCase):
    # Reutiliza solo la preparación aislada de usuarios/motor de WebTests.
    @classmethod
    def setUpClass(cls):
        support.WebTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        support.WebTests.tearDownClass.__func__(cls)

    def call(self, function):
        return self.engine.call('Operador ficticio CSRF', function)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.host = '127.0.0.1:8765'
        self.origin = 'http://' + self.host

    def page(self, path='/acceso/'):
        return self.client.get(path, HTTP_HOST=self.host)

    def token(self, response):
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
        self.assertIsNotNone(match)
        return html.unescape(match.group(1))

    def login_data(self, token):
        return {'usuario': 'operador_ficticio', 'clave': 'ClaveFicticiaWeb_2026!', 'csrfmiddlewaretoken': token}

    def test_browser_form_policy_preserves_own_origin_and_login(self):
        page = self.page()
        self.assertEqual(page['Referrer-Policy'], 'same-origin')
        self.assertIn('no-store', page['Cache-Control'])
        # El estándar Fetch serializa el origen como null para un POST nativo
        # con no-referrer. No es una prueba visual ni ejecución de navegador.
        browser_origin = 'null' if page['Referrer-Policy'] == 'no-referrer' else self.origin
        response = self.client.post('/acceso/', self.login_data(self.token(page)), HTTP_HOST=self.host, HTTP_ORIGIN=browser_origin)
        self.assertEqual(response.status_code, 302)
        home = self.page('/')
        self.assertEqual(home.status_code, 200)
        self.assertNotIn('name="referrer" content="no-referrer"', home.content.decode())
        self.assertEqual(home['Referrer-Policy'], 'same-origin')
        logout = self.client.post('/salir/', {'csrfmiddlewaretoken': self.token(home)}, HTTP_HOST=self.host, HTTP_ORIGIN=self.origin)
        self.assertEqual(logout.status_code, 302)

    def test_null_and_foreign_origins_still_rejected_with_valid_cookie_and_token(self):
        for origin in ('null', 'https://sitio-ficticio.invalid', 'http://127.0.0.1:8766'):
            with self.subTest(origin=origin):
                page = self.page()
                response = self.client.post('/acceso/', self.login_data(self.token(page)), HTTP_HOST=self.host, HTTP_ORIGIN=origin)
                self.assertEqual(response.status_code, 403)
                self.assertIn('Volver a abrir el acceso', response.content.decode())
                self.assertNotIn(origin, response.content.decode())
                self.assertNotIn('DEBUG=True', response.content.decode())
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_missing_cookie_and_stale_token_have_safe_recovery(self):
        token = self.token(self.page())
        self.client.cookies.clear()
        response = self.client.post('/acceso/', self.login_data(token), HTTP_HOST=self.host, HTTP_ORIGIN=self.origin)
        self.assertEqual(response.status_code, 403)
        self.assertIn('cookie', response.content.decode())
        fresh = self.token(self.page())
        self.assertEqual(self.client.post('/acceso/', self.login_data(fresh), HTTP_HOST=self.host, HTTP_ORIGIN=self.origin).status_code, 302)
        # Iniciar sesión rota el token; una pestaña anterior debe seguir rechazada.
        stale = self.client.post('/salir/', {'csrfmiddlewaretoken': fresh}, HTTP_HOST=self.host, HTTP_ORIGIN=self.origin)
        self.assertEqual(stale.status_code, 403)
        self.assertIn('Volver al sistema', stale.content.decode())
        current = self.token(self.page('/'))
        self.assertEqual(self.client.post('/salir/', {'csrfmiddlewaretoken': current}, HTTP_HOST=self.host, HTTP_ORIGIN=self.origin).status_code, 302)

    def test_fresh_native_post_reaches_business_view_without_csrf_bypass(self):
        login_page = self.page()
        self.assertEqual(self.client.post('/acceso/', self.login_data(self.token(login_page)), HTTP_HOST=self.host, HTTP_ORIGIN=self.origin).status_code, 302)
        page = self.page('/accion/folio/')
        ticket = html.unescape(re.search(r'name="ticket" value="([^"]+)"', page.content.decode()).group(1))
        response = self.client.post('/accion/folio/', {'csrfmiddlewaretoken': self.token(page), 'ticket': ticket,
            'numero': 'FOLIO-CSRF-FICTICIO', 'motivo': 'Comprobación ficticia de formulario'}, HTTP_HOST=self.host, HTTP_ORIGIN=self.origin)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.call(lambda s: len(s.rows("SELECT id FROM folios WHERE numero='FOLIO-CSRF-FICTICIO'"))), 1)

    def test_waitress_http_form_post_with_origin_and_recovery(self):
        import http.cookiejar
        import threading
        from urllib.error import HTTPError
        from urllib.parse import urlencode
        from urllib.request import build_opener, HTTPCookieProcessor, Request
        from iniciar_web import application
        from waitress import create_server
        server = create_server(application(), host='127.0.0.1', port=0, threads=2, asyncore_loop_timeout=0.1)
        closing=threading.Event();errors=[]
        def run():
            try:server.run()
            except OSError as error:
                if not (closing.is_set() and getattr(error,'winerror',None)==10038):errors.append(error)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        origin = 'http://127.0.0.1:' + str(server.effective_port)
        opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        try:
            with opener.open(origin + '/acceso/?next=/', timeout=15) as response:
                content = response.read().decode()
                self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')
            token = html.unescape(re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content).group(1))
            payload = urlencode(self.login_data(token)).encode()
            with self.assertRaises(HTTPError) as rejected:
                opener.open(Request(origin + '/acceso/', data=payload, headers={'Origin': 'null'}), timeout=15)
            try:
                self.assertEqual(rejected.exception.code, 403)
                self.assertIn('Volver a abrir el acceso', rejected.exception.read().decode())
            finally: rejected.exception.close()
            with opener.open(Request(origin + '/acceso/', data=payload, headers={'Origin': origin, 'Referer': origin + '/acceso/'}), timeout=15) as response:
                self.assertEqual(response.geturl(), origin + '/')
                content = response.read().decode()
                self.assertIn('Mi jornada', content)
                self.assertIn('name="referrer" content="same-origin"', content)
            fresh = html.unescape(re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content).group(1))
            with opener.open(Request(origin + '/salir/', data=urlencode({'csrfmiddlewaretoken': fresh}).encode(), headers={'Origin': origin}), timeout=15) as response:
                self.assertEqual(response.geturl(), origin + '/acceso/')
        finally:
            closing.set()
            server.task_dispatcher.shutdown()
            server.close()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors,[])
