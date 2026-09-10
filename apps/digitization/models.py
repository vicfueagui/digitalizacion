from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class ScanSessionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Activa"
    COMPLETED = "COMPLETED", "Terminada"
    ABORTED = "ABORTED", "Interrumpida"


class ScanSession(models.Model):
    record = models.ForeignKey("records.PersonnelRecord", on_delete=models.PROTECT, related_name="scan_sessions")
    digitalizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="scan_sessions",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    workstation = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=ScanSessionStatus.choices)

    class Meta:
        ordering = ("-started_at",)
        verbose_name = "sesión de digitalización"
        verbose_name_plural = "sesiones de digitalización"

    def __str__(self):
        return f"{self.record} · {self.digitalizer}"


class DocumentType(TimeStampedModel):
    code = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(r"^[A-Z0-9_-]+$", "Use letras, números, guion o guion bajo.")],
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    destination_folder = models.CharField(max_length=100)
    applicable_systems = models.ManyToManyField(
        "people.AdministrativeSystem",
        related_name="document_types",
        blank=True,
    )
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("sort_order", "code")
        verbose_name = "tipo documental"
        verbose_name_plural = "tipos documentales"

    def clean(self):
        folder = self.destination_folder.strip()
        if not folder or folder in {".", ".."} or "/" in folder or "\\" in folder:
            raise ValidationError({"destination_folder": "Indique un solo nombre de carpeta, sin ruta."})
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("La fecha final no puede ser anterior a la inicial.")

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.destination_folder = self.destination_folder.strip().upper()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} · {self.name}"


class ScanMode(models.TextChoices):
    INDIVIDUAL_ONE_SIDE = "INDIVIDUAL_ONE_SIDE", "Individual una cara"
    INDIVIDUAL_DUPLEX = "INDIVIDUAL_DUPLEX", "Individual doble cara / METLIFE"
    MULTI_ONE_SIDE = "MULTI_ONE_SIDE", "Multi una cara"
    OTHER = "OTHER", "Otra"


class ScanModeGroup(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", "Individual"
    MULTI = "MULTI", "Multi"
    OTHER = "OTHER", "Otra / pendiente"


class DigitalDocument(models.Model):
    record = models.ForeignKey("records.PersonnelRecord", on_delete=models.PROTECT, related_name="documents")
    scan_session = models.ForeignKey(
        ScanSession,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, related_name="documents")
    scan_mode = models.CharField(max_length=24, choices=ScanMode.choices)
    other_mode_description = models.CharField(max_length=200, blank=True)
    sequence = models.PositiveIntegerField(null=True, blank=True)
    classification_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="confirmed_documents",
    )
    classification_confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sequence", "pk")
        verbose_name = "documento lógico"
        verbose_name_plural = "documentos lógicos"
        constraints = [
            models.CheckConstraint(
                condition=~Q(scan_mode=ScanMode.OTHER) | ~Q(other_mode_description=""),
                name="other_scan_mode_requires_description",
            )
        ]

    @property
    def scan_mode_group(self):
        if self.scan_mode in (ScanMode.INDIVIDUAL_ONE_SIDE, ScanMode.INDIVIDUAL_DUPLEX):
            return ScanModeGroup.INDIVIDUAL
        if self.scan_mode == ScanMode.MULTI_ONE_SIDE:
            return ScanModeGroup.MULTI
        return ScanModeGroup.OTHER

    @property
    def scan_mode_group_display(self):
        return ScanModeGroup(self.scan_mode_group).label

    def clean(self):
        if self.scan_mode == ScanMode.OTHER and not self.other_mode_description.strip():
            raise ValidationError({"other_mode_description": "Describa la modalidad OTHER."})
        if self.document_type_id and not self.document_type.active:
            raise ValidationError({"document_type": "El tipo documental está inactivo."})

    def __str__(self):
        return f"{self.record} · {self.document_type.code}"


class AssetStatus(models.TextChoices):
    PRESENT = "PRESENT", "Presente"
    MISSING = "MISSING", "No encontrado en la última verificación"
    UNEXPECTED = "UNEXPECTED", "Nombre o ubicación inesperada"


