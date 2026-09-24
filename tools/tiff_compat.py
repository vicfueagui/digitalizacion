"""Corpus sintético entre runtimes: píxeles/metadata y bytes son evidencias distintas."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from PIL import Image,TiffImagePlugin
from app.backup import sha256
from app.coding import stream_edit,page_info
from app.integrity import runtime_info
from app.update_recovery import write_json


def content(path):
    rows=[]
    with Image.open(str(path)) as im:
        for page in range(getattr(im,'n_frames',1)):
            im.seek(page);im.load()
            rows.append({'modo':im.mode,'tamano':list(im.size),'pixeles':hashlib.sha256(im.tobytes()).hexdigest(),
                         'dpi':[round(float(v),6) for v in im.info.get('dpi',())],
                         'compresion':im.info.get('compression'),'descripcion':str(im.tag_v2.get(270,''))})
    return rows


def create(destination):
    destination.mkdir(parents=True,exist_ok=False)
    images=[]
    try:
        for mode in ('1','L','RGB'):
            im=Image.new(mode,(37,61))
            for y in range(61):
                for x in range(37):
                    value=(x*7+y*11)%256
                    im.putpixel((x,y), (value,255-value,(x+y)%256) if mode=='RGB' else (255 if value>127 else 0) if mode=='1' else value)
            images.append(im)
        tags=TiffImagePlugin.ImageFileDirectory_v2();tags[270]='CORPUS FICTICIO'
        images[0].save(str(destination/'multipagina.tif'),save_all=True,append_images=images[1:],compression='tiff_deflate',dpi=(200,200),tiffinfo=tags)
        images[2].save(str(destination/'individual.tif'),compression='tiff_deflate',dpi=(300,300),tiffinfo=tags)
    finally:
        for im in images:im.close()
    cases=[]
    for source,page,ops in [('individual.tif',0,[('rotate',-90)]),('multipagina.tif',1,[('rotate',-90)]),
                            ('multipagina.tif',2,[('crop',2,3,31,50)]),('individual.tif',0,[('rotate',.2)])]:
        name='esperado-'+str(len(cases))+'.tif';stream_edit(destination/source,destination/name,page,ops)
        cases.append({'source':source,'source_sha256':sha256(destination/source),'pagina':page,'ops':ops,'esperado':name,
                      'sha256':sha256(destination/name),'contenido':content(destination/name)})
    report={'entorno':runtime_info(),'casos':cases};write_json(destination/'referencia.json',report);return report


def compare(source,destination):
    source=source.resolve();destination.mkdir(parents=True,exist_ok=False)
    baseline=json.loads((source/'referencia.json').read_text(encoding='utf-8'));results=[]
    for case in baseline['casos']:
        from app.manifests import plain_path
        original=plain_path(source,case['source']);expected=plain_path(source,case['esperado'])
        if sha256(original)!=case['source_sha256'] or sha256(expected)!=case['sha256']:raise ValueError('El corpus de referencia fue alterado.')
        out=plain_path(destination,case['esperado']);stream_edit(original,out,case['pagina'],case['ops'])
        results.append({'caso':case['esperado'],'bytes_iguales':sha256(out)==case['sha256'],
                        'pixeles_paginas_metadata_iguales':content(out)==case['contenido']})
    report={'origen':baseline['entorno'],'destino':runtime_info(),'casos':results,
            'bytes_iguales':all(r['bytes_iguales'] for r in results),
            'contenido_igual':all(r['pixeles_paginas_metadata_iguales'] for r in results),
            'alcance':'Corpus sintético limitado; no certifica reconstrucción de todos los TIFF históricos.'}
    write_json(destination/'comparacion.json',report);return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--crear');parser.add_argument('--comparar');parser.add_argument('--salida')
    args=parser.parse_args()
    if args.crear and not args.comparar:result=create(Path(args.crear).resolve())
    elif args.comparar and args.salida and not args.crear:result=compare(Path(args.comparar),Path(args.salida).resolve())
    else:parser.error('Usa --crear CARPETA_NUEVA o --comparar CORPUS --salida CARPETA_NUEVA')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('bytes_iguales',True) and result.get('contenido_igual',True) else 2


if __name__=='__main__':sys.exit(main())
