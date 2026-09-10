from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.core.audit import audit_event

from .models import (
    Incident,
    IncidentStatus,
    PersonnelRecord,
    PhysicalCount,
    RecordAssignment,
    RecordStatus,
    RecordStatusTransition,
)
from .selectors import user_can_access_record

ALLOWED_TRANSITIONS = {
    RecordStatus.RECEIVED: {RecordStatus.ASSIGNED, RecordStatus.CANCELLED},
    RecordStatus.ASSIGNED: {RecordStatus.IN_PROGRESS, RecordStatus.CANCELLED},
    RecordStatus.IN_PROGRESS: {RecordStatus.READY_FOR_REVIEW, RecordStatus.CANCELLED},
    RecordStatus.READY_FOR_REVIEW: {RecordStatus.OBSERVED, RecordStatus.VALIDATED, RecordStatus.CANCELLED},
    RecordStatus.OBSERVED: {RecordStatus.CORRECTED, RecordStatus.CANCELLED},
    RecordStatus.CORRECTED: {RecordStatus.OBSERVED, RecordStatus.VALIDATED, RecordStatus.CANCELLED},
    RecordStatus.VALIDATED: {RecordStatus.CLOSED},
    RecordStatus.CLOSED: set(),
    RecordStatus.CANCELLED: set(),
}


def _active_assignment(record):
    return record.assignments.filter(ended_at__isnull=True).select_related("digitalizer").first()


def _require_assigned_actor(record, actor):
    assignment = _active_assignment(record)
    if assignment is None or assignment.digitalizer_id != actor.pk:
        raise PermissionDenied("El expediente no está asignado actualmente a este usuario.")
    return assignment


def _transition(*, record, to_status, actor, reason=""):
    if to_status not in ALLOWED_TRANSITIONS.get(record.status, set()):
        raise ValidationError(
            f"No se permite cambiar de {record.get_status_display()} a {RecordStatus(to_status).label}."
        )
    previous = record.status
    record.status = to_status
    record.save(update_fields=("status", "updated_at"))
    RecordStatusTransition.objects.create(
        record=record,
        from_status=previous,
        to_status=to_status,
        actor=actor,
        reason=reason,
    )
    audit_event(
        actor=actor,
        action="record.status_changed",
        entity=record,
        previous={"status": previous},
        new={"status": to_status},
        context={"reason": reason},
    )


