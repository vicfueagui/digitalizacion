"""Recepción de bytes del navegador, prevalidación y confirmación por cuenta."""
import json
import math
import os
import uuid
from pathlib import Path,PureWindowsPath
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from app.coding import CodingService,page_info,digest
from app.integrations import Integrations
from .views import call,authorize
from .desk_views import payload


def clear_staged(folder,entries):
    """Retirar solo los bytes temporales listados bajo esta carpeta aleatoria."""
    root=folder.resolve()
    for entry in entries:
        path=(folder/entry['relative']).resolve()
        if root not in path.parents or path.parent.parent!=root:raise ValueError('Ruta temporal fuera del lote.')
        path.unlink(missing_ok=True)
        if path.parent.exists() and not any(path.parent.iterdir()):path.parent.rmdir()


@login_required
@require_POST
def stage(request,work):
    if not authorize(request,'upload'):return JsonResponse({'error':'Sin permiso de importación.'},status=403)
    try:
        files=request.FILES.getlist('files')
        if not files or len(files)>100 or sum(f.size for f in files)>200*1024*1024:
            raise ValueError('Selecciona hasta 100 TIFF y 200 MB por lote.')
        metadata=json.loads(request.POST.get('metadata','[]'))
        if not isinstance(metadata,list) or len(metadata)!=len(files) or not all(isinstance(m,dict) for m in metadata):raise ValueError('Metadatos incompletos.')
        folder=settings.WORKSPACE/'.web'/'incoming'/uuid.uuid4().hex;folder.mkdir()
        entries=[]
        for index,(upload,meta) in enumerate(zip(files,metadata)):
            name=PureWindowsPath(upload.name).name
            if Path(name).suffix.lower() not in ('.tif','.tiff') or name!=upload.name or any(c in name for c in '<>:"/\\|?*') or name.endswith((' ','.')) or PureWindowsPath(name).is_reserved():
                raise ValueError('Nombre TIFF no compatible con Windows.')
            sub=folder/str(index);sub.mkdir();dest=sub/name
            with dest.open('xb') as stream:
                for chunk in upload.chunks():stream.write(chunk)
            stamp=meta.get('modified')
            if stamp is not None:
                stamp=float(stamp)/1000
                if not math.isfinite(stamp) or not 0<=stamp<=32503680000:raise ValueError('Fecha de archivo inválida.')
                os.utime(dest,(stamp,stamp))
            try:
                pages=len(page_info(dest,True));sha=digest(dest);error=''
            except (ValueError,OSError,EOFError) as exc:pages=0;sha='';error='Contenido TIFF ilegible o fuera de límites.'
            entries.append(dict(name=name,relative=str(index)+'/'+name,pages=pages,sha=sha,bytes=dest.stat().st_size,error=error,modified=stamp))
        def check(store):
            coder=CodingService(store);coder.active_work(work)
            hashes={r['hash_original'] for r in store.rows('SELECT hash_original FROM archivos_tiff WHERE trabajo_id=?',(work,))}
            for entry in entries:
                entry['duplicate']=bool(entry['sha'] and entry['sha'] in hashes)
                if entry['sha']:hashes.add(entry['sha'])
            return Integrations(store).current(work)['id']
        integration=call(request,check)
        record=dict(user=request.user.pk,work=work,integration=integration,entries=entries,state='prepared')
        (folder/'manifest.json').write_text(json.dumps(record,ensure_ascii=False),encoding='utf8')
        token=signing.dumps([request.user.pk,work,folder.name],salt='import-preview')
        return JsonResponse(dict(token=token,entries=[{k:v for k,v in e.items() if k not in ('relative','sha')} for e in entries],integration=integration))
    except (ValueError,TypeError,OSError) as error:return JsonResponse({'error':str(error)},status=400)


@login_required
@require_POST
def confirm(request,work):
    if not authorize(request,'upload'):return JsonResponse({'error':'Sin permiso de importación.'},status=403)
    try:
        values=json.loads(request.body)
        if not isinstance(values,dict):raise ValueError('Confirmación inválida.')
        token=values.get('token','')
        identity=signing.loads(token,salt='import-preview',max_age=7200)
        if identity[:2]!=[request.user.pk,work] or len(identity[2])!=32:raise signing.BadSignature()
        folder=settings.WORKSPACE/'.web'/'incoming'/identity[2]
        record=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
        if values.get('confirmado')!='on':raise ValueError('Confirma los archivos y el destino revisados.')
        def execute(store):
            if Integrations(store).current(work)['id']!=record['integration']:raise ValueError('La integración cambió. Prepara otro lote.')
            if any(e['error'] for e in record['entries']):raise ValueError('Hay TIFF ilegibles. Corrige el lote antes de importar.')
            coder=CodingService(store);results=[];done=[];pending=[]
            entries=record['entries']
            # Comprobar todas las copias temporales antes de importar la primera.
            for e in entries:
                path=folder/e['relative']
                if digest(path)!=e['sha'] or len(page_info(path,True))!=e['pages']:raise ValueError('El lote cambió. Prepara otra vista previa.')
            for index,e in enumerate(entries):
                def metadata(ident):
                    # No se dispone de la fecha de creación original de Windows.
                    store.db.execute('UPDATE archivos_tiff SET fecha_origen=?,creacion_origen=0 WHERE id=?',(e['modified'] or 0,ident))
                result=coder.import_files(work,[folder/e['relative']],on_import=metadata)
                results.append(result)
                if result['errores']:pending=[x['name'] for x in entries[index:]];break
                done.append(e['name'])
            if not pending:clear_staged(folder,entries)
            return dict(message='Importación: {} nuevos; {} duplicados omitidos; {} pendientes.'.format(sum(r['importados'] for r in results),sum(r['duplicados'] for r in results),len(pending)),
                        completed=done,pending=pending,warning=bool(pending))
        result=call(request,execute,token)
        return JsonResponse(dict(result=result,state=payload(request,work)))
    except signing.BadSignature:return JsonResponse({'error':'Vista previa vencida o ajena.'},status=403)
    except (ValueError,TypeError,OSError) as error:return JsonResponse({'error':str(error)},status=409)


@login_required
@require_POST
def cancel(request,work):
    if not authorize(request,'upload'):return JsonResponse({'error':'Sin permiso de importación.'},status=403)
    try:
        token=json.loads(request.body).get('token','')
        identity=signing.loads(token,salt='import-preview',max_age=7200)
        if identity[:2]!=[request.user.pk,work]:raise signing.BadSignature()
        folder=settings.WORKSPACE/'.web'/'incoming'/identity[2]
        record=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
        def discard(store):
            clear_staged(folder,record['entries'])
            return dict(message='Importación cancelada. No se añadieron documentos.',completed=[],pending=[],warning=False)
        return JsonResponse(dict(result=call(request,discard,token)))
    except signing.BadSignature:return JsonResponse({'error':'Vista previa vencida o ajena.'},status=403)
    except (ValueError,TypeError,OSError) as error:return JsonResponse({'error':str(error)},status=409)
