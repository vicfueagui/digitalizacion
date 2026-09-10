from django.contrib import admin

from .audit import audit_event
from .models import AuditEvent


class AuditedCatalogAdmin(admin.ModelAdmin):
    """Registra altas/cambios hechos desde el administrador funcional."""

    def save_model(self, request, obj, form, change):
        previous = {
            field: form.initial.get(field)
            for field in form.changed_data
            if field in form.initial
        }
        super().save_model(request, obj, form, change)
        new = {field: form.cleaned_data.get(field) for field in form.changed_data}
        audit_event(
            actor=request.user,
            action="catalog.updated" if change else "catalog.created",
            entity=obj,
            previous=previous,
            new=new,
        )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "actor", "action", "entity_type", "entity_id")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_id", "actor__username")
    readonly_fields = (
        "actor",
        "action",
        "entity_type",
        "entity_id",
        "occurred_at",
        "previous_values",
        "new_values",
        "context",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
