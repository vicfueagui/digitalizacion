from django.contrib import admin

from .models import QualityReview


@admin.register(QualityReview)
class QualityReviewAdmin(admin.ModelAdmin):
    list_display = ("record", "reviewer", "decision", "reviewed_at")
    list_filter = ("decision",)
    readonly_fields = (
        "record",
        "reviewer",
        "reviewed_at",
        "decision",
        "observations",
        "verified_physical_count",
        "verified_digital_count",
        "verified_individual_count",
        "verified_multi_count",
        "discrepancies",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
