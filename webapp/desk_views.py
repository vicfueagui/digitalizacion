import json
import uuid
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from . import desk, domain, preferences
from .views import call, role, authorize

ACTIONS = ('code','batch_code','batch','rename','edit','original','correction','pages','edit_pending','revision')


def tokens(request, work, integration):
    return {action:signing.dumps([request.user.pk,work,action,integration,uuid.uuid4().hex],salt='mesa')
            for action in ACTIONS if authorize(request,action)}


def payload(request, work):
    data = call(request, lambda s: desk.state(s,work))
    data['preferences'] = preferences.read(request.user)
    data['tokens'] = tokens(request,work,data['integration'])
    return data


@login_required
@require_GET
def station(request, work):
    try: data = payload(request,work)
    except ValueError: raise Http404('Expediente inexistente')
    return render(request,'coding_desk.html',dict(active='works',station=True,desk=data,context=data['context']))


@login_required
@require_POST
def preference(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data,dict): raise ValueError('Preferencia no válida.')
        codes = call(request, lambda s: {r['id'] for r in domain.CodingService(s).catalog()})
        return JsonResponse(preferences.update(request.user,data,codes))
    except (ValueError,TypeError): return JsonResponse({'error':'No se pudo guardar esa preferencia.'},status=400)


@login_required
@require_POST
def execute(request,work):
    try:
        data = json.loads(request.body)
        action = data.get('action')
        if action not in ACTIONS or not authorize(request,action): return JsonResponse({'error':'Tu perfil no permite esta acción.'},status=403)
        ticket = data.get('ticket','')
        identity = signing.loads(ticket,salt='mesa',max_age=7200)
        if identity[:3] != [request.user.pk,work,action]: raise signing.BadSignature()
    except (signing.BadSignature,ValueError,TypeError,AttributeError): return JsonResponse({'error':'Formulario vencido o ajeno. Vuelve a abrir la estación.'},status=403)
    try:
        values = data.get('data',{})
        if not isinstance(values,dict): raise ValueError('Datos no válidos.')
        ids = values.get('seleccion',[])
        if not isinstance(ids,list) or len(ids)>500: raise ValueError('Selecciona hasta 500 documentos por operación.')
        if action in ('batch_code','batch') and len(set(map(str,ids)))>1 and values.get('confirmado')!='on':
            raise ValueError('Confirma la operación y la cantidad de documentos.')
        if action=='original' and values.get('confirmado')!='on': raise ValueError('Confirma la restauración del original.')
        profile = role(request.user)
        def run(store):
            if domain.Integrations(store).current(work)['id'] != identity[3]: raise ValueError('Cambió la integración. Abre nuevamente la estación.')
            if action!='pages':
                expected=values.get('versions',{})
                targets=ids if action in ('batch','batch_code') else [values.get('archivo')]
                for ident in targets:
                    row=domain.CodingService(store).file(int(ident))
                    if row['trabajo_id']!=work: raise ValueError('Archivo ajeno al expediente.')
                    if expected.get(str(ident)) != [row['version_id'],row['hash_actual'],row['codigo'],row['activo']]:
                        raise ValueError('El documento cambió. Revisa el estado actualizado antes de confirmar.')
            return domain.act(store,profile,action,work,values)
        result = call(request,run,ticket)
        return JsonResponse(dict(result=result,state=payload(request,work)))
    except (ValueError,OSError,TypeError) as error:
        # No reintentar escrituras automáticamente: la solicitud queda en el diario.
        return JsonResponse({'error':str(error),'state':payload(request,work)},status=409)


@login_required
@require_GET
def preview(request,work,ident,page):
    try:
        thumb = request.GET.get('miniatura')=='1'
        revision = request.GET.get('revision')
        data = call(request,lambda s: desk.preview(s,work,ident,0 if thumb else page-1,
                    original=request.GET.get('original')=='1',thumbnail=thumb,revision=revision,full=request.GET.get('full')=='1'))
    except (ValueError,OSError,EOFError,IndexError): raise Http404('Página no disponible')
    return HttpResponse(data,content_type='image/png')


@login_required
@require_GET
def history(request,work,ident,page):
    try: return JsonResponse(call(request,lambda s: desk.history(s,work,ident,page-1,request.GET.get('original')=='1',request.GET.get('revision'))))
    except (ValueError,OSError,EOFError,IndexError): raise Http404('Documento no disponible')


@login_required
@require_POST
def page_plan(request,work):
    if not authorize(request,'pages'): return JsonResponse({'error':'Sin permiso para modificar páginas.'},status=403)
    try:
        from app.pages import PageOperations,signature
        spec=json.loads(request.body)
        plan=call(request,lambda s:PageOperations(domain.CodingService(s)).plan(work,spec))
        return JsonResponse(dict(plan=plan,fingerprint=signature(plan)))
    except (ValueError,TypeError,KeyError,OSError) as error: return JsonResponse({'error':str(error)},status=400)


@login_required
@require_POST
def edit_preview(request,work,ident,page):
    if not authorize(request,'edit_pending'): return JsonResponse({'error':'Sin permiso de edición.'},status=403)
    try:
        values=json.loads(request.body)
        if not isinstance(values,dict):raise ValueError('Datos de vista previa inválidos.')
        ops=desk.edits(values)
        def render_pending(store):
            import base64,io
            from app.coding import render_page
            coder=domain.CodingService(store);row=coder.file(ident)
            if row['trabajo_id']!=work or row['hash_actual']!=values.get('version'): raise ValueError('Documento ajeno o desactualizado.')
            with render_page(coder.path(row['ruta']),page-1,ops) as frame:
                width,height=frame.size
                if not values.get('full'):frame.thumbnail((1800,1800))
                out=io.BytesIO()
                with frame.convert('RGB') as rgb:rgb.save(out,format='PNG')
                return dict(width=width,height=height,image=base64.b64encode(out.getvalue()).decode('ascii'))
        return JsonResponse(call(request,render_pending))
    except (ValueError,TypeError,OSError,IndexError) as error:return JsonResponse({'error':str(error)},status=400)
