from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=64, db_index=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-occurred_at", "-pk")
        verbose_name = "evento de auditoría"
        verbose_name_plural = "eventos de auditoría"
        permissions = [("view_operational_audit", "Puede consultar auditoría operativa")]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Los eventos de auditoría son inmutables.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los eventos de auditoría no se eliminan.")

    def __str__(self):
        return f"{self.action} · {self.entity_type} {self.entity_id}"
