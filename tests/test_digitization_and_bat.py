import tempfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.digitization.models import (
    AssetStatus,
    BatRowStatus,
    DigitalAsset,
    DigitalPage,
    DocumentType,
    ScanMode,
)
from apps.digitization.services import (
    create_digital_asset,
    create_digital_document,
    import_bat_csv,
    inventory_record_tiffs,
    record_reconciliation,
)
from apps.records.services import assign_record, register_physical_count

from .helpers import initialize_reference_data, make_batch_record, user_in_role

BAT_HEADER = (
    "CURP;FECHA;HORA;DIGITALIZADOR;FISICOS;DIGITALES;INDIVIDUALES;MULTI;"
    "PERSONALES;FEDERAL;TIFF_RAIZ_CURP;DP;FP;HL;MOVIDOS_EJECUCION;CONFLICTOS;"
    "ERRORES;TIFF_SUELTOS;OTROS_DESTINO;RESULTADO\n"
)


class DigitizationAndBatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        initialize_reference_data()
        cls.supervisor = user_in_role("supervisor_digital", "Responsables de digitalización")
        cls.digitalizer = user_in_role("digitalizador_digital", "Digitalizadores")

    def setUp(self):
        self.batch, self.record = make_batch_record(suffix="F", responsible=self.supervisor)
        assign_record(record_id=self.record.pk, digitalizer=self.digitalizer, actor=self.supervisor)

    def test_page_count_never_determines_individual_or_multi(self):
        individual_doc = create_digital_document(
            record_id=self.record.pk,
            actor=self.digitalizer,
            document_type=DocumentType.objects.get(code="DP"),
            scan_mode=ScanMode.INDIVIDUAL_DUPLEX,
            other_mode_description="",
            sequence=1,
        )
        multi_doc = create_digital_document(
            record_id=self.record.pk,
            actor=self.digitalizer,
            document_type=DocumentType.objects.get(code="HL"),
            scan_mode=ScanMode.MULTI_ONE_SIDE,
            other_mode_description="",
            sequence=2,
        )
        individual_asset = create_digital_asset(
            record_id=self.record.pk,
            actor=self.digitalizer,
            document=individual_doc,
            filename="DP-01.tif",
            relative_path=f"{self.record.person.curp}/PERSONALES/DP-01.tif",
            extension="tif",
            file_size=10,
            sha256="",
            page_count=2,
        )
        create_digital_asset(
            record_id=self.record.pk,
            actor=self.digitalizer,
            document=multi_doc,
            filename="HL-01.tif",
            relative_path=f"{self.record.person.curp}/FEDERAL/HL-01.tif",
            extension="tif",
            file_size=20,
            sha256="",
            page_count=1,
        )
        DigitalPage.objects.create(asset=individual_asset, page_number=1)
        DigitalPage.objects.create(asset=individual_asset, page_number=2)
        checks = record_reconciliation(self.record)
        modality = checks["individual_plus_multi_equals_digital_total"]
        self.assertEqual((modality["individual"], modality["multi"]), (1, 1))
        self.assertTrue(modality["ok"])
        register_physical_count(record_id=self.record.pk, sheet_count=25, actor=self.digitalizer)
        self.assertEqual(self.record.latest_physical_count.sheet_count, 25)
        self.assertEqual(self.record.digital_assets.count(), 2)
        self.assertEqual(individual_asset.pages.count(), 2)

    def test_read_only_inventory_detects_prefix_folders_unexpected_and_hashes(self):
        with tempfile.TemporaryDirectory() as root:
            record_root = Path(root) / self.record.person.curp
            (record_root / "PERSONALES").mkdir(parents=True)
            (record_root / "FEDERAL").mkdir()
            (record_root / "PERSONALES" / "DP-01.tif").write_bytes(b"synthetic-tiff-a")
            (record_root / "FEDERAL" / "HL-01.tiff").write_bytes(b"synthetic-tiff-b")
            (record_root / "OTRO.tif").write_bytes(b"synthetic-tiff-c")
            with override_settings(DIGITAL_REPOSITORY_ROOT=root):
                run = inventory_record_tiffs(
                    record_id=self.record.pk,
                    actor=self.supervisor,
                    compute_hashes=True,
                )
                self.assertEqual((run.discovered_count, run.unexpected_count), (3, 1))
                self.assertTrue((record_root / "PERSONALES" / "DP-01.tif").exists())
                self.assertEqual(DigitalAsset.objects.filter(record=self.record).count(), 3)
                self.assertEqual(
                    DigitalAsset.objects.get(filename="OTRO.tif").status,
                    AssetStatus.UNEXPECTED,
                )
                self.assertEqual(len(DigitalAsset.objects.get(filename="DP-01.tif").sha256), 64)
                with self.assertRaises(ValidationError):
                    inventory_record_tiffs(
                        record_id=self.record.pk,
                        actor=self.supervisor,
                        relative_folder="../fuera",
                    )

    def test_bat_import_valid_discrepancy_duplicate_invalid_and_unknown_curp(self):
        register_physical_count(record_id=self.record.pk, sheet_count=10, actor=self.digitalizer)
        valid_row = (
            f"{self.record.person.curp};06/09/2026;10:00:00;Operador;11;2;1;1;1;1;0;1;0;1;2;0;0;0;0;OK\n"
        )
        content = (BAT_HEADER + valid_row).encode("utf-8")
        uploaded = SimpleUploadedFile("CONTROL_DIGITALIZACION.csv", content, content_type="text/csv")
        imported = import_bat_csv(batch_id=self.batch.pk, uploaded_file=uploaded, actor=self.supervisor)
        row = imported.rows.get()
        self.assertEqual(row.status, BatRowStatus.DISCREPANCY)
        self.assertEqual(row.discrepancies[0]["code"], "physical_count_mismatch")

        with self.assertRaises(ValidationError):
            import_bat_csv(
                batch_id=self.batch.pk,
                uploaded_file=SimpleUploadedFile("copia.csv", content),
                actor=self.supervisor,
            )

        unknown = "TESTZ000000AAAAA01;06/09/2026;11:00:00;Operador;1;2;1;1;1;1;0;1;0;1;2;0;0;0;0;REVISAR\n"
        second = import_bat_csv(
            batch_id=self.batch.pk,
            uploaded_file=SimpleUploadedFile("otro.csv", (BAT_HEADER + unknown).encode("utf-8")),
            actor=self.supervisor,
        )
        self.assertEqual(second.rows.get().status, BatRowStatus.ERROR)
        self.assertIn("no existe", second.rows.get().errors[-1])

        invalid_counts = (
            f"{self.record.person.curp};06/09/2026;12:00:00;Operador;1;3;1;1;1;2;0;1;0;2;3;0;0;0;0;REVISAR\n"
        )
        third = import_bat_csv(
            batch_id=self.batch.pk,
            uploaded_file=SimpleUploadedFile(
                "conteos_invalidos.csv", (BAT_HEADER + invalid_counts).encode("utf-8")
            ),
            actor=self.supervisor,
        )
        self.assertEqual(third.rows.get().status, BatRowStatus.ERROR)
        self.assertIn("INDIVIDUALES + MULTI", third.rows.get().errors[0])
