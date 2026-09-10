from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class BatchStatus(models.TextChoices):
    RECEIVED = "RECEIVED", "Recibido"
    IN_PROGRESS = "IN_PROGRESS", "En proceso"
    COMPLETED = "COMPLETED", "Completado"
    CANCELLED = "CANCELLED", "Cancelado"


class IntakeBatch(TimeStampedModel):
    code = models.CharField(max_length=80, unique=True)
    received_at = models.DateField()
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responsible_batches",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_batches",
    )
    source_import = models.ForeignKey(
        "sources.PayrollImport",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="intake_batches",
    )
    expected_system = models.ForeignKey(
        "people.AdministrativeSystem",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="intake_batches",
    )
    expected_records = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.RECEIVED)

    class Meta:
        ordering = ("-received_at", "-pk")
        verbose_name = "lote de digitalización"
        verbose_name_plural = "lotes de digitalización"
        permissions = [
            ("receive_batch", "Puede recibir lotes"),
            ("reconcile_batch", "Puede conciliar lotes"),
        ]

    def __str__(self):
        return self.code
