from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class ReviewDecision(models.TextChoices):
    OBSERVED = "OBSERVED", "Devolver con observaciones"
    VALIDATED = "VALIDATED", "Validar"


class QualityReview(models.Model):
    record = models.ForeignKey("records.PersonnelRecord", on_delete=models.PROTECT, related_name="quality_reviews")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="quality_reviews",
    )
    reviewed_at = models.DateTimeField(auto_now_add=True)
    decision = models.CharField(max_length=10, choices=ReviewDecision.choices)
    observations = models.TextField(blank=True)
    verified_physical_count = models.PositiveIntegerField(null=True, blank=True)
    verified_digital_count = models.PositiveIntegerField(null=True, blank=True)
    verified_individual_count = models.PositiveIntegerField(null=True, blank=True)
    verified_multi_count = models.PositiveIntegerField(null=True, blank=True)
    discrepancies = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ("-reviewed_at",)
        verbose_name = "revisión de calidad"
        verbose_name_plural = "revisiones de calidad"
        permissions = [
            ("observe_record", "Puede devolver expedientes con observaciones"),
            ("validate_record", "Puede validar expedientes"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(decision=ReviewDecision.OBSERVED) | ~Q(observations=""),
                name="observed_review_requires_notes",
            )
        ]

    def clean(self):
        if self.decision == ReviewDecision.OBSERVED and not self.observations.strip():
            raise ValidationError({"observations": "Una devolución requiere observaciones."})

    def __str__(self):
        return f"{self.record} · {self.get_decision_display()}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Las revisiones registradas son inmutables.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Las revisiones registradas no se eliminan.")
