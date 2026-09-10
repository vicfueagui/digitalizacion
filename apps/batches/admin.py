from django.contrib import admin

from .models import IntakeBatch


@admin.register(IntakeBatch)
class IntakeBatchAdmin(admin.ModelAdmin):
    list_display = ("code", "received_at", "responsible", "expected_records", "status")
    list_filter = ("status", "expected_system")
    search_fields = ("code",)
    autocomplete_fields = ("responsible", "created_by", "source_import")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
