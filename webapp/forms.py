from django import forms
from app.core import STATES
from app.operations import CUSTODY
from app.review import OBSERVATION_TYPES


LABELS = {'folio': 'Registrar folio', 'expected': 'Añadir expediente esperado', 'receipt': 'Registrar recepción del folio',
          'accept': 'Cotejar y aceptar selección', 'difference': 'Revisar diferencia de recepción', 'legajos': 'Desglosar legajos',
          'assign': 'Asignar responsable', 'integration': 'Recibir nueva integración', 'count': 'Añadir bloque de hojas',
          'confirm_count': 'Confirmar conteo actual', 'edit_count': 'Corregir bloque de conteo', 'state': 'Registrar etapa',
          'card': 'Prioridad y seguimiento', 'custody': 'Registrar devolución / custodia', 'upload': 'Importar TIFF',
          'code': 'Codificar documento', 'rename': 'Renombrar TIFF', 'edit': 'Girar o recortar una página',
          'original': 'Restaurar imagen original', 'batch': 'Retirar / recuperar selección', 'recover': 'Recuperar operación TIFF',
          'correction': 'Solicitar reescaneo', 'replace': 'Aplicar reescaneo', 'resolve_correction': 'Resolver sin reemplazo',
          'deliver': 'Organizar / entregar expediente completo', 'validate': 'Validar expediente', 'begin_review': 'Iniciar revisión de entrega',
          'approve': 'Aprobar entrega exacta', 'observe': 'Registrar observación', 'respond': 'Responder / validar observación',
          'incident': 'Registrar incidencia', 'catalog': 'Añadir código documental', 'directory': 'Añadir al directorio',
          'backup': 'Crear respaldo completo', 'export_delivery': 'Exportar copia de entrega'}


class MultipleInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFiles(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = MultipleInput(attrs={'accept': '.tif,.tiff'})
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not isinstance(data, (list, tuple)):
            data = [data] if data else []
        if not data:
            raise forms.ValidationError('Selecciona al menos un archivo TIFF.')
        if len(data) > 100 or sum(f.size for f in data) > 200 * 1024 * 1024:
            raise forms.ValidationError('Importa hasta 100 TIFF y 200 MB por lote.')
        return [super(MultipleFiles, self).clean(item, initial) for item in data]


def action_form(action, context, data=None, files=None):
    f = forms.Form(data=data, files=files)
    def text(key, label, required=True, initial='', help_text=''):
        f.fields[key] = forms.CharField(label=label, required=required, max_length=2000, initial=initial, help_text=help_text)
    def number(key, label, minimum=0, required=True, initial=None):
        f.fields[key] = forms.IntegerField(label=label, min_value=minimum, required=required, initial=initial)
    def choice(key, label, choices, required=True):
        f.fields[key] = forms.ChoiceField(label=label, choices=[('', 'Selecciona…')] + list(choices), required=required)
    def check(label): f.fields['confirmado'] = forms.BooleanField(label=label, required=True)
    def date(key='fecha', label='Fecha real', required=True):
        f.fields[key] = forms.DateField(label=label, required=required, widget=forms.DateInput(attrs={'type': 'date'}))
    def pickfile():
        choice('archivo', 'TIFF', [(r['id'], '#{} · {} · {}'.format(r['id'], r['nombre'], 'Activo' if r['activo'] else 'Retirado')) for r in context.get('files', [])])
    def delivery():
        choice('entrega', 'Entrega exacta', [(r['id'], 'Versión {} · {} · {}'.format(r['numero'], r['estado'], r['creado'][:10])) for r in context.get('deliveries', [])])
    def folio():
        choice('folio', 'Folio', [(r['id'], r['numero']) for r in context.get('folios', [])])
    if action == 'folio':
        text('numero', 'Número de folio'); date(required=False); text('responsable', 'Responsable', False)
    elif action == 'expected':
        folio(); text('curp', 'CURP'); text('nombre', 'Nombre completo'); number('legajo', 'Legajo', 1); text('ubicacion', 'Ubicación original', False)
    elif action == 'receipt':
        folio()
        for key, label in [('origen', 'Área de origen'), ('entrega', 'Persona que entrega'), ('recibe', 'Persona que recibe'), ('acuse', 'Referencia del acuse')]: text(key, label)
        text('fecha_hora', 'Fecha y hora real con zona, formato ISO', False, help_text='Vacío registra la hora actual. Ejemplo: 2026-10-05T09:30:00-06:00.')
    elif action in ('accept', 'difference', 'legajos'):
        folio()
        items = [(r['id'], '#{} · {} · {} · legajo {} · {}'.format(r['id'], r['curp_esperada'], r.get('nombre') or '', r['legajo_esperado'] or 'por confirmar', r['validacion'])) for r in context.get('items', [])]
        if action == 'accept':
            f.fields['seleccion'] = forms.MultipleChoiceField(label='Elementos cotejados físicamente', choices=items, widget=forms.CheckboxSelectMultiple)
            number('legajo', 'Legajo común solo para los que no lo tienen', 1, False)
            check('He cotejado físicamente CURP, nombre, legajo y documentación de cada elemento seleccionado.')
        else:
            choice('item', 'Elemento de la lista', items)
            if action == 'legajos': text('legajos', 'Legajos separados por comas', help_text='Cada número corresponde a un expediente físico comprobado.')
            else:
                choice('decision', 'Resultado', [(x, x) for x in ['Pendiente', 'Aceptado', 'Faltante', 'Discrepancia']])
                text('curp', 'CURP comprobada', False); number('legajo', 'Legajo comprobado', 1, False)
                f.fields['confirmado'] = forms.BooleanField(label='Aceptar expresamente el recibido fuera de lista, si corresponde', required=False)
    elif action == 'assign':
        text('persona', 'Persona responsable'); choice('rol', 'Función', [(r, r) for r in ['Digitalizador', 'Revisor', 'Responsable']])
    elif action == 'integration':
        folio(); date(); text('acuse', 'Referencia del acuse'); text('persona', 'Digitalizador', False)
        check('Cotejé CURP, legajo y documentación nueva; la entrega anterior está aprobada.')
    elif action in ('count', 'edit_count'):
        if action == 'edit_count':
            choice('bloque', 'Bloque de la integración actual', [(r['id'], '#{} · {} hojas'.format(r['id'], r['cantidad'])) for r in context.get('counts', []) if r['activo']])
            f.fields['anular'] = forms.BooleanField(label='Anular el bloque con motivo', required=False)
        number('cantidad', 'Hojas físicas del bloque', 1, initial=1)
    elif action == 'confirm_count': check('Comprobé los bloques y el total de hojas físicas de esta integración.')
    elif action == 'state': choice('estado', 'Nueva etapa', [(x, x) for x in STATES])
    elif action == 'card':
        choice('prioridad', 'Prioridad', [(x, x) for x in ['Baja', 'Normal', 'Alta', 'Urgente']]); date(label='Fecha objetivo', required=False)
        for key, label in [('notas', 'Nota de seguimiento'), ('etiqueta', 'Etiqueta'), ('bloqueo', 'Bloqueo a resolver')]: text(key, label, False)
    elif action == 'custody':
        choice('custodia', 'Movimiento físico', [(x, x) for x in CUSTODY]); text('recibe', 'Persona que recibe o acepta', False)
    elif action == 'upload': f.fields['archivos'] = MultipleFiles(label='Archivos TIFF nuevos', help_text='Se conservan los originales. Hasta 100 archivos y 200 MB por lote.')
    elif action in ('code', 'rename', 'edit', 'original', 'correction'):
        pickfile()
        if action == 'code': choice('codigo', 'Código documental', [(r['codigo'], r['codigo'] + ' · ' + r['titulo']) for r in context.get('catalog', []) if r['activo']])
        if action == 'rename': text('nombre', 'Nombre nuevo, conservando extensión TIFF')
        if action in ('edit', 'correction'): number('pagina', 'Página', 1, initial=1)
        if action == 'edit':
            choice('tipo', 'Ajuste', [('girar', 'Girar página'), ('recortar', 'Recortar por coordenadas de la imagen original')])
            f.fields['angulo'] = forms.ChoiceField(label='Giro', choices=[('90', '90° izquierda'), ('-90', '90° derecha'), ('180', '180°')], required=False)
            for key in ('x1', 'y1', 'x2', 'y2'): number(key, key.upper() + ' (solo recorte)', required=False)
        if action == 'correction': text('ubicacion', 'Ubicación de la hoja física')
        if action == 'original': check('Restaurar el original generará una nueva revisión y requerirá validar otra vez.')
    elif action == 'batch':
        choice('tipo', 'Acción para la selección', [('retirar', 'Retirar TIFF activos'), ('recuperar', 'Recuperar TIFF retirados')])
        f.fields['seleccion'] = forms.MultipleChoiceField(label='TIFF seleccionados', choices=[(r['id'], '#{} · {} · {}'.format(r['id'], r['nombre'], 'Activo' if r['activo'] else 'Retirado')) for r in context.get('files', [])], widget=forms.CheckboxSelectMultiple)
    elif action in ('replace', 'resolve_correction'):
        choice('correccion', 'Corrección', [(r['id'], '#{} · {} · {}'.format(r['id'], r['problema'], r['estado'])) for r in context.get('corrections', [])])
        if action == 'replace':
            choice('nuevo', 'TIFF importado de reemplazo', [(r['id'], '#{} · {}'.format(r['id'], r['nombre'])) for r in context.get('files', []) if r['activo']])
            choice('tipo', 'Alcance', [('pagina', 'Sustituir la página marcada'), ('documento', 'Sustituir documento')])
    elif action in ('begin_review', 'approve', 'export_delivery'):
        delivery()
        if action == 'approve': check('Revisé y cotejé esta entrega exacta; sus documentos y conteos son correctos.')
    elif action == 'deliver': check('Generar una nueva entrega del expediente completo actualizado, conservando las anteriores.')
    elif action == 'observe':
        choice('sesion', 'Sesión abierta', [(r['id'], r['inicio'] + ' · ' + r['revisor']) for r in context.get('sessions', [])])
        choice('tipo', 'Tipo de observación', [(x, x) for x in OBSERVATION_TYPES]); text('persona', 'Responsable de corregir'); text('ubicacion', 'Ubicación física', False)
        f.fields['bloqueante'] = forms.BooleanField(label='Impide aprobar hasta resolverse', required=False, initial=True)
    elif action == 'respond':
        choice('observacion', 'Observación', [(r['id'], '#{} · {} · {}'.format(r['id'], r['estado'], r['descripcion'])) for r in context.get('observations', [])])
        choice('estado', 'Respuesta', [(x, x) for x in ['En corrección', 'Resuelta', 'Validada', 'Abierta', 'Anulada']]); delivery(); f.fields['entrega'].required = False
    elif action == 'incident': text('documento', 'Código o referencia del documento', False)
    elif action == 'catalog':
        text('codigo', 'Código'); choice('carpeta', 'Clasificación', [('PERSONALES', 'Personales'), ('FEDERAL', 'Federal')]); text('titulo', 'Nombre del documento')
    elif action == 'directory':
        choice('tipo', 'Tipo', [(x, x) for x in ['persona', 'area', 'sistema', 'ubicacion']]); text('nombre', 'Nombre')
    text('motivo', 'Motivo o evidencia', initial='Comprobación realizada por el operador' if action == 'validate' else '')
    f.fields['motivo'].widget = forms.Textarea(attrs={'rows': 3})
    for field in f.fields.values():
        if isinstance(field.widget, forms.CheckboxInput): field.widget.attrs['class'] = 'form-check-input'
        elif not isinstance(field.widget, forms.CheckboxSelectMultiple): field.widget.attrs['class'] = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
    return f
