from django import forms

from .models import DigitalAsset, DigitalDocument, DocumentType


class DigitalDocumentForm(forms.ModelForm):
    class Meta:
        model = DigitalDocument
        fields = ("document_type", "scan_mode", "other_mode_description", "sequence")
        labels = {
            "document_type": "Tipo documental confirmado",
            "scan_mode": "Modalidad de escaneo",
            "other_mode_description": "Descripción si elige Otra",
            "sequence": "Orden en el expediente",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document_type"].queryset = DocumentType.objects.filter(active=True)


class DigitalAssetForm(forms.ModelForm):
    class Meta:
        model = DigitalAsset
        fields = ("document", "filename", "relative_path", "extension", "file_size", "sha256", "page_count")
        labels = {
            "document": "Documento lógico",
            "filename": "Nombre del TIFF",
            "relative_path": "Ruta relativa",
            "extension": "Extensión",
            "file_size": "Tamaño en bytes",
            "sha256": "SHA-256",
            "page_count": "Páginas digitales (si se verificaron)",
        }

    def __init__(self, *args, record=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document"].queryset = (
            record.documents.all() if record is not None else DigitalDocument.objects.none()
        )


class BatCsvImportForm(forms.Form):
    source_file = forms.FileField(
        label="Resumen CSV del BAT",
        help_text="Acepta RESUMEN_DIGITALIZACION.csv o CONTROL_DIGITALIZACION.csv.",
    )

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        if not uploaded.name.lower().endswith(".csv"):
            raise forms.ValidationError("Seleccione un archivo .csv.")
        from django.conf import settings

        if uploaded.size > settings.MAX_IMPORT_FILE_BYTES:
            raise forms.ValidationError("El archivo excede el límite configurado.")
        return uploaded
