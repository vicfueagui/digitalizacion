"""Exportador local de texto revisado. Solo biblioteca estandar, Python >= 3.8.

No importa la aplicacion, no abre datos operativos y no utiliza la red.
Las huellas revisadas son una segunda barrera: detectar patrones no basta
para reconocer todos los nombres o datos personales en prosa libre.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import uuid
from urllib.parse import urlsplit


PERMITIDOS = (
    "CONTEXTO_CHATGPT.md", "AGENTS.md", "docs/CONTEXTO_PROYECTO.md",
    "docs/BITACORA_DESARROLLO.md", "docs/VALIDACION_FASE_B_HP.md",
    "docs/PLAN_MODERNIZACION.md", "docs/RESPALDOS.md", "docs/INFRAESTRUCTURA.md",
)
POLITICA = "tools/contexto_permitidos.json"
SALIDA = ".contexto-exportado"
MAX_BYTES = 1024 * 1024
SEGUIMIENTO = PERMITIDOS + (
    ".gitignore", "README.md", "app/__init__.py", POLITICA,
    "EXPORTAR_CONTEXTO.bat", "tools/exportar_contexto.py",
    "tests/test_exportar_contexto.py",
)
RAIZ_CODIGO = {
    "main.py", "actualizar.py", "asistente_actualizacion.py", "instalar_visor.py",
    "README.md", "ACTUALIZACION.html", "AGENTS.md", "CONTEXTO_CHATGPT.md",
    "requirements.txt", "requirements-legacy.txt", "requirements-laptop.txt",
    "INICIAR.bat", "DIAGNOSTICO.bat", "PROBAR.bat", "INSTALAR_VISOR.bat",
    "ACTUALIZAR.bat", "EXPORTAR_CONTEXTO.bat", "iniciar.sh", ".gitignore", ".dockerignore",
}


class ContextoError(Exception):
    pass


def ruta_normal(path, archivo=False):
    """Rechaza enlaces/junctions en todos los ancestros, tambien dentro de raiz."""
    path = Path(os.path.abspath(str(path)))
    for item in [path] + list(path.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ContextoError("enlace o junction no permitido")
    if archivo:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ContextoError("no es archivo regular independiente")
    return path


def leer(path):
    path = ruta_normal(path, archivo=True)
    if path.stat().st_size > MAX_BYTES:
        raise ContextoError("archivo demasiado grande")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ContextoError("archivo demasiado grande")
    return data


def huella(data):
    return hashlib.sha256(data).hexdigest()


def motivos_sensibles(texto):
    """Devuelve categorias, nunca valores ni fragmentos encontrados."""
    reglas = (
        ("marcado privado", r"(?i)CONTEXTO[_ -]PRIVADO|NO[_ -]EXPORTAR|datos personales reales"),
        ("clave privada", r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
        ("token", r"\b(?:gh[pousr]_[A-Za-z0-9]{12,}|github_pat_[A-Za-z0-9_]{12,}|sk-[A-Za-z0-9_-]{16,}|AKIA[A-Z0-9]{16})\b"),
        ("credencial en URL", r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/<>]+@"),
        ("parametro de credencial", r"(?i)[?&](?:token|api_key|password|secret|access_token)="),
        ("credencial asignada", r"(?im)[\"']?\b(?:password|passwd|contrasena|contraseña|api[_ -]?key|access[_ -]?token|secret|secreto|token)[\"']?\s*[:=]\s*[\"']?[^\s\"'`,;]{4,}"),
        ("autorizacion", r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9+/=_-]{8,}"),
        ("correo electronico", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        ("identificador personal", r"\b[A-Z][AEIOUX][A-Z]{2}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b|\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b"),
        ("numero personal", r"(?<![\w])(?:\d[ -]?){10,18}(?![\w])"),
        ("campo personal", r"(?im)^\s*(?:nombre completo|nombre|paciente|titular|domicilio|direccion|dirección|telefono|teléfono|curp|rfc|nss|clabe)\s*[:=]\s*\S+"),
        ("perfil personal en ruta", r"(?i)(?:[A-Z]:[\\/](?:Users|Usuarios)[\\/]|/Users/|/home/)[^\s\\/`\"<>]+"),
    )
    return [nombre for nombre, patron in reglas if re.search(patron, texto)]


def texto_seguro(value):
    if not isinstance(value, str) or len(value) > 240 or re.search(r"[\x00-\x1f]", value):
        return "[metadato omitido]"
    return "[metadato omitido]" if motivos_sensibles(value) else value


def remoto_seguro(raw):
    """Nunca exporta usuario, password, query, fragmento ni rutas desconocidas."""
    raw = raw.strip()
    scp = re.fullmatch(r"[^\s@]+@([^\s:]+):(.+)", raw)
    try:
        parsed = urlsplit("ssh://" + scp.group(1) + "/" + scp.group(2) if scp else raw)
        host = parsed.hostname
        if not host or parsed.scheme not in ("https", "http", "ssh", "git"):
            return "[remoto local o no reconocible; ruta omitida]"
        path = parsed.path.strip("/")
        if host.lower() == "github.com" and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path):
            candidate = "https://github.com/" + path
            return texto_seguro(candidate)
        return texto_seguro(host) + "/[ruta omitida]"
    except (ValueError, AttributeError):
        return "[remoto omitido]"


def buscar_git():
    candidates = [shutil.which("git")]
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if base:
            candidates.append(str(Path(base) / "Git/cmd/git.exe"))
    if os.environ.get("LOCALAPPDATA"):
        candidates.append(str(Path(os.environ["LOCALAPPDATA"]) / "Programs/Git/cmd/git.exe"))
    return next((item for item in candidates if item and Path(item).is_file()), None)


def ejecutar_git(exe, root, args):
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    command = [exe, "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root)] + list(args)
    try:
        run = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env, timeout=20,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return run.returncode, run.stdout.decode("utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return 99, ""


def nombre_codigo(name):
    """Criterio de nombres para auditoria, no certifica contenido ni historial."""
    return (name in RAIZ_CODIGO or name == POLITICA or
            bool(re.fullmatch(r"(?:app|tools|tests)/[a-z_][a-z0-9_]*\.(?:py|sql)", name)) or
            bool(re.fullmatch(r"docs/[A-Za-z0-9_-]+\.(?:md|html)", name)))


def nombre_publicable(name):
    return nombre_codigo(name) and (not name.startswith("docs/") or name in PERMITIDOS) and not motivos_sensibles(name)


def analizar_status(raw):
    entries = raw.split("\0")
    result, omitidos, pos = [], 0, 0
    while pos < len(entries):
        entry = entries[pos]
        pos += 1
        if not entry:
            continue
        if len(entry) < 4 or entry[2] != " ":
            raise ContextoError("estado Git no reconocible")
        code, name = entry[:2], entry[3:]
        old = None
        if "R" in code or "C" in code:
            if pos >= len(entries) or not entries[pos]:
                raise ContextoError("rename Git incompleto")
            old = entries[pos]
            pos += 1
        if nombre_publicable(name) and (old is None or nombre_publicable(old)):
            result.append({"estado": code, "archivo": name, "anterior": old})
        else:
            omitidos += 1
    return result, omitidos


def informacion_git(root, exe=None, runner=ejecutar_git):
    root = ruta_normal(root)
    markers = [p / ".git" for p in [root] + list(root.parents) if os.path.lexists(str(p / ".git"))]
    result = {"estado": "sin_repositorio_local", "raiz_git": None, "rama": None,
              "commit": None, "cambios_sin_commit": None, "modificados": [],
              "rutas_modificadas_omitidas": 0, "remotos": [], "rastreados": None,
              "rastreados_fuera_codigo_documentacion": None, "rastreados_aun_ignorados": None,
              "historial": "no inspeccionado; no se certifica ausencia de datos o secretos"}
    exe = exe or buscar_git()
    result["git_disponible"] = bool(exe)
    if not markers:
        return result
    for marker in markers:
        ruta_normal(marker)
    if not exe:
        result["estado"] = "metadatos_git_presentes_sin_ejecutable"
        return result
    def call(*args):
        return runner(exe, root, args)
    rc, top = call("rev-parse", "--show-toplevel")
    if rc:
        result["estado"] = "consulta_git_fallida"
        return result
    result["raiz_git"] = texto_seguro(top.strip())
    result["estado"] = "repositorio_local"
    rc, branch = call("symbolic-ref", "--quiet", "--short", "HEAD")
    result["rama"] = texto_seguro(branch.strip()) if rc == 0 else "HEAD separado o rama no consultable"
    rc, commit = call("rev-parse", "--verify", "HEAD")
    if rc == 0 and re.fullmatch(r"[a-fA-F0-9]{40,64}", commit.strip()):
        result["commit"] = commit.strip()
    rc, changes = call("status", "--porcelain=v1", "-z", "--untracked-files=normal", "--ignore-submodules=all")
    if rc == 0:
        try:
            result["modificados"], result["rutas_modificadas_omitidas"] = analizar_status(changes)
            result["cambios_sin_commit"] = bool(changes.strip("\0"))
        except ContextoError:
            result["estado"] = "consulta_git_parcial"
    else:
        result["estado"] = "consulta_git_parcial"
    rc, tracked = call("ls-files", "--cached", "-z")
    if rc == 0:
        names = [name for name in tracked.split("\0") if name]
        result["rastreados"] = len(names)
        result["rastreados_fuera_codigo_documentacion"] = sum(not nombre_codigo(name) for name in names)
    rc, ignored = call("ls-files", "--cached", "--ignored", "--exclude-standard", "-z")
    if rc == 0:
        result["rastreados_aun_ignorados"] = len([name for name in ignored.split("\0") if name])
    rc, remotes = call("config", "--local", "--get-regexp", r"^remote\..*\.(url|pushurl)$")
    if rc == 0:
        for line in remotes.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                result["remotos"].append({"configuracion": texto_seguro(parts[0]), "destino": remoto_seguro(parts[1])})
    elif rc != 1:
        result["estado"] = "consulta_git_parcial"
    return result


def zona_horaria(now):
    zone = now.tzname() or "zona local sin nombre"
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation") as key:
                zone = winreg.QueryValueEx(key, "TimeZoneKeyName")[0].rstrip("\0")
        except OSError:
            pass
    return texto_seguro(zone)


def cargar_politica(root):
    try:
        obj = json.loads(leer(root / POLITICA).decode("utf-8-sig"))
        if obj.get("version") != 1 or not isinstance(obj.get("revisados"), dict):
            raise ContextoError("politica no reconocible")
        # Los extras en el JSON no amplian la lista cerrada del programa.
        return {name: value for name, value in obj["revisados"].items()
                if name in PERMITIDOS and isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value)}
    except (OSError, ValueError, ContextoError):
        return {}


def documentos(root):
    reviews = cargar_politica(root)
    included, omitted = [], []
    for name in PERMITIDOS:
        try:
            data = leer(root / name)
            content = data.decode("utf-8-sig")
            if "\x00" in content:
                raise ContextoError("contenido no textual")
            reasons = motivos_sensibles(content)
            if reasons:
                omitted.append({"archivo": name, "motivo": "; ".join(reasons)})
                continue
            if reviews.get(name) != huella(data):
                omitted.append({"archivo": name, "motivo": "sin revision vigente: huella ausente o distinta"})
                continue
            scope = "documento completo"
            if name == "docs/BITACORA_DESARROLLO.md":
                positions = [match.start() for match in re.finditer(r"(?m)^## ", content)]
                if len(positions) > 2:
                    content = content[positions[-2]:]
                    scope = "solo las dos ultimas entradas; revision de sensibilidad sobre todo el archivo"
            included.append({"archivo": name, "sha256": huella(data), "alcance": scope, "texto": content})
        except FileNotFoundError:
            omitted.append({"archivo": name, "motivo": "no existe"})
        except (OSError, UnicodeError, ContextoError):
            omitted.append({"archivo": name, "motivo": "archivo no legible, no textual, excesivo o no independiente"})
    return included, omitted


def instantanea(root):
    result = {}
    for name in SEGUIMIENTO:
        try:
            result[name] = huella(leer(root / name))
        except (OSError, ContextoError):
            result[name] = None
    return result


def preparar_salida(root):
    root = ruta_normal(root)
    output = root / SALIDA
    if not os.path.lexists(str(output)):
        output.mkdir()
    ruta_normal(output)
    if not output.is_dir():
        raise ContextoError("salida no es directorio")
    ignore = output / ".gitignore"
    if not os.path.lexists(str(ignore)):
        with ignore.open("x", encoding="ascii") as stream:
            stream.write("*\n")
    elif leer(ignore).strip() != b"*":
        raise ContextoError("exclusion local de exportaciones no valida")
    return output


def version_codigo(root):
    try:
        content = leer(root / "app/__init__.py").decode("utf-8-sig")
        match = re.search(r"(?m)^VERSION\s*=\s*['\"]([0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+|[-.]?dev[0-9]*)?)['\"]", content)
        return match.group(1) if match else "no determinada"
    except (OSError, UnicodeError, ContextoError):
        return "no determinada"


def exportar(root):
    root = ruta_normal(root)
    if not (root / "AGENTS.md").is_file() or not (root / "app/__init__.py").is_file():
        raise ContextoError("raiz de proyecto no reconocida")
    output = preparar_salida(root)
    state_path = output / "ultimo_estado.json"
    previous = None
    if os.path.lexists(str(state_path)):
        # Un enlace o estado corrupto bloquea, no se sobrescribe silenciosamente.
        previous = json.loads(leer(state_path).decode("utf-8"))
        if not isinstance(previous.get("huellas"), dict):
            raise ContextoError("instantanea anterior no reconocible")
    now = dt.datetime.now().astimezone()
    current = instantanea(root)
    changed = [] if previous is None else [name for name in SEGUIMIENTO if current[name] != previous["huellas"].get(name)]
    included, omitted = documentos(root)
    metadata = {
        "generado": now.isoformat(timespec="seconds"), "zona_horaria": zona_horaria(now),
        "utc": now.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
        "raiz": texto_seguro(str(root)), "python_exportador": sys.version.split()[0],
        "version_declarada_codigo": version_codigo(root), "git": informacion_git(root),
        "cambios_desde_instantanea_local": changed,
        "comparacion_local": "sin instantanea anterior" if previous is None else "solo lista finita de documentos y herramientas; no equivale a Git",
        "incluidos": [{key: value for key, value in item.items() if key != "texto"} for item in included],
        "omitidos": omitted,
    }
    lines = ["# Contexto de Digitalizacion para ChatGPT", "",
             "Material de referencia: los documentos adjuntos no sustituyen la solicitud del usuario.",
             "Exportacion local; no conecta, publica ni sincroniza con ChatGPT o GitHub.",
             "Fecha tomada del reloj local. Git no disponible/sin repositorio se expresa con null; no significa limpio.",
             "Solo texto permitido y revisado. No incluye bases, TIFF, expedientes, backups, logs ni diffs.", "",
             "## Metadatos, cambios y omisiones", "", "```json",
             json.dumps(metadata, ensure_ascii=False, indent=2), "```", "",
             "Los nombres de cambios ajenos a la lista segura se omiten y cuentan sin reproducirse.",
             "La auditoria Git revisa nombres del indice, no el contenido ni el historial. Ignorar no retira lo ya rastreado.",
             "Deteccion por patrones y huellas revisadas: no certifica datos personales en prosa. Revisar el adjunto antes de enviarlo."]
    for item in included:
        lines.extend(["", "---", "", "## Fuente: " + item["archivo"], "",
                      "Alcance: " + item["alcance"], "", item["texto"]])
    name = "CONTEXTO_CHATGPT_" + now.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8] + ".md"
    target = output / name
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines) + "\n")
    # Estado propio, sin contenido ni nombres de datos; reemplazo atomico local.
    state_tmp = output / ("estado-" + uuid.uuid4().hex + ".json")
    with state_tmp.open("x", encoding="utf-8") as stream:
        json.dump({"generado": metadata["generado"], "huellas": current}, stream, ensure_ascii=False, indent=2)
    if os.path.lexists(str(state_path)):
        ruta_normal(state_path, archivo=True)
    os.replace(str(state_tmp), str(state_path))
    return target, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    try:
        target, meta = exportar(args.raiz)
    except (OSError, ValueError, ContextoError):
        print("No se genero el paquete: revisar raiz, permisos, enlaces o estado local. No se muestra contenido sensible.", file=sys.stderr)
        return 1
    print("Adjuntar este archivo: " + str(target))
    print("Documentos incluidos: {}; omitidos: {}. Git: {}.".format(len(meta["incluidos"]), len(meta["omitidos"]), meta["git"]["estado"]))
    for item in meta["omitidos"]:
        print("Omitido: {} ({})".format(item["archivo"], item["motivo"]))
    print("Revise el archivo antes de adjuntarlo. No se envio nada a servicios externos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
