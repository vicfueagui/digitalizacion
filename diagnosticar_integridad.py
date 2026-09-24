"""Inventario local legible/JSON, siempre de lectura sobre los datos originales."""
import argparse
import sys
from pathlib import Path
from app.integrity import diagnose,save_report
from app.workspace import Workspace


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True)
    parser.add_argument('--codigo',help='Carpeta del programa que funciona en origen')
    parser.add_argument('--salida',required=True,help='Carpeta NUEVA y externa para los informes locales')
    args=parser.parse_args()
    workspace=Workspace(args.workspace);destination=Path(args.salida).resolve()
    if destination==workspace.root or workspace.root in destination.parents:
        parser.error('Guarda el diagnóstico fuera del workspace que se revisa.')
    result=diagnose(workspace,args.codigo)
    save_report(result,destination)
    print('DIAGNOSTICO '+('CORRECTO' if result['correcto'] else 'CON PROBLEMAS'))
    print('Referencias correctas: {} / {}'.format(result['tiff']['correctas'],result['tiff']['referencias']))
    print('Informe local:',destination)
    return 0 if result['correcto'] else 1


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as error:print('Diagnóstico detenido:',error,file=sys.stderr);sys.exit(1)
