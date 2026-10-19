"""Servidor local: demo explícita o instalación activada tras validar una copia."""
import argparse
import getpass
import json
import os
from pathlib import Path
import secrets
import sys

CODE = Path(__file__).resolve().parent


def checked_workspace(value, operational=False):
    requested = Path(value).absolute()
    for path in [requested] + list(requested.parents):
        stat = path.lstat()
        if path.is_symlink() or getattr(stat, 'st_file_attributes', 0) & 0x400:
            raise ValueError('No se admiten enlaces o junctions en el workspace.')
    root = requested.resolve()
    if (root / '.restauracion_web_incompleta').exists():
        raise ValueError('La restauración web está incompleta. No abrir esta copia.')
    # Hasta completar validación/aceptación y transición se bloquea operación real.
    if root == Path('C:/Digitalizacion').resolve() and not operational:
        raise ValueError('La candidata no se puede abrir sobre la instalación diaria.')
    for path in [root] + list(root.parents):
        stat = path.lstat()
        if path.is_symlink() or getattr(stat, 'st_file_attributes', 0) & 0x400:
            raise ValueError('No se admiten enlaces o junctions en el workspace.')
    if operational:
        from app.manifests import checked_files, plain_path
        from app.release import allowed
        from app.backup import sha256
        activation = json.loads(plain_path(root, '.web/activacion.json').read_text(encoding='utf-8'))
        if root != CODE or activation.get('format') != 'web-local-1' or Path(activation.get('workspace', '')).resolve() != root:
            raise ValueError('Falta activación de esta instalación y su copia validada.')
        for name, digest in checked_files(activation.get('files'), allowed).items():
            if sha256(plain_path(root, name)) != digest:
                raise ValueError('El código instalado cambió después de activar: ' + name)
    else:
        marker = root / 'DEMO.json'
        if not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')).get('demo') is not True:
            raise ValueError('La candidata solo admite una demostración ficticia identificada.')
    if not (root / 'datos' / 'digitalizacion.sqlite3').is_file():
        raise ValueError('Falta la base de demostración. No se creará una vacía por accidente.')
    return root


def configure(root, operational=False):
    private = root / '.web'
    for name in ('', 'tmp', 'incoming'):
        (private / name).mkdir(exist_ok=True)
    config = private / 'config.json'
    if not config.exists():
        with config.open('x', encoding='utf-8') as out:
            json.dump({'secret_key': secrets.token_urlsafe(64), 'demo': not operational or (root / 'DEMO.json').exists()}, out)
    os.environ['DIGITALIZACION_WEB_WORKSPACE'] = str(root)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'webapp.settings'
    import django
    django.setup()
    from django.core.management import call_command
    call_command('migrate', interactive=False, verbosity=0)


def application():
    from django.core.wsgi import get_wsgi_application
    from whitenoise import WhiteNoise
    return WhiteNoise(get_wsgi_application(), root=str(CODE / 'webapp' / 'static'), prefix='static/', max_age=0)


def main():
    parser = argparse.ArgumentParser(description='Digitalización web local · candidata con datos ficticios')
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--crear-demo', action='store_true')
    parser.add_argument('--crear-usuario', action='store_true')
    parser.add_argument('--sin-navegador', action='store_true')
    parser.add_argument('--operacion', action='store_true', help='Solo para una instalación activada tras validar su copia')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14): raise ValueError('Usa el entorno verificado Python 3.14 de esta candidata.')
    if not 1024 <= args.port <= 65535: raise ValueError('Puerto fuera del rango permitido.')
    if args.crear_demo and args.operacion: raise ValueError('Una demostración no es una activación operativa.')
    if args.crear_demo:
        if Path(args.workspace).exists(): raise ValueError('La nueva demostración requiere una carpeta inexistente.')
        from app.demo import create_demo
        create_demo(args.workspace)
    root = checked_workspace(args.workspace, operational=args.operacion)
    configure(root, operational=args.operacion)
    from django.contrib.auth.models import User, Group
    from app.operations import ROLES
    for name in ROLES: Group.objects.get_or_create(name=name)
    if args.crear_usuario or not User.objects.exists():
        user = input('Nombre de usuario nuevo: ').strip()
        password = getpass.getpass('Contraseña (mínimo 12 caracteres): ')
        if password != getpass.getpass('Repite la contraseña: ') or len(password) < 12:
            raise ValueError('La contraseña no coincide o es demasiado corta.')
        if not user or User.objects.filter(username=user).exists(): raise ValueError('Usuario vacío o ya existente.')
        if not User.objects.exists(): User.objects.create_superuser(user, password=password)
        else:
            print('Funciones: ' + ', '.join(ROLES))
            name = input('Función del usuario: ').strip()
            if name not in ROLES: raise ValueError('Función desconocida.')
            created = User.objects.create_user(user, password=password)
            created.groups.add(Group.objects.get(name=name))
    from webapp.engine import start, stop
    from waitress import create_server
    start(root)
    server = None
    try:
        server = create_server(application(), host='127.0.0.1', port=args.port, threads=4,
                               max_request_body_size=210 * 1024 * 1024, channel_timeout=1800, clear_untrusted_proxy_headers=True)
        from django.conf import settings
        print(('DEMOSTRACIÓN FICTICIA' if settings.CONFIG['demo'] else 'DIGITALIZACIÓN WEB') + ' · http://127.0.0.1:' + str(args.port))
        print('Cierra con Ctrl+C. No abras otra interfaz sobre este mismo workspace.')
        if not args.sin_navegador:
            import webbrowser
            webbrowser.open('http://127.0.0.1:' + str(args.port))
        server.run()
    finally:
        if server: server.close()
        stop()


if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: print('Servicio cerrado.')
    except Exception as error:
        print('No se inició: ' + str(error))
        sys.exit(1)
