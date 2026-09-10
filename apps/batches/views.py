from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.digitization.forms import BatCsvImportForm
from apps.sources.forms import PayrollImportForm
from apps.sources.importers import XlsxPayrollImporter

from .forms import (
    BulkAssignmentForm,
    ExistingSourceForm,
    IntakeBatchForm,
    ManualRecordForm,
)
from .models import IntakeBatch
from .selectors import batches_for_user
from .services import (
    attach_source_import,
    batch_reconciliation,
    bulk_assign_records,
    create_manual_record,
    materialize_records_from_source,
)


@login_required
def batch_list(request):
    if not request.user.has_perm("batches.view_intakebatch"):
        raise PermissionDenied
    return render(
        request,
        "batches/list.html",
        {"batches": batches_for_user(request.user).select_related("responsible")},
    )


@permission_required("batches.receive_batch", raise_exception=True)
def batch_create(request):
    form = IntakeBatchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        batch = form.save(commit=False)
        batch.created_by = request.user
        batch.save()
        from apps.core.audit import audit_event

        audit_event(actor=request.user, action="batch.received", entity=batch, new={"code": batch.code})
        messages.success(request, "Lote recibido y registrado.")
        return redirect("batch_detail", pk=batch.pk)
    return render(request, "batches/form.html", {"form": form})


@login_required
def batch_detail(request, pk):
    if not request.user.has_perm("batches.view_intakebatch"):
        raise PermissionDenied
    batch = get_object_or_404(
        batches_for_user(request.user).select_related("responsible", "source_import", "expected_system"),
        pk=pk,
    )
    from apps.records.selectors import records_for_user

    visible_records = records_for_user(request.user).filter(batch=batch).select_related(
        "person", "current_custodian"
    )
    source_rows = batch.source_import.rows.all()[:100] if batch.source_import_id else []
    return render(
        request,
        "batches/detail.html",
        {
            "batch": batch,
            "records": visible_records,
            "reconciliation": batch_reconciliation(batch),
            "import_form": PayrollImportForm(),
            "manual_record_form": ManualRecordForm(),
            "bat_import_form": BatCsvImportForm(),
            "source_rows": source_rows,
            "bat_rows": batch.bat_rows.select_related("record", "csv_import")[:100],
            "bulk_assignment_form": BulkAssignmentForm(batch=batch),
            "existing_source_form": ExistingSourceForm(),
        },
    )


@permission_required(("sources.import_payroll", "batches.reconcile_batch"), raise_exception=True)
def batch_import_source(request, pk):
    if request.method != "POST":
        return redirect("batch_detail", pk=pk)
    form = PayrollImportForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            imported = XlsxPayrollImporter().import_file(
                uploaded_file=form.cleaned_data["source_file"],
                mapping=form.to_mapping(),
                actor=request.user,
            )
            attach_source_import(batch_id=pk, source_import=imported, actor=request.user)
        except (ValidationError, PermissionError) as exc:
            messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
        else:
            messages.success(request, "Fuente oficial importada y asociada al lote.")
    else:
        messages.error(request, "Revise los datos de importación: " + str(form.errors.as_text()))
    return redirect("batch_detail", pk=pk)


@permission_required(("sources.import_payroll", "batches.reconcile_batch"), raise_exception=True)
def batch_attach_existing_source(request, pk):
    if request.method == "POST":
        form = ExistingSourceForm(request.POST)
        if form.is_valid():
            try:
                attach_source_import(
                    batch_id=pk,
                    source_import=form.cleaned_data["source_import"],
                    actor=request.user,
                )
            except (ValidationError, PermissionError) as exc:
                messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
            else:
                messages.success(request, "Fuente oficial existente asociada al lote.")
    return redirect("batch_detail", pk=pk)


@permission_required("batches.reconcile_batch", raise_exception=True)
def batch_materialize(request, pk):
    if request.method == "POST":
        try:
            created, existing = materialize_records_from_source(batch_id=pk, actor=request.user)
        except (ValidationError, PermissionError) as exc:
            messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
        else:
            messages.success(request, f"Expedientes creados: {created}. Ya existentes: {existing}.")
    return redirect("batch_detail", pk=pk)


@permission_required("batches.reconcile_batch", raise_exception=True)
def batch_add_record(request, pk):
    if request.method == "POST":
        form = ManualRecordForm(request.POST)
        if form.is_valid():
            try:
                record = create_manual_record(
                    batch_id=pk,
                    actor=request.user,
                    curp=form.cleaned_data["curp"],
                    full_name=form.cleaned_data["full_name"],
                    physical_identifier=form.cleaned_data["physical_identifier"],
                    systems=form.cleaned_data["declared_systems"],
                )
            except (ValidationError, PermissionError) as exc:
                messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
            else:
                messages.success(request, "Expediente físico registrado; queda visible la falta de fila oficial.")
                return redirect("record_detail", pk=record.pk)
        else:
            messages.error(request, "Revise los datos del expediente: " + str(form.errors.as_text()))
    return redirect("batch_detail", pk=pk)


@permission_required("records.assign_record", raise_exception=True)
def batch_assign(request, pk):
    batch = get_object_or_404(IntakeBatch, pk=pk)
    if request.method == "POST":
        form = BulkAssignmentForm(request.POST, batch=batch)
        if form.is_valid():
            try:
                assignments = bulk_assign_records(
                    batch_id=batch.pk,
                    record_ids=form.cleaned_data["records"].values_list("pk", flat=True),
                    digitalizer=form.cleaned_data["digitalizer"],
                    actor=request.user,
                    reason=form.cleaned_data["reason"],
                )
            except (ValidationError, PermissionError) as exc:
                messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))
            else:
                messages.success(request, f"Expedientes asignados: {len(assignments)}.")
    return redirect("batch_detail", pk=pk)
