from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.core.audit import audit_event
from apps.digitization.services import record_reconciliation
from apps.records.models import PersonnelRecord, RecordStatus
from apps.records.selectors import user_can_access_record
from apps.records.services import _active_assignment, _transition

from .models import QualityReview, ReviewDecision


@transaction.atomic
def review_record(*, record_id, actor, decision, observations="", **verified_counts):
    required_permission = (
        "quality.validate_record" if decision == ReviewDecision.VALIDATED else "quality.observe_record"
    )
    if not actor.has_perm(required_permission):
        raise PermissionDenied("No tiene permiso para registrar esa decisión.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    if not user_can_access_record(actor, record):
        raise PermissionDenied("No tiene acceso a este expediente.")
    if record.status not in (RecordStatus.READY_FOR_REVIEW, RecordStatus.CORRECTED):
        raise ValidationError("El expediente no está en una bandeja revisable.")
    assignment = _active_assignment(record)
    if assignment and assignment.digitalizer_id == actor.pk:
        raise PermissionDenied("No se permite validar u observar el trabajo propio en el MVP.")
    if decision == ReviewDecision.OBSERVED and not observations.strip():
        raise ValidationError("Debe indicar las observaciones que se corregirán.")
    if decision not in ReviewDecision.values:
        raise ValidationError("Decisión de revisión inválida.")

    checks = record_reconciliation(record)
    discrepancies = [
        {"code": code, **result}
        for code, result in checks.items()
        if not result.get("ok", False)
    ]
    review = QualityReview(
        record=record,
        reviewer=actor,
        decision=decision,
        observations=observations,
        discrepancies=discrepancies,
        **verified_counts,
    )
    review.full_clean()
    review.save()
    target = RecordStatus.VALIDATED if decision == ReviewDecision.VALIDATED else RecordStatus.OBSERVED
    _transition(record=record, to_status=target, actor=actor, reason=observations)
    audit_event(
        actor=actor,
        action="quality_review.recorded",
        entity=review,
        new={"decision": decision, "record_id": record.pk, "discrepancies": discrepancies},
    )
    return review
