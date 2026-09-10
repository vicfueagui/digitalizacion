from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.records.models import RecordStatus
from apps.records.selectors import records_for_user

from .forms import QualityReviewForm
from .services import review_record


def _may_review(user):
    return user.has_perm("quality.observe_record") or user.has_perm("quality.validate_record")


@login_required
def review_queue(request):
    if not _may_review(request.user):
        raise PermissionDenied
    records = records_for_user(request.user).filter(
        status__in=(RecordStatus.READY_FOR_REVIEW, RecordStatus.CORRECTED)
    ).select_related("person", "batch", "current_custodian")
    return render(request, "quality/queue.html", {"records": records})


@login_required
def review_detail(request, pk):
    if not _may_review(request.user):
        raise PermissionDenied
    record = get_object_or_404(
        records_for_user(request.user).select_related("person", "batch", "current_custodian"),
        pk=pk,
        status__in=(RecordStatus.READY_FOR_REVIEW, RecordStatus.CORRECTED),
    )
    form = QualityReviewForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            review_record(record_id=record.pk, actor=request.user, **form.cleaned_data)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
        else:
            messages.success(request, "Revisión registrada sin borrar antecedentes.")
            return redirect("review_queue")
    return render(request, "quality/detail.html", {"record": record, "form": form})
