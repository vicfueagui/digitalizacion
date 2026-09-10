import hashlib
from pathlib import Path, PurePosixPath
from typing import Iterator, Protocol

from django.core.exceptions import ValidationError


class ReadOnlyTiffStorage(Protocol):
    def resolve_folder(self, relative_folder: str) -> Path: ...

    def iter_tiffs(self, relative_folder: str) -> Iterator[Path]: ...

    def sha256(self, path: Path) -> str: ...


class LocalReadOnlyTiffStorage:
    """Adaptador local/de red que nunca ofrece operaciones de escritura."""

    def __init__(self, root_setting: str):
        if not root_setting:
            raise ValidationError("DIGITAL_REPOSITORY_ROOT no está configurado.")
        self.root = Path(root_setting).expanduser().resolve()
        if not self.root.is_dir():
            raise ValidationError("DIGITAL_REPOSITORY_ROOT no existe o no es una carpeta.")
        self.skipped_outside_root = 0

    def resolve_folder(self, relative_folder: str) -> Path:
        relative = PurePosixPath(str(relative_folder).replace("\\", "/"))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValidationError("La carpeta relativa no puede escapar del repositorio configurado.")
        target = (self.root / Path(*relative.parts)).resolve()
        if not target.is_relative_to(self.root):
            raise ValidationError("La carpeta solicitada está fuera del repositorio configurado.")
        if not target.is_dir():
            raise ValidationError("La carpeta del expediente no existe dentro del repositorio.")
        return target

    def iter_tiffs(self, relative_folder: str):
        target = self.resolve_folder(relative_folder)
        for path in sorted(target.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".tif", ".tiff"}:
                continue
            if not path.resolve().is_relative_to(target):
                self.skipped_outside_root += 1
                continue
            yield path

    def sha256(self, path: Path) -> str:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValidationError("No se calculará el hash de un archivo fuera del repositorio.")
        digest = hashlib.sha256()
        with resolved.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
