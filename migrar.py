"""Asistente local o CLI para el traslado conservador, sin instalar en el origen."""
import argparse
import json
from pathlib import Path
import sys

from app.workspace import Workspace
from app.transfer import export_migration,verify_package,restore_migration,compare_source,verify_destination
from app.integrity import diagnose,save_report
from app.migration_acceptance import rehearse,activate,launch


def main(argv=None):
    parser=argparse.ArgumentParser(description='Migración verificable Windows 7 a Windows 10')
    parser.add_argument('--auditar',action='store_true')
    sub=parser.add_subparsers(dest='accion')
    p=sub.add_parser('exportar');p.add_argument('--workspace',required=True);p.add_argument('--codigo',required=True);p.add_argument('--destino',required=True)
    p.add_argument('--laboratorio',action='store_true');p.add_argument('--raiz-historica',action='append',default=[])
    for action in ('verificar-paquete','restaurar','comparar-origen'):
        p=sub.add_parser(action);p.add_argument('--paquete',required=True);p.add_argument('--sha256',required=True)
        if action=='restaurar':p.add_argument('--destino',required=True)
        if action=='comparar-origen':p.add_argument('--workspace',required=True)
    for action in ('verificar-destino','ensayar','activar','abrir'):
        p=sub.add_parser(action);p.add_argument('--instalacion',required=True)
        if action=='ensayar':p.add_argument('--python')
        if action=='activar':p.add_argument('--confirmo-origen-congelado-y-revision-visual',action='store_true')
    args=parser.parse_args(argv)
    if not args.accion:
        from app.migration_ui import run
        run(audit=args.auditar);return 0
    action=args.accion
    if action=='exportar':result=export_migration(Workspace(args.workspace),args.codigo,args.destino,historical_roots=args.raiz_historica,laboratory=args.laboratorio)
    elif action=='verificar-paquete':
        m=verify_package(args.paquete,args.sha256);result={'conclusion':'PAQUETE VERIFICADO','paquete_id':m['id'],'solo_laboratorio':m['solo_laboratorio']}
    elif action=='restaurar':result=restore_migration(args.paquete,args.destino,args.sha256)
    elif action=='comparar-origen':result=compare_source(args.paquete,Workspace(args.workspace),args.sha256)
    elif action=='verificar-destino':result=verify_destination(args.instalacion)
    elif action=='ensayar':result=rehearse(args.instalacion,args.python)
    elif action=='activar':result=activate(args.instalacion,args.confirmo_origen_congelado_y_revision_visual)
    else:return launch(args.instalacion)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result.get('diferencias') else 0


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError,KeyError) as error:
        print('MIGRACION NO VERIFICADA:',error,file=sys.stderr);sys.exit(1)
