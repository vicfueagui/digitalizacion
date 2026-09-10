import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.batches.models import IntakeBatch
from apps.core.audit import audit_event
from apps.people.validators import normalize_curp, validate_curp
from apps.records.models import PersonnelRecord
from apps.records.selectors import user_can_access_record

from .models import (
    AssetStatus,
    BatCsvImport,
    BatCsvRow,
    BatImportStatus,
    BatRowStatus,
    DigitalAsset,
    DigitalDocument,
    DigitalInventoryRun,
    DocumentType,
    ScanMode,
)
from .storage import LocalReadOnlyTiffStorage


def _require_record_edit(record, actor, permission):
    if not actor.has_perm(permission):
        raise PermissionDenied("No tiene el permiso requerido.")
    if not (actor.is_superuser or actor.has_perm("records.view_all_records")):
        assigned = record.assignments.filter(digitalizer=actor, ended_at__isnull=True).exists()
        if not assigned:
            raise PermissionDenied("El expediente no está asignado actualmente a este usuario.")


@transaction.atomic
def create_digital_document(*, record_id, actor, **data):
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    _require_record_edit(record, actor, "digitization.add_digitaldocument")
    document = DigitalDocument(record=record, classification_confirmed_by=actor, **data)
    document.full_clean()
    document.save()
    audit_event(
        actor=actor,
        action="digital_document.classified",
        entity=document,
        new={
            "record_id": record.pk,
            "document_type": document.document_type.code,
            "scan_mode": document.scan_mode,
            "scan_mode_group": document.scan_mode_group,
        },
    )
    return document


@transaction.atomic
def create_digital_asset(*, record_id, actor, **data):
    record = PersonnelRecord.objects.select_for_update().get(pk=record_id)
    _require_record_edit(record, actor, "digitization.add_digitalasset")
    filename = data["filename"]
    prefix = filename.split("-", 1)[0].upper() if "-" in filename else ""
    document_type = DocumentType.objects.filter(code=prefix, active=True).first()
    parent_folder = PurePosixPath(data["relative_path"].replace("\\", "/")).parent.name.upper()
    status = (
        AssetStatus.PRESENT
        if document_type and parent_folder == document_type.destination_folder.upper()
        else AssetStatus.UNEXPECTED
    )
    asset = DigitalAsset(record=record, detected_prefix=prefix, status=status, **data)
    asset.full_clean()
    asset.save()
    audit_event(
        actor=actor,
        action="tiff_asset.registered",
        entity=asset,
        new={"record_id": record.pk, "relative_path": asset.relative_path, "sha256": asset.sha256},
    )
    return asset


