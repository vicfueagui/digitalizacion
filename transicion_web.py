"""Se ejecuta explícitamente con la aplicación y escrituras externas detenidas."""
import argparse
from pathlib import Path
import sys
from webapp.transition import prepare, activate


def main():
    parser = argparse.ArgumentParser(description='Transición privada a Digitalización web')
    sub = parser.add_subparsers(dest='action', required=True)
    ready = sub.add_parser('preparar')
    ready.add_argument('--destino', required=True)
    ready.add_argument('--resguardo', required=True)
    ready.add_argument('--confirmar-pausa', action='store_true', required=True)
    apply = sub.add_parser('activar')
    apply.add_argument('--resguardo', required=True)
    apply.add_argument('--confirmar-pausa', action='store_true', required=True)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14): raise ValueError('Requiere el entorno Python 3.14 verificado.')
    if args.action == 'preparar':
        plan = prepare(Path(__file__).resolve().parent, args.destino, args.resguardo)
        print('Copia validada. La instalación diaria sigue intacta. TIFF:', plan['copy_validation']['tiff_decoded'])
    else:
        activate(args.resguardo)
        print('Acceso web activado. Abre INICIAR.bat y crea tu cuenta personal cuando se solicite.')


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError) as error:
        print('Transición detenida: ' + str(error)); sys.exit(1)
