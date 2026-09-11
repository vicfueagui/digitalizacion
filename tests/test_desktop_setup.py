import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from scripts.prepare_local_env import ensure_local_env


class LocalEnvironmentSetupTests(SimpleTestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temporary_directory.name)
        self.example_path = self.project_dir / ".env.example"
        self.example_path.write_text(
            "DJANGO_DEBUG=True\n"
            "DJANGO_SECRET_KEY=cambie-esta-clave-en-produccion\n"
            "DB_ENGINE=sqlite\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_creates_env_with_random_secret_and_preserves_configuration(self):
        changed = ensure_local_env(self.project_dir)

        content = (self.project_dir / ".env").read_text(encoding="utf-8")
        self.assertTrue(changed)
        self.assertIn("DJANGO_DEBUG=True", content)
        self.assertIn("DB_ENGINE=sqlite", content)
        self.assertNotIn("cambie-esta-clave-en-produccion", content)
        secret_line = next(line for line in content.splitlines() if line.startswith("DJANGO_SECRET_KEY="))
        self.assertGreater(len(secret_line.partition("=")[2]), 50)

    def test_preserves_existing_non_placeholder_secret(self):
        env_path = self.project_dir / ".env"
        original = "DJANGO_DEBUG=True\nDJANGO_SECRET_KEY=clave-local-personalizada-y-segura\n"
        env_path.write_text(original, encoding="utf-8")

        changed = ensure_local_env(self.project_dir)

        self.assertFalse(changed)
        self.assertEqual(env_path.read_text(encoding="utf-8"), original)

    def test_replaces_placeholder_in_existing_env(self):
        env_path = self.project_dir / ".env"
        env_path.write_text(self.example_path.read_text(encoding="utf-8"), encoding="utf-8")

        changed = ensure_local_env(self.project_dir)

        self.assertTrue(changed)
        self.assertNotIn(
            "cambie-esta-clave-en-produccion",
            env_path.read_text(encoding="utf-8"),
        )
