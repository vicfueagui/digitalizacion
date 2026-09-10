from django.contrib import admin

from apps.core.admin import AuditedCatalogAdmin

from .models import (
    BatCsvImport,
    BatCsvRow,
    DigitalAsset,
    DigitalDocument,
    DigitalInventoryRun,
    DigitalPage,
    DocumentType,
    ScanSession,
)


@admin.register(DocumentType)
class DocumentTypeAdmin(AuditedCatalogAdmin):
    list_display = ("code", "name", "destination_folder", "active", "sort_order")
    list_filter = ("active", "destination_folder", "applicable_systems")
    search_fields = ("code", "name")


class ReadOnlyOperationalAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(ScanSession, ReadOnlyOperationalAdmin)
admin.site.register(DigitalDocument, ReadOnlyOperationalAdmin)
admin.site.register(DigitalPage, ReadOnlyOperationalAdmin)


@admin.register(DigitalAsset)
class DigitalAssetAdmin(admin.ModelAdmin):
    list_display = ("filename", "record", "status", "file_size", "detected_prefix", "last_verified_at")
    list_filter = ("status", "extension", "detected_prefix")
    search_fields = ("filename", "relative_path", "sha256", "record__person__curp")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DigitalInventoryRun)
class DigitalInventoryRunAdmin(admin.ModelAdmin):
    list_display = ("record", "requested_by", "started_at", "discovered_count", "unexpected_count")
    readonly_fields = ("started_at", "finished_at", "summary")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BatCsvRowInline(admin.TabularInline):
    model = BatCsvRow
    extra = 0
    can_delete = False
    readonly_fields = (
        "row_number",
        "record",
        "curp",
        "physical_count",
        "digital_count",
        "individual_count",
        "multi_count",
        "status",
        "errors",
        "discrepancies",
        "raw_payload",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BatCsvImport)
class BatCsvImportAdmin(admin.ModelAdmin):
    list_display = ("source_file_name", "batch", "imported_by", "imported_at", "status", "row_count")
    readonly_fields = (
        "batch",
        "source_file_name",
        "sha256",
        "imported_by",
        "imported_at",
        "status",
        "row_count",
        "accepted_rows",
        "error_rows",
    )
    inlines = (BatCsvRowInline,)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
