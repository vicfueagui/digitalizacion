"""Crea la configuración local sin publicar ni mostrar su clave secreta."""

import os
import secrets
import tempfile
from pathlib import Path

PLACEHOLDER_SECRETS = {
    "",
    "cambie-esta-clave-en-produccion",
    "dev-only-change-before-production",
}


def _current_secret(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("DJANGO_SECRET_KEY="):
            return line.partition("=")[2].strip()
    return ""


def _with_secret(content: str, secret_key: str) -> str:
    result = []
    secret_written = False
    for line in content.splitlines():
        if line.startswith("DJANGO_SECRET_KEY="):
            if not secret_written:
                result.append(f"DJANGO_SECRET_KEY={secret_key}")
                secret_written = True
            continue
        result.append(line)
    if not secret_written:
        result.append(f"DJANGO_SECRET_KEY={secret_key}")
    return "\n".join(result) + "\n"


def _restrict_permissions(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        # Windows aplica sus ACL de usuario; chmod puede no representar todos los bits POSIX.
        pass


def ensure_local_env(project_dir: Path) -> bool:
    """Garantiza `.env`; devuelve True cuando creó o sustituyó una clave de ejemplo."""

    project_dir = project_dir.resolve()
    env_path = project_dir / ".env"
    example_path = project_dir / ".env.example"
    source_path = env_path if env_path.is_file() else example_path
    if not source_path.is_file():
        raise FileNotFoundError("No existe .env ni .env.example.")

    content = source_path.read_text(encoding="utf-8")
    if env_path.is_file() and _current_secret(content) not in PLACEHOLDER_SECRETS:
        _restrict_permissions(env_path)
        return False

    secure_content = _with_secret(content, secrets.token_urlsafe(64))
    descriptor, temporary_name = tempfile.mkstemp(prefix=".env.", dir=project_dir, text=True)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary_file:
            temporary_file.write(secure_content)
        _restrict_permissions(temporary_path)
        os.replace(temporary_path, env_path)
        _restrict_permissions(env_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return True


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent
    changed = ensure_local_env(project_dir)
    if changed:
        print("Configuración local creada con una clave aleatoria.")
    else:
        print("Configuración local existente conservada.")


if __name__ == "__main__":
    main()
