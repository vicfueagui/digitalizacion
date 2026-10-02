"""Acceso de revisión: exige el marcador de demostración, sin ruta por defecto."""
import argparse
import json
from pathlib import Path
import sys

CODE=Path(__file__).resolve().parent.parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(CODE))


def main():
    parser=argparse.ArgumentParser(description='Abrir únicamente una demostración ficticia')
    parser.add_argument('--workspace',required=True)
    args=parser.parse_args();root=Path(args.workspace).resolve()
    marker=root/'DEMO.json'
    if not marker.is_file() or json.loads(marker.read_text(encoding='utf-8')).get('demo') is not True:
        parser.error('La carpeta no tiene el marcador de demostración ficticia. No se abrió la base.')
    if not (root/'datos/digitalizacion.sqlite3').is_file():parser.error('La demo no contiene su base; no se crea otra.')
    from app.core import Store
    from app.ui import App
    store=Store(workspace=root,operador='Responsable ficticio de revisión')
    try:
        app=App(store);app.title('CANDIDATO 0.7.0 · SOLO DATOS FICTICIOS');app.mainloop()
    finally:store.db.close()


if __name__=='__main__':main()
