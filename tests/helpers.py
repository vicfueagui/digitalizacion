from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.batches.models import IntakeBatch
from apps.people.models import Person
from apps.records.models import PersonnelRecord


def initialize_reference_data():
    call_command("initialize_system", stdout=StringIO(), stderr=StringIO())


def user_in_role(username, role):
    user = get_user_model().objects.create_user(username=username, password="test-only-password")
    user.groups.add(Group.objects.get(name=role))
    return user


def make_batch_record(*, suffix="A", responsible=None, source_row=None):
    user = responsible or get_user_model().objects.create_user(username=f"responsable_{suffix}")
    batch = IntakeBatch.objects.create(
        code=f"LOTE-{suffix}",
        received_at=date(2026, 1, 2),
        responsible=user,
        created_by=user,
        expected_records=1,
    )
    curp = f"TEST{suffix}000000AAAAA01"
    person = Person.objects.create(curp=curp, full_name=f"Persona sintética {suffix}")
    record = PersonnelRecord.objects.create(batch=batch, person=person, source_row=source_row)
    return batch, record
