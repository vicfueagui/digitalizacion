"""Validación común de listas de archivos antes de copiar datos o código."""
import re
import stat
import unicodedata
from pathlib import Path, PurePosixPath, PureWindowsPath


def sqlite_sidecar(name):
    """Decisión léxica: nunca hacer resolve/stat sobre auxiliares bloqueados."""
    return str(name).lower().endswith(('-wal', '-shm', '-journal'))


def checked_files(files, allowed):
    if not isinstance(files, dict) or not files:
        raise ValueError('El manifiesto debe contener una lista de archivos con huellas SHA-256.')
    seen = set()
    for name, digest in files.items():
        if not isinstance(name, str) or not name or '\\' in name:
            raise ValueError('Nombre de archivo no portable en el manifiesto.')
        path = PurePosixPath(name)
        if path.is_absolute() or PureWindowsPath(name).drive or any(p in ('', '.', '..') for p in name.split('/')):
            raise ValueError('El manifiesto requiere rutas relativas sin saltos: ' + name)
        if any(ord(ch) < 32 or ch in '<>:"|?*' for ch in name) or not allowed(name):
            raise ValueError('Ruta no permitida en el manifiesto: ' + name)
        if any(part.endswith((' ', '.')) or PureWindowsPath(part).is_reserved() for part in path.parts):
            raise ValueError('Nombre incompatible con Windows: ' + name)
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Huella SHA-256 inválida: ' + name)
        key = unicodedata.normalize('NFC', name).casefold()
        if key in seen:
            raise ValueError('Dos rutas se confunden por mayúsculas o acentos: ' + name)
        seen.add(key)
    for name in seen:
        if any(str(parent) in seen for parent in PurePosixPath(name).parents):
            raise ValueError('Una ruta es archivo y carpeta a la vez: ' + name)
    return files


def plain_path(root, name):
    """Rechazar enlaces en cada componente, incluso si resuelven dentro de la raíz."""
    root = Path(root).resolve()
    target = root.joinpath(*PurePosixPath(name).parts)
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('No se admiten enlaces en esta copia: ' + name)
        try:
            attributes = getattr(current.lstat(), 'st_file_attributes', 0)
        except FileNotFoundError:
            attributes = 0
        if attributes & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400):
            raise ValueError('No se admiten junctions ni puntos de reanálisis: ' + name)
    if root not in target.resolve().parents:
        raise ValueError('Ruta fuera del destino permitido: ' + name)
    return target


def walk_plain(root):
    """Enumeración estable sin descender por symlinks/junctions (también Windows 7)."""
    root=Path(root).resolve();pending=[root]
    while pending:
        folder=pending.pop()
        if folder!=root:
            try:plain_path(root,folder.relative_to(root).as_posix())
            except ValueError:continue
        directories=[]
        for path in sorted(folder.iterdir(),key=lambda p:(unicodedata.normalize('NFC',p.name).casefold(),p.name)):
            yield path
            try:plain_path(root,path.relative_to(root).as_posix())
            except ValueError:continue
            if path.is_dir():directories.append(path)
        pending.extend(reversed(directories))
