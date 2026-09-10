from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect

from .forms import BatCsvImportForm, DigitalAssetForm, DigitalDocumentForm
from .services import (
    create_digital_asset,
    create_digital_document,
    import_bat_csv,
    inventory_record_tiffs,
)


def _error(request, exc):
    messages.error(request, "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc))


@permission_required("digitization.add_digitaldocument", raise_exception=True)
def document_add(request, record_pk):
    if request.method == "POST":
        form = DigitalDocumentForm(request.POST)
        if form.is_valid():
            try:
                create_digital_document(record_id=record_pk, actor=request.user, **form.cleaned_data)
            except (ValidationError, PermissionDenied) as exc:
                _error(request, exc)
            else:
                messages.success(request, "Documento lógico y modalidad registrados.")
    return redirect("record_detail", pk=record_pk)


@permission_required("digitization.add_digitalasset", raise_exception=True)
def asset_add(request, record_pk):
    if request.method == "POST":
        from apps.records.models import PersonnelRecord

        record = PersonnelRecord.objects.get(pk=record_pk)
        form = DigitalAssetForm(request.POST, record=record)
        if form.is_valid():
            try:
                create_digital_asset(record_id=record_pk, actor=request.user, **form.cleaned_data)
            except (ValidationError, PermissionDenied) as exc:
                _error(request, exc)
            else:
                messages.success(request, "Metadatos del TIFF registrados; no se movió el archivo.")
    return redirect("record_detail", pk=record_pk)


@permission_required("digitization.inventory_tiff", raise_exception=True)
def inventory_record(request, record_pk):
    if request.method == "POST":
        try:
            run = inventory_record_tiffs(
                record_id=record_pk,
                actor=request.user,
                relative_folder=request.POST.get("relative_folder") or None,
                compute_hashes=request.POST.get("compute_hashes") == "1",
            )
        except (ValidationError, PermissionDenied) as exc:
            _error(request, exc)
        else:
            messages.success(request, f"Inventario de solo lectura terminado: {run.discovered_count} TIFF.")
    return redirect("record_detail", pk=record_pk)


@permission_required("digitization.import_bat_csv", raise_exception=True)
def bat_import(request, batch_pk):
    if request.method == "POST":
        form = BatCsvImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                imported = import_bat_csv(
                    batch_id=batch_pk,
                    uploaded_file=form.cleaned_data["source_file"],
                    actor=request.user,
                )
            except (ValidationError, PermissionDenied) as exc:
                _error(request, exc)
            else:
                messages.success(
                    request,
                    f"CSV del BAT importado: {imported.accepted_rows} filas aceptadas, "
                    f"{imported.error_rows} con error.",
                )
    return redirect("batch_detail", pk=batch_pk)