@transaction.atomic
def inventory_record_tiffs(*, record_id, actor, relative_folder=None, compute_hashes=False):
    if not actor.has_perm("digitization.inventory_tiff"):
        raise PermissionDenied("No tiene permiso para inventariar TIFF.")
    record = PersonnelRecord.objects.select_for_update().select_related("person").get(pk=record_id)
    if not user_can_access_record(actor, record):
        raise PermissionDenied("No tiene acceso a este expediente.")
    folder = relative_folder or record.person.curp
    storage = LocalReadOnlyTiffStorage(settings.DIGITAL_REPOSITORY_ROOT)
    target = storage.resolve_folder(folder)
    run = DigitalInventoryRun.objects.create(
        record=record,
        root_relative_path=target.relative_to(storage.root).as_posix(),
        requested_by=actor,
        compute_hashes=compute_hashes,
    )
    type_destinations = {
        item.code.upper(): item.destination_folder.upper()
        for item in DocumentType.objects.filter(active=True)
    }
    seen_paths = set()
    prefix_counts = Counter()
    folder_counts = Counter()
    unexpected_count = 0
    for path in storage.iter_tiffs(folder):
        relative_to_record = path.relative_to(target).as_posix()
        stored_relative = (Path(folder) / relative_to_record).as_posix()
        seen_paths.add(stored_relative)
        prefix = path.name.split("-", 1)[0].upper() if "-" in path.name else ""
        parent_folder = path.parent.name.upper()
        expected_folder = type_destinations.get(prefix)
        unexpected = not expected_folder or parent_folder != expected_folder
        status = AssetStatus.UNEXPECTED if unexpected else AssetStatus.PRESENT
        previous = DigitalAsset.objects.filter(record=record, relative_path=stored_relative).first()
        defaults = {
            "filename": path.name,
            "extension": path.suffix.lower().lstrip("."),
            "file_size": path.stat().st_size,
            "detected_prefix": prefix,
            "status": status,
            "last_verified_at": timezone.now(),
        }
        if compute_hashes:
            defaults["sha256"] = storage.sha256(path)
        asset, created = DigitalAsset.objects.update_or_create(
            record=record,
            relative_path=stored_relative,
            defaults=defaults,
        )
        if previous and not created:
            audit_event(
                actor=actor,
                action="tiff_asset.verified",
                entity=asset,
                previous={"file_size": previous.file_size, "sha256": previous.sha256, "status": previous.status},
                new={"file_size": asset.file_size, "sha256": asset.sha256, "status": asset.status},
                context={"inventory_run_id": run.pk},
            )
        elif created:
            audit_event(
                actor=actor,
                action="tiff_asset.discovered",
                entity=asset,
                new={
                    "relative_path": asset.relative_path,
                    "file_size": asset.file_size,
                    "sha256": asset.sha256,
                    "status": asset.status,
                },
                context={"inventory_run_id": run.pk},
            )
        prefix_counts[prefix or "SIN_PREFIJO"] += 1
        folder_counts[parent_folder or "RAIZ"] += 1
        unexpected_count += int(unexpected)

    missing = record.digital_assets.exclude(relative_path__in=seen_paths).exclude(status=AssetStatus.MISSING)
    missing_count = missing.count()
    for asset in missing:
        previous_status = asset.status
        asset.status = AssetStatus.MISSING
        asset.last_verified_at = timezone.now()
        asset.save(update_fields=("status", "last_verified_at", "updated_at"))
        audit_event(
            actor=actor,
            action="tiff_asset.missing_on_verification",
            entity=asset,
            previous={"status": previous_status},
            new={"status": AssetStatus.MISSING},
            context={"inventory_run_id": run.pk},
        )

    summary = {
        "total": len(seen_paths),
        "prefix_counts": dict(prefix_counts),
        "folder_counts": dict(folder_counts),
        "unexpected": unexpected_count,
        "missing": missing_count,
        "skipped_outside_root": storage.skipped_outside_root,
    }
    run.finished_at = timezone.now()
    run.discovered_count = len(seen_paths)
    run.unexpected_count = unexpected_count
    run.summary = summary
    run.save(update_fields=("finished_at", "discovered_count", "unexpected_count", "summary"))
    audit_event(actor=actor, action="tiff_inventory.completed", entity=run, new=summary)
    return run


def inspect_scanner_inbox():
    root_setting = settings.SCANNER_INBOX_ROOT
    if not root_setting:
        raise ValidationError("SCANNER_INBOX_ROOT no está configurado.")
    root = Path(root_setting).expanduser().resolve()
    if not root.is_dir():
        raise ValidationError("SCANNER_INBOX_ROOT no existe o no es una carpeta.")
    files = [item.name for item in root.iterdir() if item.is_file() and item.suffix.lower() in {".tif", ".tiff"}]
    return {"count": len(files), "filenames": sorted(files)}


def _decode_csv(uploaded_file):
    uploaded_file.seek(0)
    content = uploaded_file.read()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return content.decode(encoding), content
        except UnicodeDecodeError:
            continue
    raise ValidationError("El CSV debe estar codificado como UTF-8 o Windows-1252.")


def _optional_int(payload, key, errors):
    raw = str(payload.get(key, "") or "").strip()
    if not raw or raw.upper() == "NO_CAPTURADO":
        return None
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"{key} debe ser un entero o NO_CAPTURADO.")
        return None
    if value < 0:
        errors.append(f"{key} no puede ser negativo.")
        return None
    return value


