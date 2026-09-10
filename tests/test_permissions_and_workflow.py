from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.batches.services import bulk_assign_records
from apps.core.models import AuditEvent
from apps.people.models import Person
from apps.quality.models import QualityReview, ReviewDecision
from apps.quality.services import review_record
from apps.records.models import PersonnelRecord, RecordStatus, RecordStatusTransition
from apps.records.selectors import records_for_user
from apps.records.services import (
    accept_assignment,
    assign_record,
    register_physical_count,
    start_work,
    submit_correction,
    submit_for_review,
)

from .helpers import initialize_reference_data, make_batch_record, user_in_role


class PermissionAndWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        initialize_reference_data()
        cls.supervisor = user_in_role("supervisor", "Responsables de digitalización")
        cls.digitalizer = user_in_role("digitalizador", "Digitalizadores")
        cls.other_digitalizer = user_in_role("digitalizador_otro", "Digitalizadores")
        cls.reviewer = user_in_role("revisor", "Revisores")
        cls.auditor = user_in_role("consulta", "Consulta y auditoría")
        cls.batch, cls.record = make_batch_record(suffix="D", responsible=cls.supervisor)
        _, cls.other_record = make_batch_record(suffix="E", responsible=cls.supervisor)
        assign_record(record_id=cls.record.pk, digitalizer=cls.digitalizer, actor=cls.supervisor)
        assign_record(record_id=cls.other_record.pk, digitalizer=cls.other_digitalizer, actor=cls.supervisor)

    def test_digitalizer_only_sees_assigned_record(self):
        self.assertSetEqual(
            set(records_for_user(self.digitalizer).values_list("pk", flat=True)),
            {self.record.pk},
        )
        self.client.force_login(self.digitalizer)
        response = self.client.get(reverse("record_detail", args=[self.other_record.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.digitalizer.has_perm("batches.view_intakebatch"))
        self.assertEqual(self.client.get(reverse("batch_list")).status_code, 403)

    def test_supervisor_can_assign_and_auditor_cannot_modify(self):
        self.assertTrue(self.supervisor.has_perm("records.assign_record"))
        self.assertFalse(self.auditor.has_perm("records.add_physicalcount"))
        self.client.force_login(self.auditor)
        response = self.client.post(
            reverse("record_add_physical_count", args=[self.record.pk]),
            {"sheet_count": 10, "correction_reason": ""},
        )
        self.assertEqual(response.status_code, 403)

    def test_valid_workflow_separates_submission_validation_and_close(self):
        accept_assignment(record_id=self.record.pk, actor=self.digitalizer)
        start_work(record_id=self.record.pk, actor=self.digitalizer)
        submit_for_review(record_id=self.record.pk, actor=self.digitalizer, notes="Trabajo terminado")
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, RecordStatus.READY_FOR_REVIEW)

        review_record(
            record_id=self.record.pk,
            actor=self.reviewer,
            decision=ReviewDecision.VALIDATED,
            observations="Revisión satisfactoria",
        )
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, RecordStatus.VALIDATED)
        self.assertNotEqual(self.record.status, RecordStatus.CLOSED)
        self.assertEqual(RecordStatusTransition.objects.filter(record=self.record).count(), 4)
        self.assertTrue(AuditEvent.objects.filter(action="quality_review.recorded").exists())

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(ValidationError):
            submit_for_review(record_id=self.record.pk, actor=self.digitalizer)

    def test_user_cannot_review_own_work_even_with_reviewer_role(self):
        self.digitalizer.groups.add(self.reviewer.groups.get(name="Revisores"))
        accept_assignment(record_id=self.record.pk, actor=self.digitalizer)
        start_work(record_id=self.record.pk, actor=self.digitalizer)
        submit_for_review(record_id=self.record.pk, actor=self.digitalizer)
        with self.assertRaises(PermissionDenied):
            review_record(
                record_id=self.record.pk,
                actor=self.digitalizer,
                decision=ReviewDecision.VALIDATED,
            )

    def test_observation_and_correction_preserve_review_history(self):
        accept_assignment(record_id=self.record.pk, actor=self.digitalizer)
        start_work(record_id=self.record.pk, actor=self.digitalizer)
        submit_for_review(record_id=self.record.pk, actor=self.digitalizer)
        review_record(
            record_id=self.record.pk,
            actor=self.reviewer,
            decision=ReviewDecision.OBSERVED,
            observations="Revisar conteo.",
        )
        submit_correction(record_id=self.record.pk, actor=self.digitalizer, notes="Conteo revisado.")
        review_record(
            record_id=self.record.pk,
            actor=self.reviewer,
            decision=ReviewDecision.VALIDATED,
        )
        self.assertEqual(QualityReview.objects.filter(record=self.record).count(), 2)
        first = QualityReview.objects.filter(record=self.record).order_by("reviewed_at").first()
        self.assertEqual(first.observations, "Revisar conteo.")

    def test_recount_requires_reason_and_preserves_first_count(self):
        first = register_physical_count(record_id=self.record.pk, sheet_count=10, actor=self.digitalizer)
        with self.assertRaises(ValidationError):
            register_physical_count(record_id=self.record.pk, sheet_count=11, actor=self.digitalizer)
        second = register_physical_count(
            record_id=self.record.pk,
            sheet_count=11,
            actor=self.digitalizer,
            correction_reason="Se encontró una hoja adherida.",
        )
        self.assertEqual((first.version, second.version), (1, 2))
        self.assertEqual(self.record.physical_counts.count(), 2)

    def test_work_cannot_start_before_receipt_confirmation(self):
        with self.assertRaises(ValidationError):
            start_work(record_id=self.record.pk, actor=self.digitalizer)
        assignment = accept_assignment(
            record_id=self.record.pk,
            actor=self.digitalizer,
            notes="Expediente y datos corresponden.",
        )
        self.assertIsNotNone(assignment.accepted_at)
        self.assertTrue(AuditEvent.objects.filter(action="record.received_by_digitalizer").exists())

    def test_audit_events_are_immutable(self):
        event = AuditEvent.objects.filter(entity_id=str(self.record.pk)).first()
        event.action = "changed"
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()

    def test_supervisor_operational_pages_render(self):
        self.client.force_login(self.supervisor)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("batch_detail", args=[self.batch.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("record_detail", args=[self.record.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("review_queue")).status_code, 200)
        self.assertEqual(self.client.get(reverse("operational_report")).status_code, 200)

    def test_bulk_assignment_is_atomic_and_historical(self):
        batch, first = make_batch_record(suffix="J", responsible=self.supervisor)
        second_person = Person.objects.create(curp="TESTK000000AAAAA01")
        second = PersonnelRecord.objects.create(batch=batch, person=second_person)
        assignments = bulk_assign_records(
            batch_id=batch.pk,
            record_ids=[first.pk, second.pk],
            digitalizer=self.digitalizer,
            actor=self.supervisor,
            reason="Entrega física conjunta.",
        )
        self.assertEqual(len(assignments), 2)
        self.assertEqual(
            PersonnelRecord.objects.filter(batch=batch, status=RecordStatus.ASSIGNED).count(),
            2,
        )
