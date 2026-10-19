"""Un hilo dueño de SQLite y del bloqueo de workspace durante toda la sesión.

Las solicitudes se serializan. No se comparte una conexión SQLite entre hilos,
ni se permite abrir el mismo workspace con Tk mientras el servidor está vivo.
"""
import json
import queue
import sqlite3
import threading
from concurrent.futures import Future
from pathlib import Path


class Engine:
    def __init__(self, workspace):
        self.workspace = Path(workspace).resolve()
        self.queue = queue.Queue(maxsize=24)
        self.ready = Future()
        self.closed = False
        self.thread = threading.Thread(target=self._worker, name='Expediente-SQLite', daemon=True)
        self.thread.start()
        self.ready.result(timeout=60)

    def _worker(self):
        from app.core import Store
        store = ledger = None
        try:
            store = Store(workspace=self.workspace)
            ledger = sqlite3.connect(str(self.workspace / '.web' / 'solicitudes.sqlite3'))
            ledger.execute('CREATE TABLE IF NOT EXISTS solicitudes (ticket TEXT PRIMARY KEY, estado TEXT NOT NULL, respuesta TEXT)')
            ledger.commit()
            self.ready.set_result(True)
            while True:
                task = self.queue.get()
                if task is None:
                    break
                future, actor, function, ticket = task
                if not future.set_running_or_notify_cancel():
                    continue
                try:
                    if ticket:
                        previous = ledger.execute('SELECT estado,respuesta FROM solicitudes WHERE ticket=?', (ticket,)).fetchone()
                        if previous:
                            if previous[0] == 'Completada':
                                future.set_result(json.loads(previous[1]))
                                continue
                            raise ValueError('Esta solicitud ya se intentó. Revisa el estado registrado antes de repetir la acción desde un formulario nuevo.')
                        with ledger:
                            ledger.execute('INSERT INTO solicitudes VALUES (?, ?, NULL)', (ticket, 'Iniciada'))
                    store.operador = actor
                    result = function(store)
                    if ticket:
                        with ledger:
                            ledger.execute('UPDATE solicitudes SET estado=?,respuesta=? WHERE ticket=?', ('Completada', json.dumps(result, ensure_ascii=False), ticket))
                    future.set_result(result)
                except BaseException as error:
                    if store.db.in_transaction:
                        store.db.rollback()
                    # Un fallo puede seguir a una operación de archivos ya confirmada.
                    # Conservar Iniciada obliga a revisar y evita una repetición ciega.
                    future.set_exception(error)
        except BaseException as error:
            if not self.ready.done():
                self.ready.set_exception(error)
        finally:
            if ledger:
                ledger.close()
            if store:
                store.db.close()

    def call(self, actor, function, ticket=None):
        if self.closed:
            raise ValueError('El servicio ya está cerrado.')
        future = Future()
        try:
            self.queue.put_nowait((future, actor, function, ticket))
        except queue.Full:
            raise ValueError('El equipo está terminando otras operaciones. Espera antes de volver a intentar.')
        # No abandonar escrituras en segundo plano por un timeout de la interfaz.
        return future.result()

    def close(self):
        if not self.closed:
            self.closed = True
            self.queue.put(None)
            self.thread.join()


_engine = None


def get_engine():
    if _engine is None:
        raise RuntimeError('Inicia mediante iniciar_web.py para comprobar el workspace.')
    return _engine


def start(workspace):
    global _engine
    if _engine is not None:
        raise RuntimeError('Servicio ya iniciado')
    _engine = Engine(workspace)
    return _engine


def stop():
    global _engine
    if _engine:
        _engine.close()
        _engine = None
