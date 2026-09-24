"""Punto común de selección para BAT/PowerShell y asistentes Python."""
import argparse
import json
from pathlib import Path
import sys
from app.runtime import probe,resolve


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz',default=str(Path(__file__).resolve().parent))
    parser.add_argument('--perfil',choices=('legado','instalar','laboratorio'),default='legado')
    parser.add_argument('--python')
    parser.add_argument('--seleccionar',action='store_true')
    args=parser.parse_args()
    if args.seleccionar:
        chosen,info,rejected=resolve(args.raiz,args.python,args.perfil)
        for row in rejected:print('Descartado: '+row['candidato']+' / '+row['motivo'],file=sys.stderr)
        # Única línea stdout, consumida como ruta literal; jamás se evalúa como código.
        print(str(chosen));return 0
    print(json.dumps(probe(args.python or sys.executable,args.perfil),ensure_ascii=False,indent=2));return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as error:print(error,file=sys.stderr);sys.exit(70)
