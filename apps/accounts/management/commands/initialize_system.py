from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.digitization.models import DocumentType
from apps.people.models import AdministrativeSystem

ROLE_PERMISSIONS = {
    "Responsables de digitalización": {
        "batches": {
            "view_intakebatch",
            "add_intakebatch",
            "change_intakebatch",
            "receive_batch",
            "reconcile_batch",
        },
        "sources": {
            "view_payrollimport",
            "view_payrollsourcerow",
            "import_payroll",
            "reconcile_payroll",
        },
        "people": {"view_person", "add_person", "change_person", "view_administrativesystem"},
        "records": {
            "view_personnelrecord",
            "view_all_records",
            "assign_record",
            "close_record",
            "cancel_record",
            "view_recordassignment",
            "add_recordassignment",
            "view_physicalcount",
            "add_physicalcount",
            "view_incident",
            "add_incident",
            "change_incident",
            "view_incidenttype",
            "view_recordstatustransition",
        },
        "digitization": {
            "view_scansession",
            "view_documenttype",
            "view_digitaldocument",
            "add_digitaldocument",
            "view_digitalasset",
            "view_digitalpage",
            "add_digitalasset",
            "inventory_tiff",
            "view_digitalinventoryrun",
            "view_batcsvimport",
            "view_batcsvrow",
            "import_bat_csv",
        },
        "quality": {"view_qualityreview", "add_qualityreview", "observe_record", "validate_record"},
        "core": {"view_auditevent", "view_operational_audit"},
        "reports": {"view_operational_reports"},
    },
    "Digitalizadores": {
        "people": {"view_person", "view_administrativesystem"},
        "records": {
            "view_personnelrecord",
            "work_on_record",
            "submit_record",
            "correct_record",
            "view_recordassignment",
            "view_physicalcount",
            "add_physicalcount",
            "view_incident",
            "add_incident",
            "view_incidenttype",
            "view_recordstatustransition",
        },
        "digitization": {
            "view_scansession",
            "add_scansession",
            "change_scansession",
            "view_documenttype",
            "view_digitaldocument",
            "add_digitaldocument",
            "view_digitalasset",
            "view_digitalpage",
            "add_digitalasset",
            "change_digitalasset",
            "inventory_tiff",
            "view_digitalinventoryrun",
            "view_batcsvrow",
        },
        "quality": {"view_qualityreview"},
    },
    "Revisores": {
        "batches": {"view_intakebatch"},
        "sources": {"view_payrollimport", "view_payrollsourcerow"},
        "people": {"view_person", "view_administrativesystem"},
        "records": {
            "view_personnelrecord",
            "view_all_records",
            "view_recordassignment",
            "view_physicalcount",
            "view_incident",
            "add_incident",
            "change_incident",
            "view_incidenttype",
            "view_recordstatustransition",
        },
        "digitization": {
            "view_scansession",
            "view_documenttype",
            "view_digitaldocument",
            "view_digitalasset",
            "view_digitalpage",
            "inventory_tiff",
            "view_digitalinventoryrun",
            "view_batcsvimport",
            "view_batcsvrow",
        },
        "quality": {"view_qualityreview", "add_qualityreview", "observe_record", "validate_record"},
        "core": {"view_auditevent", "view_operational_audit"},
        "reports": {"view_operational_reports"},
    },
    "Consulta y auditoría": {
        "batches": {"view_intakebatch"},
        "sources": {"view_payrollimport", "view_payrollsourcerow"},
        "people": {"view_person", "view_administrativesystem", "view_personsystemmembership"},
        "records": {
            "view_personnelrecord",
            "view_all_records",
            "view_recordassignment",
            "view_physicalcount",
            "view_incident",
            "view_incidenttype",
            "view_recordstatustransition",
        },
        "digitization": {
            "view_scansession",
            "view_documenttype",
            "view_digitaldocument",
            "view_digitalasset",
            "view_digitalpage",
            "view_digitalinventoryrun",
            "view_batcsvimport",
            "view_batcsvrow",
        },
        "quality": {"view_qualityreview"},
        "core": {"view_auditevent", "view_operational_audit"},
        "reports": {"view_operational_reports"},
    },
}


class Command(BaseCommand):
    help = "Crea catálogos y permisos iniciales de forma idempotente."

    @transaction.atomic
    def handle(self, *args, **options):
        systems = {}
        for code, name in (("FEDERAL", "Federal"), ("ESTATAL", "Estatal")):
            systems[code], _ = AdministrativeSystem.objects.get_or_create(
                code=code,
                defaults={"name": name, "active": True},
            )

        for order, (code, folder) in enumerate(
            (("DP", "PERSONALES"), ("FP", "PERSONALES"), ("HL", "FEDERAL")), start=1
        ):
            DocumentType.objects.get_or_create(
                code=code,
                defaults={
                    "name": code,
                    "description": "Definición semántica pendiente de confirmación del área.",
                    "destination_folder": folder,
                    "active": True,
                    "sort_order": order,
                },
            )

        admin_group, _ = Group.objects.get_or_create(name="Administradores")
        admin_group.permissions.add(*Permission.objects.all())

        missing = []
        for group_name, app_permissions in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            for app_label, codenames in app_permissions.items():
                for codename in codenames:
                    permission = Permission.objects.filter(
                        content_type__app_label=app_label,
                        codename=codename,
                    ).first()
                    if permission:
                        group.permissions.add(permission)
                    else:
                        missing.append(f"{app_label}.{codename}")

        if missing:
            self.stderr.write("Permisos no encontrados: " + ", ".join(sorted(missing)))
        self.stdout.write(self.style.SUCCESS("Catálogos, grupos y permisos iniciales listos."))
