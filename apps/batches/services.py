from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core.audit import audit_event
from apps.people.models import AdministrativeSystem, Person
from apps.records.models import PersonnelRecord
from apps.sources.models import SourceRowStatus

from .models import IntakeBatch


@transaction.atomic
def attach_source_import(*, batch_id, source_import, actor):
    if not (
        actor.has_perm("sources.import_payroll")
        and actor.has_perm("batches.reconcile_batch")
    ):
        raise PermissionError("No tiene permiso para asociar una fuente oficial.")
    batch = IntakeBatch.objects.select_for_update().get(pk=batch_id)
    if batch.source_import_id and batch.source_import_id != source_import.pk:
        raise ValidationError("El lote ya tiene una fuente oficial asociada; no se reemplazó.")
    if batch.source_import_id == source_import.pk:
        return batch
    batch.source_import = source_import
    batch.save(update_fields=("source_import", "updated_at"))
    audit_event(
        actor=actor,
        action="batch.source_attached",
        entity=batch,
        new={"source_import_id": source_import.pk, "sha256": source_import.sha256},
    )
    return batch


@transaction.atomic
def materialize_records_from_source(*, batch_id, actor):
    if not actor.has_perm("batches.reconcile_batch"):
        raise PermissionError("No tiene permiso para conciliar el lote.")
    batch = IntakeBatch.objects.select_for_update().select_related("source_import").get(pk=batch_id)
    if not batch.source_import_id:
        raise ValidationError("Primero asocie una importación oficial al lote.")

    created_count = 0
    existing_count = 0
    rows = batch.source_import.rows.filter(
        status__in=(SourceRowStatus.ACCEPTED, SourceRowStatus.WARNING),
        person__isnull=False,
    ).select_related("person")
    for row in rows:
        record, created = PersonnelRecord.objects.get_or_create(
            batch=batch,
            person=row.person,
            defaults={
                "source_row": row,
                "expected_system": batch.expected_system,
            },
        )
        if created:
            created_count += 1
        else:
            existing_count += 1
            if record.source_row_id is None:
                record.source_row = row
                record.save(update_fields=("source_row", "updated_at"))
        systems = AdministrativeSystem.objects.filter(code__in=row.systems_payload)
        record.declared_systems.add(*systems)

    audit_event(
        actor=actor,
        action="batch.records_materialized",
        entity=batch,
        new={"created": created_count, "already_existing": existing_count},
    )
    return created_count, existing_count


@transaction.atomic
def create_manual_record(*, batch_id, actor, curp, full_name="", physical_identifier="", systems=()):
    if not actor.has_perm("batches.reconcile_batch"):
        raise PermissionError("No tiene permiso para registrar expedientes del lote.")
    batch = IntakeBatch.objects.select_for_update().get(pk=batch_id)
    person, person_created = Person.objects.get_or_create(curp=curp, defaults={"full_name": full_name})
    if full_name and not person.full_name:
        person.full_name = full_name
        person.save()
    record, created = PersonnelRecord.objects.get_or_create(
        batch=batch,
        person=person,
        defaults={
            "expected_system": batch.expected_system,
            "physical_identifier": physical_identifier,
        },
    )
    if not created:
        raise ValidationError("Esta persona ya tiene un expediente dentro del lote.")
    record.declared_systems.add(*systems)
    audit_event(
        actor=actor,
        action="record.registered_from_physical_intake",
        entity=record,
        new={
            "batch_id": batch.pk,
            "person_created": person_created,
            "has_source_row": False,
        },
    )
    return record


def batch_reconciliation(batch):
    records = batch.records.select_related("source_row")
    source_accepted = (
        batch.source_import.rows.filter(
            status__in=(SourceRowStatus.ACCEPTED, SourceRowStatus.WARNING)
        ).count()
        if batch.source_import_id
        else 0
    )
    record_count = records.count()
    without_source = records.filter(source_row__isnull=True).count()
    source_without_record = max(source_accepted - records.filter(source_row__isnull=False).count(), 0)
    return {
        "expected_records": batch.expected_records,
        "record_count": record_count,
        "source_accepted": source_accepted,
        "without_source": without_source,
        "source_without_record": source_without_record,
        "expected_matches": record_count == batch.expected_records,
        "source_matches": source_accepted == record_count and without_source == 0,
    }


@transaction.atomic
def bulk_assign_records(*, batch_id, record_ids, digitalizer, actor, reason=""):
    if not actor.has_perm("records.assign_record"):
        raise PermissionError("No tiene permiso para asignar expedientes.")
    batch = IntakeBatch.objects.select_for_update().get(pk=batch_id)
    requested_ids = list(dict.fromkeys(record_ids))
    records = list(batch.records.filter(pk__in=requested_ids).order_by("pk"))
    if len(records) != len(requested_ids):
        raise ValidationError("Uno o más expedientes no pertenecen al lote.")
    from apps.records.services import assign_record

    assignments = [
        assign_record(
            record_id=record.pk,
            digitalizer=digitalizer,
            actor=actor,
            reason=reason,
        )
        for record in records
    ]
    return assignments
