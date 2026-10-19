"""Captura web sobre los servicios de conteo; estado firmado contra formularios viejos."""
import hashlib
import json
from app.integrations import Integrations
from app.operations import Operations
from app.core import STATES


def snapshot(store, work):
    service = Integrations(store)
    current = service.current(work)
    context = service.context(work)
    current_work = store.one('trabajos', work)
    blocks = store.rows('SELECT * FROM conteos WHERE integracion_id=? ORDER BY id', (current['id'],))
    history = [r for r in service.list(work) if r['id'] != current['id']]
    fingerprint = hashlib.sha256(json.dumps([current,blocks,current_work['estado']],sort_keys=True).encode()).hexdigest()
    return dict(work=dict(current_work,nombre=context['nombre']), context=context, current=current,
                blocks=blocks, history=history, historical=sum(r['fisicos'] or 0 for r in history),
                historical_pending=sum(r['fisicos'] is None for r in history),
                total=sum(r['cantidad'] for r in blocks if r['activo']),
                confirmed=current['fisicos'] is not None, fingerprint=fingerprint,
                tiff=next(r['tiff'] for r in service.list(work) if r['id']==current['id']),
                pages=next(r['paginas'] for r in service.list(work) if r['id']==current['id']))


def change(store, role, work, action, data, fingerprint):
    Operations(store, role).permit('proceso')
    state = snapshot(store, work)
    if fingerprint != state['fingerprint']:
        raise ValueError('Los bloques o la integración cambiaron. Revisa el conteo actualizado antes de confirmar.')
    reason = str(data.get('motivo','')).strip()
    if not reason: raise ValueError('Indica el motivo o la referencia del bloque.')
    if action == 'reabrir':
        if data.get('confirmado') != 'on': raise ValueError('Confirma la reapertura del conteo.')
        if not state['confirmed'] and state['work']['estado'] in STATES[:2]:
            raise ValueError('El conteo ya está abierto.')
        if state['work']['estado'] != STATES[1]: store.change_state(work, STATES[1], reason)
        with store.db:
            store.dirty_count(work)
            store.audit('integraciones', state['current']['id'], 'reabrir conteo', state['current'],
                        Integrations(store).current(work), reason)
    elif state['confirmed']:
        raise ValueError('El conteo está confirmado. Usa Reabrir con motivo antes de modificarlo.')
    elif action == 'agregar': store.add_count(work, data.get('cantidad'), reason)
    elif action == 'corregir':
        selected = next((b for b in state['blocks'] if b['id']==int(data.get('bloque',0)) and b['activo']),None)
        if not selected: raise ValueError('El bloque no pertenece al conteo actual.')
        store.edit_count(selected['id'], data.get('cantidad'), reason, data.get('anular')=='on')
    elif action == 'confirmar':
        if data.get('confirmado') != 'on': raise ValueError('Confirma el total físico mostrado.')
        store.confirm_count(work)
    else: raise ValueError('Acción de conteo desconocida.')
    return {'message':'Conteo registrado.', 'work':work}
