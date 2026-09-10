from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ImportStatus(models.TextChoices):
    PROCESSING = "PROCESSING", "Procesando"
    COMPLETED = "COMPLETED", "Completada"
    COMPLETED_WITH_ERRORS = "WITH_ERRORS", "Completada con errores"
    FAILED = "FAILED", "Fallida"


class SourceRowStatus(models.TextChoices):
    ACCEPTED = "ACCEPTED", "Aceptada"
    WARNING = "WARNING", "Aceptada con advertencias"
    ERROR = "ERROR", "Con error"


class PayrollImport(TimeStampedModel):
    source_file = models.FileField(upload_to="source_imports/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, unique=True)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payroll_imports",
    )
    imported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=ImportStatus.choices,
        default=ImportStatus.PROCESSING,
    )
    row_count = models.PositiveIntegerField(default=0)
    accepted_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    warning_rows = models.PositiveIntegerField(default=0)
    column_mapping = models.JSONField(default=dict)
    warnings = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ("-imported_at",)
        verbose_name = "importación de Nóminas"
        verbose_name_plural = "importaciones de Nóminas"
        permissions = [
            ("import_payroll", "Puede importar archivos oficiales de Nóminas"),
            ("reconcile_payroll", "Puede conciliar fuente oficial y expedientes"),
        ]

    def __str__(self):
        return f"{self.original_filename} · {self.imported_at:%Y-%m-%d %H:%M}"


class PayrollSourceRow(models.Model):
    payroll_import = models.ForeignKey(
        PayrollImport,
        on_delete=models.PROTECT,
        related_name="rows",
    )
    row_number = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=SourceRowStatus.choices)
    curp_raw = models.CharField(max_length=255, blank=True)
    normalized_curp = models.CharField(max_length=18, blank=True, db_index=True)
    full_name = models.CharField(max_length=250, blank=True)
    employment_status_raw = models.CharField(max_length=100, blank=True)
    systems_payload = models.JSONField(default=list, blank=True)
    raw_payload = models.JSONField(default=dict)
    errors = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    row_fingerprint = models.CharField(max_length=64)
    person = models.ForeignKey(
        "people.Person",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="source_rows",
    )

    class Meta:
        ordering = ("row_number",)
        constraints = [
            models.UniqueConstraint(
                fields=("payroll_import", "row_number"),
                name="unique_payroll_import_row_number",
            )
        ]
        verbose_name = "fila de fuente oficial"
        verbose_name_plural = "filas de fuente oficial"

    def __str__(self):
        return f"{self.payroll_import_id} / fila {self.row_number}"
