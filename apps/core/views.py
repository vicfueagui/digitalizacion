from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from apps.batches.selectors import batches_for_user
from apps.records.models import RecordStatus, RecordStatusTransition
from apps.records.selectors import records_for_user


@login_required
def dashboard(request):
    records = records_for_user(request.user)
    batches = batches_for_user(request.user)
    status_counts = dict(
        records.values_list("status").annotate(total=Count("id")).values_list("status", "total")
    )
    cards = [
        ("Recibidos", RecordStatus.RECEIVED, "secondary"),
        ("Asignados", RecordStatus.ASSIGNED, "info"),
        ("En proceso", RecordStatus.IN_PROGRESS, "primary"),
        ("Pendientes de revisión", RecordStatus.READY_FOR_REVIEW, "warning"),
        ("Observados", RecordStatus.OBSERVED, "danger"),
        ("Corregidos", RecordStatus.CORRECTED, "warning"),
        ("Validados", RecordStatus.VALIDATED, "success"),
    ]
    now = timezone.localdate()
    batch_alerts = (
        sum(
            batch.records.count() != batch.expected_records
            or batch.records.filter(source_row__isnull=True).exists()
            for batch in batches
        )
        if request.user.has_perm("batches.reconcile_batch")
        else 0
    )
    submitted_this_month = RecordStatusTransition.objects.filter(
        record__in=records,
        to_status=RecordStatus.READY_FOR_REVIEW,
        occurred_at__year=now.year,
        occurred_at__month=now.month,
    ).count()
    return render(
        request,
        "core/dashboard.html",
        {
            "cards": [(label, status, color, status_counts.get(status, 0)) for label, status, color in cards],
            "recent_records": records.select_related("person", "batch").order_by("-updated_at")[:10],
            "operational_summary": {
                "Lotes visibles": batches.count(),
                "Pendientes de asignar": status_counts.get(RecordStatus.RECEIVED, 0),
                "Alertas de lote": batch_alerts,
                "Enviados a revisión este mes": submitted_this_month,
            },
        },
    )
