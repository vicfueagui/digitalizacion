from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from django.db import models

from .models import AuditEvent

SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "file_content"}


def _safe_value(value):
    if isinstance(value, models.Model):
        return str(value.pk)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID, Path)):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): "[REDACTADO]" if str(key).lower() in SENSITIVE_KEYS else _safe_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def audit_event(*, actor, action, entity, previous=None, new=None, context=None):
    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity_type=entity._meta.label_lower,
        entity_id=str(entity.pk),
        previous_values=_safe_value(previous or {}),
        new_values=_safe_value(new or {}),
        context=_safe_value(context or {}),
    )
