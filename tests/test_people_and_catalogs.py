from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.digitization.models import (
    DigitalDocument,
    DocumentType,
    ScanMode,
    ScanModeGroup,
)
from apps.people.models import AdministrativeSystem, Person, PersonSystemMembership
from apps.records.models import Incident, IncidentStage, IncidentType

from .helpers import initialize_reference_data, make_batch_record, user_in_role


class PeopleAndCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        initialize_reference_data()

    def test_curp_is_normalized_and_rejects_evident_invalid_format(self):
        person = Person.objects.create(curp=" testa 000000aaaaa01 ")
        self.assertEqual(person.curp, "TESTA000000AAAAA01")
        with self.assertRaises(ValidationError):
            Person.objects.create(curp="CORTA")

    def test_curp_is_unique_as_business_identifier(self):
        Person.objects.create(curp="TESTA000000AAAAA01")
        with self.assertRaises(ValidationError):
            Person.objects.create(curp="testa000000aaaaa01")

    def test_person_can_belong_to_federal_and_state_at_once(self):
        person = Person.objects.create(curp="TESTA000000AAAAA01")
        federal = AdministrativeSystem.objects.get(code="FEDERAL")
        state = AdministrativeSystem.objects.get(code="ESTATAL")
        PersonSystemMembership.objects.create(person=person, system=federal)
        PersonSystemMembership.objects.create(person=person, system=state)
        self.assertSetEqual(set(person.systems.values_list("code", flat=True)), {"FEDERAL", "ESTATAL"})

    def test_document_type_can_be_deactivated_without_destroying_history(self):
        digitalizer = user_in_role("digitalizador_catalogo", "Digitalizadores")
        _, record = make_batch_record(suffix="C")
        document_type = DocumentType.objects.get(code="DP")
        document = DigitalDocument.objects.create(
            record=record,
            document_type=document_type,
            scan_mode=ScanMode.INDIVIDUAL_ONE_SIDE,
            classification_confirmed_by=digitalizer,
        )
        document_type.active = False
        document_type.save()
        document.refresh_from_db()
        self.assertEqual(document.document_type.code, "DP")
        self.assertEqual(document.scan_mode_group, ScanModeGroup.INDIVIDUAL)

    def test_seed_command_is_idempotent(self):
        initialize_reference_data()
        self.assertEqual(AdministrativeSystem.objects.filter(code__in=["FEDERAL", "ESTATAL"]).count(), 2)
        self.assertEqual(DocumentType.objects.filter(code__in=["DP", "FP", "HL"]).count(), 3)

    def test_inactive_incident_type_preserves_existing_incident(self):
        digitalizer = user_in_role("digitalizador_incidencia", "Digitalizadores")
        _, record = make_batch_record(suffix="I")
        incident_type = IncidentType.objects.create(code="PRUEBA", name="Incidencia sintética")
        incident = Incident.objects.create(
            record=record,
            incident_type=incident_type,
            stage=IncidentStage.INTAKE,
            detected_by=digitalizer,
        )
        incident_type.active = False
        incident_type.save()
        incident.refresh_from_db()
        self.assertEqual(incident.incident_type.code, "PRUEBA")
