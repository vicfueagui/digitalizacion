from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from apps.digitization.models import AssetStatus, DigitalAsset, ScanMode
from apps.digitization.services import record_reconciliation
from apps.quality.models import QualityReview, ReviewDecision
from apps.records.models import Incident, RecordStatus
from apps.records.selectors import records_for_user


@permission_required("reports.view_operational_reports", raise_exception=True)
def operational_report(request):
    records = records_for_user(request.user).select_related("person", "batch", "current_custodian")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    batch = request.GET.get("batch", "")
    digitalizer = request.GET.get("digitalizer", "")
    status = request.GET.get("status", "")
    if date_from:
        records = records.filter(updated_at__date__gte=date_from)
    if date_to:
        records = records.filter(updated_at__date__lte=date_to)
    if batch:
        records = records.filter(batch__code__icontains=batch)
    if digitalizer:
        records = records.filter(current_custodian__username__icontains=digitalizer)
    if status in RecordStatus.values:
        records = records.filter(status=status)
    records = records.distinct()

    record_ids = list(records.values_list("id", flat=True))
    physical_total = sum(
        item.latest_physical_count.sheet_count
        for item in records
        if item.latest_physical_count is not None
    )
    assets = DigitalAsset.objects.filter(record_id__in=record_ids).exclude(status=AssetStatus.MISSING)
    individual = assets.filter(
        document__scan_mode__in=(ScanMode.INDIVIDUAL_ONE_SIDE, ScanMode.INDIVIDUAL_DUPLEX)
    ).count()
    multi = assets.filter(document__scan_mode=ScanMode.MULTI_ONE_SIDE).count()
    incidents = Incident.objects.filter(record_id__in=record_ids)
    observed = (
        QualityReview.objects.filter(record_id__in=record_ids, decision=ReviewDecision.OBSERVED)
        .values("record_id")
        .distinct()
        .count()
    )
    differences = sum(
        any(not check["ok"] for check in record_reconciliation(item).values()) for item in records
    )
    metrics = {
        "records": len(record_ids),
        "physical": physical_total,
        "digital": assets.count(),
        "individual": individual,
        "multi": multi,
        "incidents": incidents.count(),
        "observed": observed,
        "validated": records.filter(status__in=(RecordStatus.VALIDATED, RecordStatus.CLOSED)).count(),
        "differences": differences,
    }
    return render(
        request,
        "reports/operational.html",
        {
            "records": records,
            "metrics": metrics,
            "status_choices": RecordStatus.choices,
            "filters": request.GET,
        },
    )
