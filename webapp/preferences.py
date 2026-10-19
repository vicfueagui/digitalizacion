from django.db import transaction
import threading
from .models import DeskPreferences

DEFAULTS = {'left':220, 'right':245, 'view':'list', 'hide_left':False, 'hide_right':False, 'advance':True,'thumb_size':120}
_writes = threading.Lock()  # Un único servidor posee el bloqueo de este workspace.


def read(user):
    row = DeskPreferences.objects.filter(user=user).first()
    return {'favorites':row.favorites if row else [], 'layout':dict(DEFAULTS, **(row.layout if row else {}))}


def update(user, data, valid_codes):
    kind = data.get('kind')
    if kind not in ('favorite','layout'): raise ValueError('Preferencia desconocida.')
    with _writes, transaction.atomic():
        row, _ = DeskPreferences.objects.get_or_create(user=user)
        if kind == 'favorite':
            ident = int(data.get('catalog_id',0))
            if ident not in valid_codes: raise ValueError('El código ya no está activo.')
            enabled = data.get('enabled')
            if type(enabled) is not bool: raise ValueError('Indica favorito activo o inactivo.')
            row.favorites = [i for i in row.favorites if i != ident]
            if enabled: row.favorites.append(ident)
        else:
            patch = data.get('layout',{})
            if not isinstance(patch,dict) or set(patch)-set(DEFAULTS): raise ValueError('Diseño no válido.')
            for key,value in patch.items():
                if key in ('left','right') and (type(value) is not int or not 170<=value<=460): raise ValueError('Ancho fuera de rango.')
                if key == 'view' and value not in ('icons','list','details','thumbs'): raise ValueError('Vista no válida.')
                if key == 'thumb_size' and (type(value) is not int or not 80<=value<=200):raise ValueError('Tamaño fuera de rango.')
                if key in ('hide_left','hide_right','advance') and type(value) is not bool: raise ValueError('Preferencia no válida.')
            row.layout = dict(row.layout, **patch)
        row.save()
    return read(user)
