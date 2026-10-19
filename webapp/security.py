"""La candidata solo admite loopback. Ningún archivo privado se sirve como estático."""
import ipaddress
import time
import threading
from django.http import HttpResponseForbidden
from django.shortcuts import render


def csrf_failure(request, reason=''):
    """Rechazar el POST y ofrecer un GET nuevo; nunca repetir credenciales/acciones."""
    if reason == 'CSRF cookie not set.':
        explanation = 'El navegador no envió la cookie necesaria. Abre nuevamente el acceso y permite las cookies de esta aplicación local.'
    elif reason.startswith(('Origin checking failed', 'Referer checking failed')):
        explanation = 'El origen del formulario no pudo comprobarse. Abre nuevamente el acceso desde la dirección local de esta aplicación.'
    else:
        explanation = 'El formulario ya no coincide con tu sesión. Puede ocurrir al iniciar sesión en otra pestaña o volver a una página anterior.'
    authenticated = bool(getattr(request, 'user', None) and request.user.is_authenticated)
    return render(request, 'csrf_failure.html', {
        'explanation': explanation,
        'return_url': '/' if authenticated else '/acceso/',
        'return_label': 'Volver al sistema' if authenticated else 'Volver a abrir el acceso',
    }, status=403)


class LocalOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            allowed = ipaddress.ip_address(request.META.get('REMOTE_ADDR', '')).is_loopback
        except ValueError:
            allowed = False
        if not allowed:
            return HttpResponseForbidden('Esta instalación solo admite acceso desde el equipo local.')
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store, private'
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response


_login_lock = threading.Lock()
_failures = []


def login_limit(failed=False):
    with _login_lock:
        now = time.monotonic()
        _failures[:] = [stamp for stamp in _failures if now - stamp < 300]
        if failed:
            _failures.append(now)
        return len(_failures) >= 8
