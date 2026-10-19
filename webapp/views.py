import csv
import io
import json
import uuid
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .engine import get_engine
from . import domain
from .forms import action_form, LABELS
from .security import login_limit


def role(user):
    if user.is_superuser: return 'Administrador'
    from app.operations import ROLES
    groups = list(user.groups.filter(name__in=ROLES).values_list('name', flat=True))
    return groups[0] if len(groups) == 1 else 'Consulta'


def common(request):
    from app import VERSION
    return {'web_version': VERSION + ' · web candidata', 'demo_mode': settings.CONFIG['demo'],
            'user_role': role(request.user) if hasattr(request, 'user') and request.user.is_authenticated else ''}


def call(request, function, ticket=None):
    return get_engine().call(request.user.get_username(), function, ticket)


def filters(request):
    return {key: request.GET.get(key, '').strip()[:200] for key in ['q', 'folio', 'digitalizador', 'estado', 'prioridad', 'pendiente']}


@require_http_methods(['GET', 'POST'])
def access(request):
    error = ''
    if request.method == 'POST':
        if login_limit(): error = 'Espera cinco minutos antes de volver a intentar.'
        else:
            user = authenticate(request, username=request.POST.get('usuario', ''), password=request.POST.get('clave', ''))
            if user:
                login(request, user)
                return redirect('home')
            login_limit(True)
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'access.html', {'error': error})


@require_POST
def exit_session(request):
    logout(request)
    return redirect('access')


@login_required
@require_GET
def home(request):
    return render(request, 'home.html', {'snapshot': call(request, lambda s: domain.overview(s, filters(request))), 'active': 'home'})


@login_required
@require_GET
def works(request):
    from .work_table import build
    f = filters(request)
    rows,summary = call(request, lambda s: build(s, f,request.GET.get('orden','nombre'),request.GET.get('desc')=='1'))
    page = Paginator(rows, 40).get_page(request.GET.get('page'))
    return render(request, 'work_rows.html' if request.headers.get('HX-Request') else 'works.html',
                  {'page': page, 'filters': f, 'active': 'works', 'states': domain.STATES,'summary':summary,
                   'can_code':authorize(request,'code'),'return_url':request.get_full_path()})


@login_required
@require_GET
def kanban(request):
    return render(request, 'board_rows.html' if request.headers.get('HX-Request') else 'board.html',
                  {'columns': call(request, lambda s: domain.board(s, filters(request))), 'filters': filters(request), 'active': 'kanban'})


@login_required
@require_GET
def expediente(request, work):
    try: data = call(request, lambda s: domain.detail(s, work))
    except ValueError: raise Http404('Expediente inexistente')
    data['active'] = 'works'
    selected = request.GET.get('recepcion')
    if selected:
        data['viewed_receipt'] = next((i for i in data['integrations'] if str(i['id'])==selected),None)
        if not data['viewed_receipt']: raise Http404('Recepción ajena al ciclo')
    return render(request, 'detail.html', data)


@login_required
@require_GET
def folios(request):
    from .folio_context import folio_view
    selected = request.GET.get('folio', '')
    query, condition = request.GET.get('q','')[:200], request.GET.get('condicion','')
    try: data = call(request, lambda s: folio_view(s, selected, query, condition))
    except (ValueError, TypeError): raise Http404('Folio inexistente')
    data.update(active='folios', selected=selected, query=query, condition=condition,
                conditions=['Esperado','Recibido / cotejado','Faltante','Discrepancia','Devuelto'])
    return render(request, 'folio_rows.html' if request.headers.get('HX-Request') else 'folios.html', data)


