from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel


class RecordStatus(models.TextChoices):
    RECEIVED = "RECEIVED", "Recibido"
    ASSIGNED = "ASSIGNED", "Asignado"
    IN_PROGRESS = "IN_PROGRESS", "En proceso"
    READY_FOR_REVIEW = "READY_FOR_REVIEW", "Terminado por digitalizador / Pendiente de validación"
    OBSERVED = "OBSERVED", "Observado para corrección"
    CORRECTED = "CORRECTED", "Corrección enviada / Pendiente de revisión"
    VALIDATED = "VALIDATED", "Validado"
    CLOSED = "CLOSED", "Cerrado"
    CANCELLED = "CANCELLED", "Cancelado"


class PersonnelRecord(TimeStampedModel):
    person = models.ForeignKey("people.Person", on_delete=models.PROTECT, related_name="records")
    batch = models.ForeignKey("batches.IntakeBatch", on_delete=models.PROTECT, related_name="records")
    source_row = models.ForeignKey(
        "sources.PayrollSourceRow",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="records",
    )
    declared_systems = models.ManyToManyField(
        "people.AdministrativeSystem",
        related_name="declared_records",
        blank=True,
    )
    expected_system = models.ForeignKey(
        "people.AdministrativeSystem",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expected_records",
    )
    physical_identifier = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=30, choices=RecordStatus.choices, default=RecordStatus.RECEIVED)
    current_custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="records_in_custody",
    )

    class Meta:
        ordering = ("batch", "person__curp")
        constraints = [
            models.UniqueConstraint(fields=("batch", "person"), name="unique_person_per_intake_batch")
        ]
        verbose_name = "expediente"
        verbose_name_plural = "expedientes"
        permissions = [
            ("view_all_records", "Puede consultar todos los expedientes del área"),
            ("assign_record", "Puede asignar y reasignar expedientes"),
            ("work_on_record", "Puede trabajar expedientes asignados"),
            ("submit_record", "Puede enviar expedientes a revisión"),
            ("correct_record", "Puede enviar correcciones a revisión"),
            ("close_record", "Puede cerrar expedientes validados"),
            ("cancel_record", "Puede cancelar expedientes con motivo"),
        ]

    @property
    def latest_physical_count(self):
        return self.physical_counts.order_by("-version").first()

    @property
    def current_assignment(self):
        return self.assignments.filter(ended_at__isnull=True).select_related("digitalizer").first()

    def __str__(self):
        return f"{self.person.curp} · {self.batch.code}"

    def clean(self):
        if self.source_row_id:
            if self.person_id and self.source_row.person_id != self.person_id:
                raise ValidationError({"source_row": "La fila oficial pertenece a otra persona."})
            if self.batch_id and self.batch.source_import_id != self.source_row.payroll_import_id:
                raise ValidationError({"source_row": "La fila oficial no pertenece a la fuente asociada al lote."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class RecordAssignment(models.Model):
    record = models.ForeignKey(PersonnelRecord, on_delete=models.PROTECT, related_name="assignments")
    digitalizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="digitization_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assignments_made",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    acceptance_notes = models.TextField(blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ("-assigned_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("record",),
                condition=Q(ended_at__isnull=True),
                name="one_active_assignment_per_record",
            )
        ]
        verbose_name = "asignación de expediente"
        verbose_name_plural = "asignaciones de expedientes"

    def __str__(self):
        return f"{self.record} → {self.digitalizer}"


class PhysicalCount(models.Model):
    record = models.ForeignKey(PersonnelRecord, on_delete=models.PROTECT, related_name="physical_counts")
    sheet_count = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="physical_counts",
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField()
    correction_reason = models.TextField(blank=True)

    class Meta:
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(fields=("record", "version"), name="unique_physical_count_version")
        ]
        verbose_name = "conteo físico"
        verbose_name_plural = "conteos físicos"

    def __str__(self):
        return f"{self.record}: {self.sheet_count} hojas (v{self.version})"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Los conteos físicos registrados son inmutables; agregue un reconteo.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los conteos físicos registrados no se eliminan.")


class IncidentSeverity(models.TextChoices):
    LOW = "LOW", "Baja"
    MEDIUM = "MEDIUM", "Media"
    HIGH = "HIGH", "Alta"
    CRITICAL = "CRITICAL", "Crítica"


class IncidentType(TimeStampedModel):
    code = models.CharField(
        max_length=40,
        unique=True,
        validators=[RegexValidator(r"^[A-Z0-9_-]+$", "Use letras, números, guion o guion bajo.")],
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    severity = models.CharField(max_length=10, choices=IncidentSeverity.choices, default=IncidentSeverity.MEDIUM)
    blocks_flow = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("code",)
        verbose_name = "tipo de incidencia"
        verbose_name_plural = "tipos de incidencia"

    def clean(self):
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("La fecha final no puede ser anterior a la inicial.")

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} · {self.name}"


class IncidentStage(models.TextChoices):
    INTAKE = "INTAKE", "Recepción"
    PHYSICAL_COUNT = "PHYSICAL_COUNT", "Conteo físico"
    DIGITIZATION = "DIGITIZATION", "Digitalización"
    REVIEW = "REVIEW", "Revisión"
    OTHER = "OTHER", "Otra"


class IncidentStatus(models.TextChoices):
    OPEN = "OPEN", "Abierta"
    RESOLVED = "RESOLVED", "Resuelta"


class Incident(models.Model):
    record = models.ForeignKey(PersonnelRecord, on_delete=models.PROTECT, related_name="incidents")
    incident_type = models.ForeignKey(IncidentType, on_delete=models.PROTECT, related_name="incidents")
    stage = models.CharField(max_length=20, choices=IncidentStage.choices)
    description = models.TextField(blank=True)
    detected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="detected_incidents",
    )
    detected_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=IncidentStatus.choices, default=IncidentStatus.OPEN)
    resolution = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="resolved_incidents",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-detected_at",)
        verbose_name = "incidencia"
        verbose_name_plural = "incidencias"

    def __str__(self):
        return f"{self.record} · {self.incident_type.code}"


class RecordStatusTransition(models.Model):
    record = models.ForeignKey(PersonnelRecord, on_delete=models.PROTECT, related_name="transitions")
    from_status = models.CharField(max_length=30, choices=RecordStatus.choices)
    to_status = models.CharField(max_length=30, choices=RecordStatus.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="record_transitions",
    )
    reason = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-occurred_at", "-pk")
        verbose_name = "transición de expediente"
        verbose_name_plural = "transiciones de expedientes"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Las transiciones registradas son inmutables.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Las transiciones registradas no se eliminan.")

    def __str__(self):
        return f"{self.record}: {self.from_status} → {self.to_status}"