@transaction.atomic
def import_bat_csv(*, batch_id, uploaded_file, actor):
    if not (
        actor.has_perm("digitization.import_bat_csv")
        and actor.has_perm("batches.reconcile_batch")
    ):
        raise PermissionDenied("No tiene permiso para importar resúmenes del BAT.")
    if uploaded_file.size > settings.MAX_IMPORT_FILE_BYTES:
        raise ValidationError("El archivo excede el límite configurado.")
    batch = IntakeBatch.objects.select_for_update().get(pk=batch_id)
    text, content = _decode_csv(uploaded_file)
    digest = hashlib.sha256(content).hexdigest()
    if BatCsvImport.objects.filter(sha256=digest).exists():
        raise ValidationError("Este CSV ya fue importado; coincide su hash SHA-256.")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    required = {"CURP", "FISICOS", "DIGITALES", "INDIVIDUALES", "MULTI", "RESULTADO"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise ValidationError("El CSV no contiene las columnas obligatorias generadas por el BAT v2.")

    csv_import = BatCsvImport.objects.create(
        batch=batch,
        source_file_name=uploaded_file.name[:255],
        sha256=digest,
        imported_by=actor,
        status=BatImportStatus.COMPLETED,
    )
    accepted = 0
    error_count = 0
    row_count = 0
    for row_number, source_payload in enumerate(reader, start=2):
        if not any(str(value or "").strip() for value in source_payload.values()):
            continue
        row_count += 1
        payload = {str(key): str(value or "") for key, value in source_payload.items() if key is not None}
        errors = []
        discrepancies = []
        curp = normalize_curp(payload.get("CURP", ""))
        try:
            validate_curp(curp)
        except ValidationError as exc:
            errors.extend(exc.messages)
        physical = _optional_int(payload, "FISICOS", errors)
        digital = _optional_int(payload, "DIGITALES", errors)
        individual = _optional_int(payload, "INDIVIDUALES", errors)
        multi = _optional_int(payload, "MULTI", errors)
        if None not in (digital, individual, multi) and individual + multi != digital:
            errors.append("INDIVIDUALES + MULTI no coincide con DIGITALES.")
        record = batch.records.filter(person__curp=curp).first() if not errors else None
        if not errors and record is None:
            errors.append("La CURP no existe como expediente dentro de este lote.")

        row_hash = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        duplicate = BatCsvRow.objects.filter(batch=batch, row_hash=row_hash).exists()
        if duplicate:
            status = BatRowStatus.DUPLICATE
            errors.append("Esta fila ya fue importada previamente para el lote.")
        elif errors:
            status = BatRowStatus.ERROR
        else:
            latest_physical = record.latest_physical_count
            if physical is not None and latest_physical and latest_physical.sheet_count != physical:
                discrepancies.append(
                    {
                        "code": "physical_count_mismatch",
                        "captured": latest_physical.sheet_count,
                        "bat": physical,
                    }
                )
            inventory_total = record.digital_assets.exclude(status=AssetStatus.MISSING).count()
            if digital is not None and inventory_total and inventory_total != digital:
                discrepancies.append(
                    {"code": "digital_count_mismatch", "inventory": inventory_total, "bat": digital}
                )
            status = BatRowStatus.DISCREPANCY if discrepancies else BatRowStatus.ACCEPTED

        BatCsvRow.objects.create(
            csv_import=csv_import,
            batch=batch,
            row_number=row_number,
            record=record,
            curp=curp if len(curp) <= 18 else "",
            physical_count=physical,
            digital_count=digital,
            individual_count=individual,
            multi_count=multi,
            organization_result=payload.get("RESULTADO", "")[:30],
            status=status,
            raw_payload=payload,
            errors=errors,
            discrepancies=discrepancies,
            row_hash=row_hash,
        )
        if status in (BatRowStatus.ERROR, BatRowStatus.DUPLICATE):
            error_count += 1
        else:
            accepted += 1

    csv_import.row_count = row_count
    csv_import.accepted_rows = accepted
    csv_import.error_rows = error_count
    csv_import.status = BatImportStatus.WITH_ERRORS if error_count else BatImportStatus.COMPLETED
    csv_import.save(update_fields=("row_count", "accepted_rows", "error_rows", "status"))
    audit_event(
        actor=actor,
        action="bat_csv.imported",
        entity=csv_import,
        new={"rows": row_count, "accepted": accepted, "errors": error_count, "sha256": digest},
    )
    return csv_import


def record_reconciliation(record):
    active_assets = record.digital_assets.exclude(status=AssetStatus.MISSING)
    digital_total = active_assets.count()
    individual = active_assets.filter(
        document__scan_mode__in=(ScanMode.INDIVIDUAL_ONE_SIDE, ScanMode.INDIVIDUAL_DUPLEX)
    ).count()
    multi = active_assets.filter(document__scan_mode=ScanMode.MULTI_ONE_SIDE).count()
    other_or_unclassified = digital_total - individual - multi
    recognized_prefixes = set(DocumentType.objects.filter(active=True).values_list("code", flat=True))
    recognized_count = active_assets.filter(detected_prefix__in=recognized_prefixes).count()
    unexpected_count = active_assets.filter(status=AssetStatus.UNEXPECTED).count()
    physical = record.latest_physical_count
    return {
        "physical_count_exists": {
            "ok": physical is not None,
            "actual": physical.sheet_count if physical else None,
        },
        "source_row_matches_record": {"ok": record.source_row_id is not None},
        "digital_total_matches_inventory": {"ok": True, "actual": digital_total},
        "individual_plus_multi_equals_digital_total": {
            "ok": other_or_unclassified == 0,
            "individual": individual,
            "multi": multi,
            "digital_total": digital_total,
            "unclassified_or_other": other_or_unclassified,
        },
        "prefix_counts_match_digital_total": {
            "ok": recognized_count == digital_total,
            "recognized": recognized_count,
            "digital_total": digital_total,
        },
        "unexpected_files_count": {"ok": unexpected_count == 0, "actual": unexpected_count},
    }