class DigitalAsset(TimeStampedModel):
    record = models.ForeignKey("records.PersonnelRecord", on_delete=models.PROTECT, related_name="digital_assets")
    document = models.ForeignKey(
        DigitalDocument,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assets",
    )
    filename = models.CharField(max_length=255)
    relative_path = models.CharField(max_length=500)
    extension = models.CharField(max_length=8)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    detected_prefix = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=12, choices=AssetStatus.choices, default=AssetStatus.PRESENT)
    discovered_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("relative_path",)
        constraints = [
            models.UniqueConstraint(fields=("record", "relative_path"), name="unique_asset_path_per_record")
        ]
        verbose_name = "archivo TIFF"
        verbose_name_plural = "archivos TIFF"
        permissions = [("inventory_tiff", "Puede inventariar TIFF en modo lectura")]

    def clean(self):
        path = PurePosixPath(self.relative_path.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise ValidationError({"relative_path": "La ruta debe ser relativa y no puede escapar del expediente."})
        extension = self.extension.lower().lstrip(".")
        if extension not in {"tif", "tiff"}:
            raise ValidationError({"extension": "Solamente se admiten extensiones tif o tiff."})
        if self.document_id and self.document.record_id != self.record_id:
            raise ValidationError({"document": "El documento lógico pertenece a otro expediente."})

    def save(self, *args, **kwargs):
        self.relative_path = self.relative_path.replace("\\", "/")
        self.extension = self.extension.lower().lstrip(".")
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.relative_path


class DigitalPage(models.Model):
    asset = models.ForeignKey(DigitalAsset, on_delete=models.PROTECT, related_name="pages")
    page_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("asset", "page_number")
        constraints = [
            models.UniqueConstraint(fields=("asset", "page_number"), name="unique_page_number_per_asset")
        ]
        verbose_name = "página digital"
        verbose_name_plural = "páginas digitales"

    def __str__(self):
        return f"{self.asset.filename} · página {self.page_number}"


class DigitalInventoryRun(models.Model):
    record = models.ForeignKey(
        "records.PersonnelRecord",
        on_delete=models.PROTECT,
        related_name="inventory_runs",
    )
    root_relative_path = models.CharField(max_length=500)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inventory_runs",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    compute_hashes = models.BooleanField(default=False)
    discovered_count = models.PositiveIntegerField(default=0)
    unexpected_count = models.PositiveIntegerField(default=0)
    summary = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-started_at",)
        verbose_name = "ejecución de inventario TIFF"
        verbose_name_plural = "ejecuciones de inventario TIFF"


class BatImportStatus(models.TextChoices):
    COMPLETED = "COMPLETED", "Completada"
    WITH_ERRORS = "WITH_ERRORS", "Completada con errores"


class BatCsvImport(models.Model):
    batch = models.ForeignKey("batches.IntakeBatch", on_delete=models.PROTECT, related_name="bat_imports")
    source_file_name = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, unique=True)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bat_csv_imports",
    )
    imported_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=BatImportStatus.choices)
    row_count = models.PositiveIntegerField(default=0)
    accepted_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-imported_at",)
        verbose_name = "importación CSV del BAT"
        verbose_name_plural = "importaciones CSV del BAT"
        permissions = [("import_bat_csv", "Puede importar resúmenes CSV del BAT")]


class BatRowStatus(models.TextChoices):
    ACCEPTED = "ACCEPTED", "Aceptada"
    DISCREPANCY = "DISCREPANCY", "Con discrepancias"
    ERROR = "ERROR", "Con error"
    DUPLICATE = "DUPLICATE", "Fila ya importada antes"


class BatCsvRow(models.Model):
    csv_import = models.ForeignKey(BatCsvImport, on_delete=models.PROTECT, related_name="rows")
    batch = models.ForeignKey("batches.IntakeBatch", on_delete=models.PROTECT, related_name="bat_rows")
    row_number = models.PositiveIntegerField()
    record = models.ForeignKey(
        "records.PersonnelRecord",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="bat_rows",
    )
    curp = models.CharField(max_length=18, blank=True)
    physical_count = models.PositiveIntegerField(null=True, blank=True)
    digital_count = models.PositiveIntegerField(null=True, blank=True)
    individual_count = models.PositiveIntegerField(null=True, blank=True)
    multi_count = models.PositiveIntegerField(null=True, blank=True)
    organization_result = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=16, choices=BatRowStatus.choices)
    raw_payload = models.JSONField(default=dict)
    errors = models.JSONField(default=list, blank=True)
    discrepancies = models.JSONField(default=list, blank=True)
    row_hash = models.CharField(max_length=64, db_index=True)

    class Meta:
        ordering = ("row_number",)
        constraints = [
            models.UniqueConstraint(fields=("csv_import", "row_number"), name="unique_bat_csv_row_number")
        ]
        verbose_name = "fila CSV del BAT"
        verbose_name_plural = "filas CSV del BAT"
