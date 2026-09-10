import tempfile
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from openpyxl import Workbook

from apps.batches.services import (
    attach_source_import,
    batch_reconciliation,
    materialize_records_from_source,
)
from apps.people.models import EmploymentStatus, Person
from apps.sources.models import SourceRowStatus
from apps.sources.services import import_payroll_xlsx

from .helpers import initialize_reference_data, make_batch_record, user_in_role


def workbook_bytes(rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Datos"
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def mapping():
    return {
        "sheet_name": "Datos",
        "header_row": 1,
        "curp": "CURP",
        "name": "NOMBRE",
        "employment_status": "ESTADO",
        "systems": "SISTEMA",
        "federal_flag": "",
        "state_flag": "",
        "federal_values": ["Federal"],
        "state_values": ["Estatal"],
        "active_values": ["Vigente"],
        "inactive_values": ["Baja"],
    }


class ExcelImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        initialize_reference_data()
        cls.supervisor = user_in_role("supervisor_excel", "Responsables de digitalización")

    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.temp_media.cleanup()

    def _uploaded(self, content, name="nomina_sintetica.xlsx"):
        return SimpleUploadedFile(
            name,
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_valid_rows_errors_duplicates_and_systems_are_auditable(self):
        content = workbook_bytes(
            [
                ["CURP", "NOMBRE", "SISTEMA", "ESTADO"],
                ["TESTA000000AAAAA01", "Persona A", "Federal/Estatal", "Vigente"],
                ["TESTA000000AAAAA01", "Persona A", "Federal/Estatal", "Vigente"],
                ["", "Sin CURP", "Federal", "Vigente"],
            ]
        )
        imported = import_payroll_xlsx(
            uploaded_file=self._uploaded(content), mapping=mapping(), actor=self.supervisor
        )
        self.assertEqual((imported.row_count, imported.accepted_rows, imported.error_rows), (3, 1, 2))
        self.assertEqual(imported.rows.filter(status=SourceRowStatus.ERROR).count(), 2)
        person = Person.objects.get(curp="TESTA000000AAAAA01")
        self.assertEqual(person.employment_status, EmploymentStatus.ACTIVE)
        self.assertSetEqual(set(person.systems.values_list("code", flat=True)), {"FEDERAL", "ESTATAL"})
        self.assertTrue(imported.rows.get(row_number=2).raw_payload)
        self.assertEqual(len(imported.sha256), 64)

        with self.assertRaises(ValidationError):
            import_payroll_xlsx(
                uploaded_file=self._uploaded(content, "copia.xlsx"), mapping=mapping(), actor=self.supervisor
            )

    def test_batch_materialization_and_reconciliation_preserve_source_row(self):
        content = workbook_bytes(
            [["CURP", "NOMBRE", "SISTEMA", "ESTADO"], ["TESTB000000AAAAA01", "Persona B", "Federal", "Vigente"]]
        )
        imported = import_payroll_xlsx(
            uploaded_file=self._uploaded(content), mapping=mapping(), actor=self.supervisor
        )
        batch, placeholder = make_batch_record(suffix="X", responsible=self.supervisor)
        placeholder.delete()
        attach_source_import(batch_id=batch.pk, source_import=imported, actor=self.supervisor)
        created, existing = materialize_records_from_source(batch_id=batch.pk, actor=self.supervisor)
        batch.refresh_from_db()
        self.assertEqual((created, existing), (1, 0))
        record = batch.records.get()
        self.assertEqual(record.source_row.payroll_import, imported)
        result = batch_reconciliation(batch)
        self.assertTrue(result["source_matches"])

    def test_missing_configured_header_is_rejected(self):
        content = workbook_bytes([["OTRA", "NOMBRE"], ["valor", "Persona"]])
        with self.assertRaises(ValidationError):
            import_payroll_xlsx(
                uploaded_file=self._uploaded(content), mapping=mapping(), actor=self.supervisor
            )

    def test_contradictory_system_columns_create_a_warning_not_a_silent_choice(self):
        content = workbook_bytes(
            [
                ["CURP", "NOMBRE", "SISTEMA", "ESTADO", "ESTATAL_FLAG"],
                ["TESTC000000AAAAA01", "Persona C", "Federal", "Vigente", "Sí"],
            ]
        )
        configured = mapping()
        configured["state_flag"] = "ESTATAL_FLAG"
        configured["state_values"] = ["Estatal", "Sí"]
        imported = import_payroll_xlsx(
            uploaded_file=self._uploaded(content, "contradiccion.xlsx"),
            mapping=configured,
            actor=self.supervisor,
        )
        row = imported.rows.get()
        self.assertEqual(row.status, SourceRowStatus.WARNING)
        self.assertIn("contradictorios", row.warnings[0])
        self.assertSetEqual(set(row.systems_payload), {"FEDERAL", "ESTATAL"})