@transaction.atomic
def assign_record(*, record_id, digitalizer, actor, reason=""):
    if not actor.has_perm("records.assign_record"):
        raise PermissionDenied("No tiene permiso para asignar expedientes.")
    if not digitalizer.is_active or not digitalizer.has_perm("records.work_on_record"):
        raise ValidationError("Seleccione un usuario activo con capacidad de digitalización.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    if not user_can_access_record(actor, record):
        raise PermissionDenied("No tiene acceso a este expediente.")
    if record.status not in (RecordStatus.RECEIVED, RecordStatus.ASSIGNED):
        raise ValidationError("Solo se puede asignar o reasignar un expediente recibido o asignado.")
    previous_assignment = _active_assignment(record)
    previous_user_id = None
    if previous_assignment:
        previous_user_id = previous_assignment.digitalizer_id
        if previous_user_id == digitalizer.pk:
            raise ValidationError("El expediente ya está asignado a ese digitalizador.")
        previous_assignment.ended_at = timezone.now()
        previous_assignment.save(update_fields=("ended_at",))
    assignment = RecordAssignment.objects.create(
        record=record,
        digitalizer=digitalizer,
        assigned_by=actor,
        reason=reason,
    )
    record.current_custodian = digitalizer
    record.save(update_fields=("current_custodian", "updated_at"))
    if record.status == RecordStatus.RECEIVED:
        _transition(record=record, to_status=RecordStatus.ASSIGNED, actor=actor, reason=reason)
    audit_event(
        actor=actor,
        action="record.assigned",
        entity=record,
        previous={"digitalizer_id": previous_user_id},
        new={"digitalizer_id": digitalizer.pk, "assignment_id": assignment.pk},
        context={"reason": reason},
    )
    return assignment


@transaction.atomic
def start_work(*, record_id, actor, workstation=""):
    if not actor.has_perm("records.work_on_record"):
        raise PermissionDenied("No tiene permiso para iniciar digitalización.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    assignment = _require_assigned_actor(record, actor)
    if assignment.accepted_at is None:
        raise ValidationError("Primero confirme la recepción y correspondencia del expediente.")
    _transition(record=record, to_status=RecordStatus.IN_PROGRESS, actor=actor)
    from apps.digitization.models import ScanSession, ScanSessionStatus

    session = ScanSession.objects.create(
        record=record,
        digitalizer=actor,
        workstation=workstation,
        status=ScanSessionStatus.ACTIVE,
    )
    audit_event(actor=actor, action="scan_session.started", entity=session, new={"record_id": record.pk})
    return session


@transaction.atomic
def accept_assignment(*, record_id, actor, notes=""):
    if not actor.has_perm("records.work_on_record"):
        raise PermissionDenied("No tiene permiso para recibir expedientes asignados.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    if record.status != RecordStatus.ASSIGNED:
        raise ValidationError("Solo se puede confirmar la recepción de un expediente asignado.")
    assignment = _require_assigned_actor(record, actor)
    if assignment.accepted_at is not None:
        raise ValidationError("La recepción de esta asignación ya fue confirmada.")
    assignment.accepted_at = timezone.now()
    assignment.acceptance_notes = notes
    assignment.save(update_fields=("accepted_at", "acceptance_notes"))
    audit_event(
        actor=actor,
        action="record.received_by_digitalizer",
        entity=record,
        new={"assignment_id": assignment.pk, "accepted_at": assignment.accepted_at},
        context={"notes": notes},
    )
    return assignment


@transaction.atomic
def submit_for_review(*, record_id, actor, notes=""):
    if not actor.has_perm("records.submit_record"):
        raise PermissionDenied("No tiene permiso para enviar el expediente a revisión.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    _require_assigned_actor(record, actor)
    _transition(record=record, to_status=RecordStatus.READY_FOR_REVIEW, actor=actor, reason=notes)
    from apps.digitization.models import ScanSessionStatus

    for session in record.scan_sessions.filter(status=ScanSessionStatus.ACTIVE):
        session.status = ScanSessionStatus.COMPLETED
        session.ended_at = timezone.now()
        session.notes = notes
        session.save(update_fields=("status", "ended_at", "notes"))
        audit_event(
            actor=actor,
            action="scan_session.completed",
            entity=session,
            previous={"status": ScanSessionStatus.ACTIVE},
            new={"status": ScanSessionStatus.COMPLETED, "ended_at": session.ended_at},
        )
    return record


@transaction.atomic
def submit_correction(*, record_id, actor, notes=""):
    if not actor.has_perm("records.correct_record"):
        raise PermissionDenied("No tiene permiso para enviar correcciones.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    _require_assigned_actor(record, actor)
    _transition(record=record, to_status=RecordStatus.CORRECTED, actor=actor, reason=notes)
    return record


@transaction.atomic
def close_record(*, record_id, actor, reason=""):
    if not actor.has_perm("records.close_record"):
        raise PermissionDenied("No tiene permiso para cerrar expedientes.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    if not user_can_access_record(actor, record):
        raise PermissionDenied("No tiene acceso a este expediente.")
    _transition(record=record, to_status=RecordStatus.CLOSED, actor=actor, reason=reason)
    assignment = _active_assignment(record)
    if assignment:
        assignment.ended_at = timezone.now()
        assignment.save(update_fields=("ended_at",))
    record.current_custodian = None
    record.save(update_fields=("current_custodian", "updated_at"))
    return record


@transaction.atomic
def cancel_record(*, record_id, actor, reason):
    if not actor.has_perm("records.cancel_record"):
        raise PermissionDenied("No tiene permiso para cancelar expedientes.")
    if not reason.strip():
        raise ValidationError("La cancelación requiere un motivo.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    if not user_can_access_record(actor, record):
        raise PermissionDenied("No tiene acceso a este expediente.")
    _transition(record=record, to_status=RecordStatus.CANCELLED, actor=actor, reason=reason)
    return record


def _may_edit_record(record, actor):
    if actor.is_superuser or actor.has_perm("records.view_all_records"):
        return
    _require_assigned_actor(record, actor)


@transaction.atomic
def register_physical_count(*, record_id, sheet_count, actor, correction_reason=""):
    if not actor.has_perm("records.add_physicalcount"):
        raise PermissionDenied("No tiene permiso para registrar conteos físicos.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    _may_edit_record(record, actor)
    last_version = record.physical_counts.aggregate(value=Max("version"))["value"] or 0
    if last_version and not correction_reason.strip():
        raise ValidationError("Un reconteo requiere indicar el motivo de corrección.")
    count = PhysicalCount.objects.create(
        record=record,
        sheet_count=sheet_count,
        counted_by=actor,
        version=last_version + 1,
        correction_reason=correction_reason,
    )
    audit_event(
        actor=actor,
        action="physical_count.recorded",
        entity=record,
        new={"physical_count_id": count.pk, "sheet_count": sheet_count, "version": count.version},
        context={"correction_reason": correction_reason},
    )
    return count


@transaction.atomic
def register_incident(*, record_id, incident_type, stage, description, actor):
    if not actor.has_perm("records.add_incident"):
        raise PermissionDenied("No tiene permiso para registrar incidencias.")
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    _may_edit_record(record, actor)
    if not incident_type.active:
        raise ValidationError("El tipo de incidencia está inactivo.")
    incident = Incident.objects.create(
        record=record,
        incident_type=incident_type,
        stage=stage,
        description=description,
        detected_by=actor,
    )
    audit_event(
        actor=actor,
        action="incident.recorded",
        entity=incident,
        new={"record_id": record.pk, "incident_type": incident_type.code, "stage": stage},
    )
    return incident


@transaction.atomic
def resolve_incident(*, incident_id, resolution, actor):
    if not actor.has_perm("records.change_incident"):
        raise PermissionDenied("No tiene permiso para resolver incidencias.")
    if not resolution.strip():
        raise ValidationError("La resolución es obligatoria.")
    incident = Incident.objects.select_for_update().get(pk=incident_id)
    if not user_can_access_record(actor, incident.record):
        raise PermissionDenied("No tiene acceso a este expediente.")
    if incident.status == IncidentStatus.RESOLVED:
        raise ValidationError("La incidencia ya fue resuelta.")
    incident.status = IncidentStatus.RESOLVED
    incident.resolution = resolution
    incident.resolved_by = actor
    incident.resolved_at = timezone.now()
    incident.save(update_fields=("status", "resolution", "resolved_by", "resolved_at"))
    audit_event(
        actor=actor,
        action="incident.resolved",
        entity=incident,
        previous={"status": IncidentStatus.OPEN},
        new={"status": IncidentStatus.RESOLVED},
        context={"resolution": resolution},
    )
    return incident
