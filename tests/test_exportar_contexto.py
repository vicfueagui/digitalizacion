"""Fixtures ficticios confinados; Git simulado cuando no hay ejecutable local."""
import datetime
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location("exportador", Path(__file__).resolve().parents[1] / "tools/exportar_contexto.py")
ex = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ex)


class ExportacionTests(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get("CONTEXTO_TEST_DIR")
        if not parent:
            raise RuntimeError("Fijar CONTEXTO_TEST_DIR a una carpeta sintetica nueva")
        self.temp = tempfile.TemporaryDirectory(dir=parent, prefix="fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("AGENTS.md", "# Reglas ficticias\nPreservar datos.\n")
        self.write("app/__init__.py", "VERSION = '0.6.2'\nraise RuntimeError('No importar la aplicacion')\n")
        self.write("CONTEXTO_CHATGPT.md", "# Estado ficticio\nSolo contexto tecnico.\n")
        self.approve()
        self.patcher = mock.patch.object(ex, "buscar_git", return_value=None)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode("utf-8"))
        return path

    def approve(self, extra=None):
        hashes = {name: ex.huella((self.root / name).read_bytes()) for name in ex.PERMITIDOS if (self.root / name).is_file()}
        hashes.update(extra or {})
        self.write(ex.POLITICA, json.dumps({"version": 1, "revisados": hashes}))

    def test_lista_cerrada_no_abre_datos_ni_fuentes_privadas(self):
        forbidden = ["datos/privado.sqlite3", "datos/expediente.tiff", "respaldos/copias.db",
                     "fuentes/personas.csv", ".env", ".venv/secreto.txt", "logs/operacion.log",
                     "docs/no_permitido.md"]
        for name in forbidden:
            self.write(name, "CONTENIDO_FICTICIO_NO_COMPARTIR")
        # README participa solo en la lista explicita de huellas, no en contenido.
        self.write("README.md", "CONTENIDO_FICTICIO_NO_COMPARTIR")
        original = ex.leer
        def confined(path):
            self.assertNotIn(Path(path).relative_to(self.root).as_posix(), forbidden)
            return original(path)
        with mock.patch.object(ex, "leer", side_effect=confined):
            target, metadata = ex.exportar(self.root)
        content = target.read_text(encoding="utf-8")
        self.assertNotIn("CONTENIDO_FICTICIO_NO_COMPARTIR", content)
        self.assertEqual(len(metadata["incluidos"]), 2)
        self.assertEqual(metadata["version_declarada_codigo"], "0.6.2")

    def test_sensible_se_omite_aun_con_huella_autorizada(self):
        examples = ["password = clave_ficticia", "persona@example.invalid", "Nombre completo: Persona Ficticia",
                    "GODE900101HDFXXX09", "https://usuario:clave@example.invalid/repo",
                    "github_pat_" + "z" * 28, "-----BEGIN PRIVATE KEY-----", "CONTEXTO_PRIVADO",
                    "C:\\Users\\PersonaFicticia\\secreto", "telefono: 5512345678"]
        for value in examples:
            with self.subTest(categoria=examples.index(value)):
                self.write("CONTEXTO_CHATGPT.md", value)
                self.approve()
                included, omitted = ex.documentos(self.root)
                self.assertNotIn("CONTEXTO_CHATGPT.md", [item["archivo"] for item in included])
                self.assertIn("CONTEXTO_CHATGPT.md", [item["archivo"] for item in omitted])
                self.assertNotIn(value, json.dumps(omitted))

    def test_version_candidata_sin_ejecutar_codigo(self):
        for version in ('0.8.0rc1','0.8.1-dev','0.8.1.dev2','0.8.1'):
            with self.subTest(version=version):
                self.write('app/__init__.py',"VERSION = '"+version+"'\nraise RuntimeError('No ejecutar')\n")
                self.assertEqual(ex.version_codigo(self.root),version)

    def test_prosa_nueva_sin_revision_no_sale(self):
        self.write("CONTEXTO_CHATGPT.md", "En una narracion aparece Persona Ficticia sin campo ni identificador.")
        target, metadata = ex.exportar(self.root)
        self.assertNotIn("Persona Ficticia", target.read_text(encoding="utf-8"))
        self.assertTrue(any("huella" in item["motivo"] for item in metadata["omitidos"]))

    def test_politica_no_puede_ampliar_lista_o_escapar(self):
        self.write(".env", "DATO_FICTICIO")
        self.approve({".env": ex.huella(b"DATO_FICTICIO"), "../externo.md": "a" * 64})
        self.assertNotIn(".env", ex.cargar_politica(self.root))
        self.assertNotIn("../externo.md", ex.cargar_politica(self.root))

    def test_politica_corrupta_no_autoriza_documentos(self):
        self.write(ex.POLITICA, "{incompleto")
        included, omitted = ex.documentos(self.root)
        self.assertEqual(included, [])
        self.assertEqual(len(omitted), len(ex.PERMITIDOS))

    def test_binario_utf8_invalido_y_excesivo_se_omiten(self):
        for data in [b"abc\x00def", b"\xff\xfe\xfd", b"a" * (ex.MAX_BYTES + 1)]:
            self.write("CONTEXTO_CHATGPT.md", data)
            self.approve()
            included, omitted = ex.documentos(self.root)
            self.assertNotIn("CONTEXTO_CHATGPT.md", [item["archivo"] for item in included])
            self.assertEqual(len(omitted), len(ex.PERMITIDOS) - 1)

    def test_bitacora_dos_entradas_sin_volcado_completo(self):
        self.write("docs/BITACORA_DESARROLLO.md", "# Bitacora\n## vieja\nNO_INCLUIR_ESTA_ENTRADA\n## reciente\nuno\n## ultima\ndos\n")
        self.approve()
        included, _ = ex.documentos(self.root)
        item = next(item for item in included if "BITACORA" in item["archivo"])
        self.assertNotIn("NO_INCLUIR_ESTA_ENTRADA", item["texto"])
        self.assertIn("## reciente", item["texto"])

    def test_bitacora_sensible_antigua_omite_todo_documento(self):
        self.write("docs/BITACORA_DESARROLLO.md", "## vieja\npersona@example.invalid\n## reciente\nuno\n## ultima\ndos\n")
        self.approve()
        included, omitted = ex.documentos(self.root)
        self.assertNotIn("docs/BITACORA_DESARROLLO.md", [item["archivo"] for item in included])
        self.assertTrue(any(item["motivo"] == "correo electronico" for item in omitted))

    def test_sin_git_no_se_declara_limpio_y_compara_instantaneas(self):
        first, metadata = ex.exportar(self.root)
        self.assertIsNone(metadata["git"]["cambios_sin_commit"])
        self.assertIsNone(metadata["git"]["rama"])
        self.assertIsNone(metadata["git"]["commit"])
        self.assertEqual(metadata["comparacion_local"], "sin instantanea anterior")
        self.write("AGENTS.md", "# Regla ficticia actualizada\n")
        second, metadata = ex.exportar(self.root)
        self.assertNotEqual(first, second)
        self.assertEqual(metadata["cambios_desde_instantanea_local"], ["AGENTS.md"])
        self.assertIsNone(metadata["git"]["cambios_sin_commit"])

    def test_fecha_zona_y_utc_presentes(self):
        _, metadata = ex.exportar(self.root)
        self.assertIsNotNone(datetime.datetime.fromisoformat(metadata["generado"]).utcoffset())
        self.assertTrue(metadata["zona_horaria"])
        self.assertTrue(metadata["utc"].endswith("+00:00"))

    def test_fuentes_intactas_y_salida_separada_con_ignore(self):
        before = ex.instantanea(self.root)
        target, _ = ex.exportar(self.root)
        self.assertEqual(before, ex.instantanea(self.root))
        self.assertEqual(target.parent, self.root / ex.SALIDA)
        self.assertEqual((target.parent / ".gitignore").read_text().strip(), "*")

    def test_estado_corrupto_no_sobrescribe(self):
        folder = ex.preparar_salida(self.root)
        bad = folder / "ultimo_estado.json"
        bad.write_text("corrupto", encoding="utf-8")
        with self.assertRaises(ValueError):
            ex.exportar(self.root)
        self.assertEqual(bad.read_text(), "corrupto")
        self.assertEqual(list(folder.glob("*.md")), [])

    def test_hardlink_de_documento_rechazado(self):
        source = self.write("documento_ficticio.txt", "# Contexto ficticio")
        target = self.root / "docs/PLAN_MODERNIZACION.md"
        target.parent.mkdir(exist_ok=True)
        os.link(str(source), str(target))
        self.approve()
        included, omitted = ex.documentos(self.root)
        self.assertNotIn("docs/PLAN_MODERNIZACION.md", [item["archivo"] for item in included])
        self.assertTrue(any(item["archivo"] == "docs/PLAN_MODERNIZACION.md" for item in omitted))

    def test_reparse_point_simulado_impide_exportar(self):
        output = ex.preparar_salida(self.root)
        actual = Path.lstat
        def simulated(path):
            if path == output:
                return types.SimpleNamespace(st_mode=0o040755, st_file_attributes=0x400)
            return actual(path)
        with mock.patch.object(Path, "lstat", simulated):
            with self.assertRaises(ex.ContextoError):
                ex.exportar(self.root)
        self.assertEqual(list(output.glob("*.md")), [])

    def test_salida_con_ignore_distinto_no_se_reescribe(self):
        folder = ex.preparar_salida(self.root)
        (folder / ".gitignore").write_text("!*.md", encoding="ascii")
        with self.assertRaises(ex.ContextoError):
            ex.exportar(self.root)
        self.assertEqual((folder / ".gitignore").read_text(), "!*.md")

    def git_runner(self, overrides=None):
        outputs = {
            ("rev-parse", "--show-toplevel"): (0, str(self.root) + "\n"),
            ("symbolic-ref", "--quiet", "--short", "HEAD"): (0, "respaldo/digitalizacion-tk-0.6.3\n"),
            ("rev-parse", "--verify", "HEAD"): (0, "a" * 40 + "\n"),
            ("status", "--porcelain=v1", "-z", "--untracked-files=normal", "--ignore-submodules=all"): (0, " M app/core.py\0?? datos/persona_ficticia.tiff\0"),
            ("ls-files", "--cached", "-z"): (0, "app/core.py\0datos/persona_ficticia.tiff\0.env\0"),
            ("ls-files", "--cached", "--ignored", "--exclude-standard", "-z"): (0, "datos/persona_ficticia.tiff\0.env\0"),
            ("config", "--local", "--get-regexp", r"^remote\..*\.(url|pushurl)$"): (0, "remote.origin.url https://usuario:clave_ficticia@github.com/ejemplo/proyecto.git?token=valor_ficticio_923#privado\n"),
        }
        outputs.update(overrides or {})
        def runner(exe, root, args):
            return outputs[tuple(args)]
        return runner

    def test_git_rama_commit_cambios_rastreados_y_remoto_sin_secretos(self):
        (self.root / ".git").mkdir()
        result = ex.informacion_git(self.root, exe="git-ficticio", runner=self.git_runner())
        self.assertEqual(result["rama"], "respaldo/digitalizacion-tk-0.6.3")
        self.assertEqual(result["commit"], "a" * 40)
        self.assertTrue(result["cambios_sin_commit"])
        self.assertEqual(result["modificados"][0]["archivo"], "app/core.py")
        self.assertEqual(result["rutas_modificadas_omitidas"], 1)
        self.assertEqual(result["rastreados_fuera_codigo_documentacion"], 2)
        self.assertEqual(result["rastreados_aun_ignorados"], 2)
        rendered = json.dumps(result)
        for forbidden in ("clave_ficticia", "valor_ficticio_923", "persona_ficticia", "?token=", "usuario:"):
            self.assertNotIn(forbidden, rendered)

    def test_git_head_separado(self):
        (self.root / ".git").mkdir()
        result = ex.informacion_git(self.root, exe="git-ficticio", runner=self.git_runner({
            ("symbolic-ref", "--quiet", "--short", "HEAD"): (1, "")}))
        self.assertIn("HEAD separado", result["rama"])
        self.assertEqual(result["commit"], "a" * 40)

    def test_git_sin_primer_commit(self):
        (self.root / ".git").mkdir()
        result = ex.informacion_git(self.root, exe="git-ficticio", runner=self.git_runner({
            ("rev-parse", "--verify", "HEAD"): (128, "")}))
        self.assertIsNone(result["commit"])
        self.assertEqual(result["rama"], "respaldo/digitalizacion-tk-0.6.3")

    def test_git_error_status_no_equivale_a_limpio(self):
        (self.root / ".git").mkdir()
        result = ex.informacion_git(self.root, exe="git-ficticio", runner=self.git_runner({
            ("status", "--porcelain=v1", "-z", "--untracked-files=normal", "--ignore-submodules=all"): (128, "")}))
        self.assertIsNone(result["cambios_sin_commit"])
        self.assertEqual(result["estado"], "consulta_git_parcial")

    def test_git_presente_sin_ejecutable_no_inventa_estado(self):
        (self.root / ".git").mkdir()
        result = ex.informacion_git(self.root)
        self.assertEqual(result["estado"], "metadatos_git_presentes_sin_ejecutable")
        self.assertIsNone(result["cambios_sin_commit"])

    def test_renames_nombres_con_espacios_y_privados(self):
        result, omitted = ex.analizar_status("R  app/nuevo.py\0app/viejo.py\0?? docs/persona ficticia.md\0?? .env\0")
        self.assertEqual(result, [{"estado": "R ", "archivo": "app/nuevo.py", "anterior": "app/viejo.py"}])
        self.assertEqual(omitted, 2)

    def test_remotos_scp_local_y_url_credenciales(self):
        self.assertEqual(ex.remoto_seguro("git@github.com:ejemplo/proyecto.git"), "https://github.com/ejemplo/proyecto.git")
        self.assertNotIn("PersonaFicticia", ex.remoto_seguro("C:\\Users\\PersonaFicticia\\repositorio"))
        self.assertEqual(ex.remoto_seguro("ssh://usuario:clave@servidor.invalid/ruta?secret=valor"), "servidor.invalid/[ruta omitida]")


if __name__ == "__main__":
    unittest.main()
