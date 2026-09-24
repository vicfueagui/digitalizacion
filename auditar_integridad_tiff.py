"""Auditoría completa; reconstrucción opcional solo a candidato externo exacto."""
import argparse
import sys
from pathlib import Path
from app.workspace import Workspace
from app.integrity import diagnose,save_report
from app.tiff_recovery import reconstruct_candidate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True)
    parser.add_argument('--salida',required=True)
    parser.add_argument('--archivo',type=int)
    parser.add_argument('--revision',type=int)
    parser.add_argument('--operacion',type=int)
    args=parser.parse_args();ws=Workspace(args.workspace);out=Path(args.salida).resolve()
    if ws.root==out or ws.root in out.parents:parser.error('Usa una salida fuera del workspace.')
    supplied=[args.archivo is not None,args.revision is not None,args.operacion is not None]
    if any(supplied):
        if not all(supplied):parser.error('Reconstruir requiere archivo, revisión y operación explícitos.')
        result=reconstruct_candidate(ws,args.archivo,args.revision,args.operacion,out)
        print(result['resultado']);print('SHA-256:',result['sha256']);return 0
    result=diagnose(ws);save_report(result,out)
    print('AUDITORIA '+('CORRECTA' if result['correcto'] else 'CON PROBLEMAS')+'; informe local: '+str(out))
    return 0 if result['correcto'] else 1


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as error:print('Auditoría detenida:',error,file=sys.stderr);sys.exit(1)
