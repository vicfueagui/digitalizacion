from django.contrib import admin

from apps.core.admin import AuditedCatalogAdmin

from .models import AdministrativeSystem, Person, PersonSystemMembership


class MembershipInline(admin.TabularInline):
    model = PersonSystemMembership
    extra = 0
    readonly_fields = ("first_seen_at", "last_seen_at")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("curp", "full_name", "employment_status", "updated_at")
    list_filter = ("employment_status", "systems")
    search_fields = ("curp", "full_name")
    inlines = (MembershipInline,)
    readonly_fields = ("curp", "full_name", "employment_status", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdministrativeSystem)
class AdministrativeSystemAdmin(AuditedCatalogAdmin):
    list_display = ("code", "name", "active", "effective_from", "effective_to")
    list_filter = ("active",)
    search_fields = ("code", "name")
