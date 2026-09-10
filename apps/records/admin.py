from django.contrib import admin

from apps.core.admin import AuditedCatalogAdmin

from .models import (
    Incident,
    IncidentType,
    PersonnelRecord,
    PhysicalCount,
    RecordAssignment,
    RecordStatusTransition,
)


@admin.register(PersonnelRecord)
class PersonnelRecordAdmin(admin.ModelAdmin):
    list_display = ("person", "batch", "status", "expected_system", "current_custodian", "updated_at")
    list_filter = ("status", "expected_system", "batch")
    search_fields = ("person__curp", "person__full_name", "physical_identifier")
    autocomplete_fields = ("person", "batch", "source_row", "current_custodian")
    readonly_fields = ("status", "current_custodian", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RecordAssignment)
class RecordAssignmentAdmin(admin.ModelAdmin):
    list_display = ("record", "digitalizer", "assigned_by", "assigned_at", "accepted_at", "ended_at")
    readonly_fields = (
        "record",
        "digitalizer",
        "assigned_by",
        "assigned_at",
        "accepted_at",
        "acceptance_notes",
        "ended_at",
        "reason",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PhysicalCount)
class PhysicalCountAdmin(admin.ModelAdmin):
    list_display = ("record", "sheet_count", "version", "counted_by", "recorded_at")
    readonly_fields = ("record", "sheet_count", "version", "counted_by", "recorded_at", "correction_reason")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IncidentType)
class IncidentTypeAdmin(AuditedCatalogAdmin):
    list_display = ("code", "name", "category", "severity", "blocks_flow", "active")
    list_filter = ("active", "severity", "blocks_flow", "category")
    search_fields = ("code", "name")


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("record", "incident_type", "stage", "status", "detected_by", "detected_at")
    list_filter = ("status", "stage", "incident_type")
    readonly_fields = ("detected_at", "resolved_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RecordStatusTransition)
class RecordStatusTransitionAdmin(admin.ModelAdmin):
    list_display = ("record", "from_status", "to_status", "actor", "occurred_at")
    readonly_fields = ("record", "from_status", "to_status", "actor", "reason", "occurred_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
