from typing import Protocol

from django.core.files.uploadedfile import UploadedFile

from .models import PayrollImport


class PayrollSourceImporter(Protocol):
    """Contrato para agregar formatos de fuente sin mezclar el dominio."""

    extension: str

    def import_file(self, *, uploaded_file: UploadedFile, mapping: dict, actor) -> PayrollImport: ...


class XlsxPayrollImporter:
    extension = ".xlsx"

    def import_file(self, *, uploaded_file, mapping, actor):
        from .services import import_payroll_xlsx

        return import_payroll_xlsx(uploaded_file=uploaded_file, mapping=mapping, actor=actor)
