from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.digitization.forms import DigitalAssetForm, DigitalDocumentForm
from apps.digitization.services import record_reconciliation

from .forms import (
    AssignmentForm,
    IncidentForm,
    NotesForm,
    PhysicalCountForm,
    ResolutionForm,
)
from .models import Incident, RecordStatus
from .selectors import records_for_user
from .services import (
    accept_assignment,
    assign_record,
    close_record,
    register_incident,
    register_physical_count,
    resolve_incident,
    start_work,
    submit_correction,
    submit_for_review,
)


def _message_exception(request, exc):
    messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))


@login_required
def record_list(request):
    records = records_for_user(request.user).select_related(
        "person", "batch", "expected_system", "current_custodian"
    )
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status in RecordStatus.values:
        records = records.filter(status=status)
    if query:
        records = records.filter(Q(person__curp__icontains=query) | Q(person__full_name__icontains=query))
    return render(
        request,
        "records/list.html",
        {"records": records, "status_choices": RecordStatus.choices, "selected_status": status, "query": query},
    )


@login_required
def record_detail(request, pk):
    record = get_object_or_404(
        records_for_user(request.user).select_related(
            "person", "batch", "source_row", "expected_system", "current_custodian"
        ),
        pk=pk,
    )
    return render(
        request,
        "records/detail.html",
        {
            "record": record,
            "assignment_form": AssignmentForm(),
            "physical_form": PhysicalCountForm(),
            "incident_form": IncidentForm(),
            "notes_form": NotesForm(),
            "resolution_form": ResolutionForm(),
            "document_form": DigitalDocumentForm(),
            "asset_form": DigitalAssetForm(record=record),
            "reconciliation": record_reconciliation(record),
            "current_assignment": record.current_assignment,
        },
    )


@permission_required("records.assign_record", raise_exception=True)
def record_assign(request, pk):
    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            try:
                assign_record(
                    record_id=pk,
                    digitalizer=form.cleaned_data["digitalizer"],
                    actor=request.user,
                    reason=form.cleaned_data["reason"],
                )
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Expediente asignado con historial de custodia.")
    return redirect("record_detail", pk=pk)


@permission_required("records.work_on_record", raise_exception=True)
def record_accept(request, pk):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            try:
                accept_assignment(record_id=pk, actor=request.user, notes=form.cleaned_data["notes"])
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Recepción y correspondencia confirmadas.")
    return redirect("record_detail", pk=pk)


@permission_required("records.work_on_record", raise_exception=True)
def record_start(request, pk):
    if request.method == "POST":
        try:
            start_work(record_id=pk, actor=request.user)
        except (ValidationError, PermissionDenied) as exc:
            _message_exception(request, exc)
        else:
            messages.success(request, "Trabajo iniciado.")
    return redirect("record_detail", pk=pk)


@permission_required("records.add_physicalcount", raise_exception=True)
def record_add_physical_count(request, pk):
    if request.method == "POST":
        form = PhysicalCountForm(request.POST)
        if form.is_valid():
            try:
                register_physical_count(
                    record_id=pk,
                    sheet_count=form.cleaned_data["sheet_count"],
                    correction_reason=form.cleaned_data["correction_reason"],
                    actor=request.user,
                )
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Conteo físico agregado; los anteriores se conservaron.")
    return redirect("record_detail", pk=pk)


@permission_required("records.add_incident", raise_exception=True)
def record_add_incident(request, pk):
    if request.method == "POST":
        form = IncidentForm(request.POST)
        if form.is_valid():
            try:
                register_incident(record_id=pk, actor=request.user, **form.cleaned_data)
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Incidencia registrada.")
    return redirect("record_detail", pk=pk)


@permission_required("records.submit_record", raise_exception=True)
def record_submit(request, pk):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            try:
                submit_for_review(record_id=pk, actor=request.user, notes=form.cleaned_data["notes"])
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Expediente terminado por el digitalizador y enviado a revisión.")
    return redirect("record_detail", pk=pk)


@permission_required("records.correct_record", raise_exception=True)
def record_corrected(request, pk):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            try:
                submit_correction(record_id=pk, actor=request.user, notes=form.cleaned_data["notes"])
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Corrección enviada a revisión.")
    return redirect("record_detail", pk=pk)


@permission_required("records.close_record", raise_exception=True)
def record_close(request, pk):
    if request.method == "POST":
        form = NotesForm(request.POST)
        if form.is_valid():
            try:
                close_record(record_id=pk, actor=request.user, reason=form.cleaned_data["notes"])
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Expediente cerrado finalmente.")
    return redirect("record_detail", pk=pk)


@permission_required("records.change_incident", raise_exception=True)
def incident_resolve(request, pk):
    incident = get_object_or_404(Incident.objects.select_related("record"), pk=pk)
    if request.method == "POST":
        form = ResolutionForm(request.POST)
        if form.is_valid():
            try:
                resolve_incident(
                    incident_id=incident.pk,
                    resolution=form.cleaned_data["resolution"],
                    actor=request.user,
                )
            except (ValidationError, PermissionDenied) as exc:
                _message_exception(request, exc)
            else:
                messages.success(request, "Incidencia resuelta; el registro original se conservó.")
    return redirect("record_detail", pk=incident.record_id)
