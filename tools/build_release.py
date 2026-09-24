"""Generar actualización de código sin bases, TIFF, configuración local ni .venv."""
import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.backup import sha256
from app.release import allowed
from app import VERSION
from app.manifests import checked_files


def build(destination):
    from tools.build_docs import build as build_docs
    build_docs()
    candidates = list(ROOT.iterdir())
    for folder in ('app','tests','tools','docs','instaladores'):
        candidates.extend((ROOT/folder).iterdir())
    paths = sorted(p for p in candidates if p.is_file() and not p.is_symlink()
                   and allowed(p.relative_to(ROOT).as_posix()))
    manifest = {'format': 1, 'version': VERSION, 'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths}}
    checked_files(manifest['files'], allowed)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(destination), 'w', zipfile.ZIP_DEFLATED) as z:
        for path in paths:
            z.write(str(path), path.relative_to(ROOT).as_posix())
        z.writestr('release-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    destination.with_suffix('.sha256').write_text(sha256(destination)+'  '+destination.name+'\n', encoding='ascii')
    print(destination, '|', len(paths), 'archivos de código/documentación/instalación; sin datos')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--salida', default=str(ROOT/'dist'/('Digitalizacion-'+VERSION+'-codigo.zip')))
    build(Path(parser.parse_args().salida).resolve())
