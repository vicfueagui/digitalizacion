from django.contrib import admin

from .models import PayrollImport, PayrollSourceRow


class SourceRowInline(admin.TabularInline):
    model = PayrollSourceRow
    extra = 0
    can_delete = False
    readonly_fields = (
        "row_number",
        "status",
        "curp_raw",
        "normalized_curp",
        "person",
        "errors",
        "warnings",
        "raw_payload",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PayrollImport)
class PayrollImportAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "imported_at",
        "imported_by",
        "status",
        "accepted_rows",
        "error_rows",
    )
    list_filter = ("status",)
    search_fields = ("original_filename", "sha256")
    readonly_fields = (
        "original_filename",
        "imported_by",
        "sha256",
        "imported_at",
        "status",
        "row_count",
        "accepted_rows",
        "error_rows",
        "warning_rows",
        "column_mapping",
    )
    inlines = (SourceRowInline,)
    exclude = ("source_file",)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PayrollSourceRow)
class PayrollSourceRowAdmin(admin.ModelAdmin):
    list_display = ("payroll_import", "row_number", "normalized_curp", "status", "person")
    list_filter = ("status", "payroll_import")
    search_fields = ("normalized_curp", "curp_raw", "full_name")
    readonly_fields = (
        "payroll_import",
        "row_number",
        "status",
        "curp_raw",
        "normalized_curp",
        "full_name",
        "employment_status_raw",
        "systems_payload",
        "raw_payload",
        "errors",
        "warnings",
        "row_fingerprint",
        "person",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