@login_required
@require_http_methods(['GET','POST'])
def count_desk(request, work):
    from .counting import snapshot, change
    if not authorize(request, 'count'): return HttpResponseForbidden('Tu perfil no permite registrar conteos.')
    error = ''
    if request.method == 'POST':
        ticket = request.POST.get('ticket', '')
        try:
            identity = signing.loads(ticket, salt='conteo', max_age=7200)
            if identity[:2] != [request.user.pk, work]: raise signing.BadSignature()
        except (signing.BadSignature, TypeError, IndexError): return HttpResponseForbidden('Formulario vencido o ajeno.')
        try:
            profile = role(request.user)
            call(request, lambda s: change(s,profile,work,request.POST.get('operacion'),request.POST,identity[2]), ticket)
            return redirect('count_desk', work=work)
        except (ValueError,OSError) as exc: error = str(exc)
    try: data = call(request, lambda s: snapshot(s,work))
    except ValueError: raise Http404('Expediente inexistente')
    data.update(active='works',error=error,ticket=signing.dumps([request.user.pk,work,data['fingerprint'],uuid.uuid4().hex],salt='conteo'))
    return render(request, 'count_desk.html', data)


@login_required
@require_GET
def indicators(request):
    from app.analytics import PERIODS, DIMENSIONS, SOURCES
    from .analytics_view import build
    config = {'period': request.GET.get('periodo', 'Mes'), 'dimension': request.GET.get('dimension', 'Folio'),
              'source': request.GET.get('fuente', SOURCES[0]), 'start': request.GET.get('desde', ''), 'end': request.GET.get('hasta', '')}
    try:
        data = call(request, lambda s: build(s, filters(request), config))
    except ValueError as error:
        messages.error(request, str(error))
        return redirect('indicators')
    if request.GET.get('exportar') == 'csv':
        cube = data['cube']
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow(['Periodo', 'Grupo', 'Hojas', 'Conteos pendientes', 'TIFF', 'Páginas', 'Expedientes distintos'])
        for row in cube['filas']:
            writer.writerow([safe_csv(row[k]) for k in ['periodo', 'grupo', 'hojas', 'pendientes', 'tiff', 'paginas', 'expedientes']])
        response = HttpResponse('\ufeff' + buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="indicadores_filtrados.csv"'
        return response
    data.update(active='indicators',periods=PERIODS,dimensions=DIMENSIONS,sources=SOURCES,states=domain.STATES,
                config=config,filters=filters(request))
    data['charts'] = dict(stages=data['snapshot']['etapas'],coding=data['coding'],quality=data['quality'],
                          frequent=data['frequent'],series=data['series'],reception=data['reception'],
                          volume=[{'label':r['periodo']+' · '+r['grupo'],'value':r['paginas']} for r in data['cube']['filas']])
    return render(request, 'indicators.html', data)


def safe_csv(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')): return "'" + value
    return value


@login_required
@require_GET
def preview_image(request, work, file_id, page):
    try: data = call(request, lambda s: domain.image(s, work, file_id, page - 1))
    except (ValueError, OSError, EOFError): raise Http404('No se pudo abrir esa página')
    return HttpResponse(data, content_type='image/png')


def action_context(request, work):
    if work: return call(request, lambda s: domain.detail(s, work))
    return call(request, lambda s: {'folios': s.rows('SELECT * FROM folios WHERE activo=1 ORDER BY id DESC'),
                                   'items': s.rows('SELECT i.*,p.nombre FROM prestamo_items i LEFT JOIN personas p ON p.curp=i.curp_esperada ORDER BY i.id DESC')})


def authorize(request, action):
    from app.operations import ROLES
    allowed = ROLES[role(request.user)]
    permission = domain.PERMISSIONS.get(action)
    if action == 'respond': return allowed is None or bool({'corregir', 'observar'} & allowed)
    return permission is not None and (allowed is None or permission in allowed)


@login_required
@require_http_methods(['GET', 'POST'])
def action(request, action, work=0):
    if action not in LABELS: raise Http404('Acción desconocida')
    if not authorize(request, action): return HttpResponseForbidden('Tu perfil no permite esta acción.')
    try: context = action_context(request, work)
    except ValueError: raise Http404('Expediente inexistente')
    form = action_form(action, context, request.POST if request.method == 'POST' else None, request.FILES or None)
    ticket = request.POST.get('ticket', '')
    if request.method == 'POST':
        try:
            identity = signing.loads(ticket, salt='accion', max_age=7200)
            if identity[:3] != [request.user.pk, action, work]: raise signing.BadSignature()
        except signing.BadSignature:
            return HttpResponseForbidden('El formulario venció o pertenece a otra sesión. Ábrelo nuevamente.')
        if form.is_valid():
            data = dict(form.cleaned_data)
            for key, value in list(data.items()):
                if hasattr(value, 'isoformat'): data[key] = value.isoformat()
                elif isinstance(value, bool): data[key] = 'on' if value else ''
            paths = []
            try:
                if action == 'upload':
                    for upload in data.pop('archivos'):
                        suffix = Path(upload.name).suffix.lower()
                        if suffix not in ('.tif', '.tiff'): raise ValueError('Solo se admiten TIFF.')
                        # El contenedor es aleatorio; conservar el nombre recibido
                        # permite rastrear el escaneo sin usar rutas del cliente.
                        from pathlib import PureWindowsPath
                        name = PureWindowsPath(upload.name).name
                        if any(c in name for c in '<>:"|?*') or name.endswith((' ', '.')) or PureWindowsPath(name).is_reserved():
                            raise ValueError('El nombre del TIFF no es compatible con Windows.')
                        folder = settings.WORKSPACE / '.web' / 'incoming' / uuid.uuid4().hex
                        folder.mkdir()
                        dest = folder / name
                        paths.append(dest)
                        with dest.open('xb') as out:
                            for chunk in upload.chunks(): out.write(chunk)
                profile = role(request.user)
                result = call(request, lambda s: domain.act(s, profile, action, work, data, paths), ticket)
                (messages.warning if result.get('warning') else messages.success)(request, result['message'])
                if work and request.GET.get('volver')=='mesa': return redirect('coding_desk',work=work)
                return redirect('expediente', work=work) if work else redirect('folios')
            except (ValueError, OSError) as error:
                form.add_error(None, str(error))
                ticket = ''  # Nuevo intento explícito; el anterior queda registrado.
            finally:
                for path in paths:
                    path.unlink(missing_ok=True)
                    path.parent.rmdir()
    if not ticket:
        ticket = signing.dumps([request.user.pk, action, work, uuid.uuid4().hex], salt='accion')
    if request.method == 'GET':
        for key in ('archivo', 'entrega', 'folio', 'pagina', 'tipo', 'item'):
            if key in form.fields and request.GET.get(key): form.initial[key] = request.GET[key]
        if 'seleccion' in form.fields: form.initial['seleccion'] = request.GET.getlist('seleccion')
    return render(request, 'action.html', dict(form=form, ticket=ticket, title=LABELS[action], action=action,
                  work=context.get('work'), context=context, active='works' if work else 'folios'))


@login_required
@require_GET
def help_page(request):
    documents = [('Expedientes y estación TIFF 0.8.2', 'GUIA_ESTACION_TIFF_V082.md'),
                 ('Estación, conteo e indicadores 0.8.1 (antecedente)', 'GUIA_WEB_V081.md'),
                 ('Integraciones y entregas', 'INTEGRACIONES_V070.md'), ('Recepción e indicadores', 'RECEPCION_INDICADORES_V061.md'),
                 ('Operación paso a paso', 'OPERACION_V05.md'), ('Guía base 0.8.0 (antecedente)', 'GUIA_WEB_V080.md')]
    query = request.GET.get('q', '').casefold()
    rows = []
    for title, name in documents:
        path = settings.BASE_DIR / 'docs' / name
        if path.is_file():
            content = path.read_text(encoding='utf-8')
            if not query or query in (title + content).casefold(): rows.append({'title': title, 'content': content})
    return render(request, 'help.html', {'documents': rows, 'query': request.GET.get('q', ''), 'active': 'help'})


@login_required
@require_GET
def maintenance(request):
    from app.directory import Directory
    data = call(request, lambda s: {'catalog': domain.CodingService(s).catalog(), 'people': Directory(s).entries('persona'),
                                   'counts': s.rows('SELECT COUNT(*) AS n FROM auditoria')[0]['n']})
    return render(request, 'maintenance.html', dict(data, active='maintenance'))


@login_required
@require_GET
def delivery_view(request, work, delivery):
    def read(store):
        d = domain.Deliveries(store).get(delivery)
        if d['trabajo_id'] != work: raise ValueError('Entrega ajena al expediente')
        manifest = domain.Deliveries(store).verify(delivery)
        return {'delivery': d, 'manifest': manifest, 'work_id': work, 'active': 'works'}
    try: data = call(request, read)
    except (ValueError, OSError): return HttpResponse('La entrega no pudo verificarse. Conserva sus archivos y revisa el expediente.', status=409)
    return render(request, 'delivery.html', data)


@login_required
@require_GET
def delivery_image(request, work, delivery, file_id, page):
    def read(store):
        service = domain.Deliveries(store)
        d = service.get(delivery)
        if d['trabajo_id'] != work: raise ValueError('Entrega ajena')
        manifest = service.verify(delivery)
        item = next((r for r in manifest['items'] if r['archivo_id'] == file_id), None)
        if not item or not 1 <= page <= item['paginas']: raise ValueError('Página ajena')
        from app.manifests import plain_path
        frame = domain.render_page(plain_path(store.workspace.path(d['ruta']), item['ruta']), page - 1)
        try:
            frame.thumbnail((1800, 1800)); out = io.BytesIO()
            with frame.convert('RGB') as rgb:
                rgb.save(out, format='PNG')
            return out.getvalue()
        finally: frame.close()
    try: content = call(request, read)
    except (ValueError, OSError, EOFError): raise Http404('Página no disponible')
    return HttpResponse(content, content_type='image/png')


@login_required
@require_http_methods(['GET', 'POST'])
def import_list(request):
    if not authorize(request, 'import_list'): return HttpResponseForbidden('Tu perfil no permite importar listas.')
    from django import forms
    from app.intake import LoanLists, FIELDS
    plan = None
    errors = []
    token = request.POST.get('plan', '')
    if token:
        try:
            user, plan_id = signing.loads(token, salt='lista', max_age=7200)
            if user != request.user.pk or len(plan_id) != 32 or any(c not in '0123456789abcdef' for c in plan_id): raise signing.BadSignature()
            plan_path = settings.WORKSPACE / '.web' / 'incoming' / (plan_id + '.json')
            plan = json.loads(plan_path.read_text(encoding='utf-8'))
        except (signing.BadSignature, OSError, ValueError): return HttpResponseForbidden('Vista previa vencida o inválida.')
    form = forms.Form(request.POST if request.method == 'POST' else None, request.FILES or None)
    if not plan:
        form.fields['archivo'] = forms.FileField(label='Lista CSV o XLSX', widget=forms.ClearableFileInput(attrs={'accept': '.csv,.xlsx'}))
        form.fields['folio'] = forms.CharField(label='Folio común si no está en la lista', required=False, max_length=120)
        form.fields['legajo'] = forms.IntegerField(label='Legajo común confirmado, solo si falta en la lista', required=False, min_value=1)
    else:
        form.fields['hoja'] = forms.ChoiceField(label='Hoja', choices=[(x, x) for x in plan['hojas']], initial=plan['config']['sheet'])
        form.fields['fila'] = forms.IntegerField(label='Fila de encabezados', min_value=1, initial=plan['config']['header_row'])
        for key, label in FIELDS.items():
            form.fields['col_' + key] = forms.ChoiceField(label=label, choices=[('', 'Sin asignar')] + [(str(i), str(h)) for i, h in enumerate(plan['encabezados'])], required=False, initial=str(plan['config']['mapping'].get(key, '')))
    for field in form.fields.values(): field.widget.attrs['class'] = 'form-control'
    if request.method == 'POST':
        try:
            if plan and request.POST.get('paso') == 'confirmar':
                if request.POST.get('confirmado') != 'on': raise ValueError('Confirma la revisión de la vista previa.')
                result = call(request, lambda s: LoanLists(s).commit(plan), 'import-list:' + token)
                messages.success(request, 'Lista registrada: {} elementos nuevos; {} filas por revisar. Falta cotejar la recepción física.'.format(result['elementos_nuevos'], result['por_revisar']))
                return redirect('folios')
            if form.is_valid():
                if not plan:
                    upload = form.cleaned_data['archivo']; suffix = Path(upload.name).suffix.lower()
                    if suffix not in ('.csv', '.xlsx') or upload.size > 10 * 1024 * 1024: raise ValueError('Usa CSV o XLSX de hasta 10 MB.')
                    plan_id = uuid.uuid4().hex
                    path = settings.WORKSPACE / '.web' / 'incoming' / (plan_id + suffix)
                    with path.open('xb') as out:
                        for chunk in upload.chunks(): out.write(chunk)
                    if suffix == '.xlsx':
                        import zipfile
                        with zipfile.ZipFile(path) as z:
                            if len(z.infolist()) > 1500 or sum(i.file_size for i in z.infolist()) > 100 * 1024 * 1024: raise ValueError('El XLSX expandido supera el tamaño permitido para este equipo.')
                    plan = call(request, lambda s: LoanLists(s).preview(path, default_folio=form.cleaned_data['folio'], default_legajo=form.cleaned_data['legajo']))
                    token = signing.dumps([request.user.pk, plan_id], salt='lista')
                    plan_path = settings.WORKSPACE / '.web' / 'incoming' / (plan_id + '.json')
                else:
                    mapping = {k: int(form.cleaned_data['col_' + k]) for k in FIELDS if form.cleaned_data['col_' + k] != ''}
                    config = dict(plan['config'], sheet=form.cleaned_data['hoja'], header_row=form.cleaned_data['fila'], mapping=mapping)
                    source = plan['path']
                    plan = call(request, lambda s: LoanLists(s).preview(source, **config))
                plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding='utf-8')
                # Tras analizar se vuelve a construir el formulario de mapeo en GET firmado.
                request.session['plan_actual'] = token
                return redirect('import_preview')
        except (ValueError, OSError) as error: errors.append(str(error))
    return render(request, 'import_list.html', dict(form=form, plan=plan, token=token, errors=errors, active='folios'))


@login_required
@require_GET
def import_preview(request):
    if not authorize(request, 'import_list'): return HttpResponseForbidden()
    token = request.session.get('plan_actual', '')
    try:
        user, plan_id = signing.loads(token, salt='lista', max_age=7200)
        if user != request.user.pk or len(plan_id) != 32 or any(c not in '0123456789abcdef' for c in plan_id): raise signing.BadSignature()
        plan = json.loads((settings.WORKSPACE / '.web' / 'incoming' / (plan_id + '.json')).read_text(encoding='utf-8'))
    except (signing.BadSignature, OSError, ValueError): return redirect('import_list')
    from django import forms
    from app.intake import FIELDS
    form = forms.Form()
    form.fields['hoja'] = forms.ChoiceField(label='Hoja', choices=[(x, x) for x in plan['hojas']], initial=plan['config']['sheet'])
    form.fields['fila'] = forms.IntegerField(label='Fila de encabezados', initial=plan['config']['header_row'], min_value=1)
    for key, label in FIELDS.items(): form.fields['col_' + key] = forms.ChoiceField(label=label, required=False, initial=str(plan['config']['mapping'].get(key, '')), choices=[('', 'Sin asignar')] + [(str(i), str(h)) for i, h in enumerate(plan['encabezados'])])
    for f in form.fields.values(): f.widget.attrs['class'] = 'form-control'
    return render(request, 'import_list.html', dict(form=form, plan=plan, token=token, active='folios'))
