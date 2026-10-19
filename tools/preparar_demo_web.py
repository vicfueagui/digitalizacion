"""Crea exclusivamente una demostración nueva; nunca reutiliza datos existentes."""
from pathlib import Path
import sys

CODE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE))


def main():
    root = CODE.parent / 'demo-web'
    if root.exists():
        raise ValueError('La demostración ya existe. No se sobrescribe ni reinicia.')
    from app.demo import create_demo
    from iniciar_web import configure, checked_workspace
    create_demo(root)
    configure(checked_workspace(root))
    from django.contrib.auth.models import User
    User.objects.create_superuser('operador_ficticio', password='ClaveFicticiaWeb_2026!')
    print('Demostración ficticia creada. Usuario: operador_ficticio')
    print('Clave exclusiva de esta demostración: ClaveFicticiaWeb_2026!')


if __name__ == '__main__':
    main()
