"""Raíz explícita de datos y exclusión entre procesos (sin servicios externos)."""
import os
import sqlite3
from pathlib import Path, PureWindowsPath

CODE_ROOT = Path(__file__).resolve().parent.parent


def portable_name(value):
    return PureWindowsPath(str(value)).name


def absolute(value):
    path = Path(value).expanduser()
    return (path if path.is_absolute() else CODE_ROOT / path).resolve()


class Workspace:
    def __init__(self, root=None, database=None):
        if root is not None:
            self.root = absolute(root)
            self.database = self.root / 'datos' / 'digitalizacion.sqlite3'
            if database is not None:
                raise ValueError('Usa --workspace o --db, no ambos.')
        elif database is not None:
            self.database = absolute(database)
            # Compatibilidad con la distribución original y con bases de pruebas.
            self.root = (self.database.parent.parent if self.database.parent.name == 'datos'
                         else self.database.parent)
        else:
            self.root = CODE_ROOT
            self.database = self.root / 'datos' / 'digitalizacion.sqlite3'
        self.database = self.path(self.database)

    def path(self, value):
        text = str(value)
        win = PureWindowsPath(text)
        if win.drive and os.name != 'nt':
            raise ValueError('Ruta absoluta de Windows no disponible aquí. Restaura el espacio original; no se remapea automáticamente: ' + text)
        # Las rutas relativas legadas usan backslash; los componentes se validan antes de resolver.
        portable = text.replace('\\', '/')
        if '..' in portable.split('/'):
            raise ValueError('La ruta contiene una salida del espacio de trabajo.')
        path = (self.root / portable).resolve()
        if self.root not in path.parents:
            raise ValueError('Ruta fuera del espacio de trabajo: ' + text)
        return path

    def relative(self, value):
        return self.path(value).relative_to(self.root).as_posix()

    @property
    def backups(self):
        return self.path('respaldos')

    @property
    def reports(self):
        return self.path('reportes')


class WorkspaceLock:
    """El SO libera el bloqueo incluso si se cierra inesperadamente el programa."""
    def __init__(self, root):
        root.mkdir(parents=True, exist_ok=True)
        self.file = (root / '.digitalizacion.lock').open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                self.file.seek(0, 2)
                if not self.file.tell():
                    self.file.write(b'0'); self.file.flush()
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise ValueError('Este espacio está abierto en otro proceso. Cierra la otra aplicación antes de continuar.')

    def close(self):
        if not self.file.closed:
            self.file.close()


class Connection(sqlite3.Connection):
    def close(self):
        try:
            super().close()
        finally:
            lock = getattr(self, 'workspace_lock', None)
            if lock:
                lock.close()
