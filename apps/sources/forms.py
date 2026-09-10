from django import forms


class PayrollImportForm(forms.Form):
    source_file = forms.FileField(
        label="Archivo Excel (.xlsx)",
        help_text="Se conserva una copia y su hash SHA-256 para trazabilidad.",
    )
    sheet_name = forms.CharField(
        label="Nombre de hoja",
        required=False,
        help_text="Vacío: usa la hoja activa.",
    )
    header_row = forms.IntegerField(label="Fila de encabezados", min_value=1, initial=1)
    curp_column = forms.CharField(label="Encabezado de CURP", initial="CURP")
    name_column = forms.CharField(label="Encabezado de nombre", required=False)
    status_column = forms.CharField(label="Encabezado de estado laboral", required=False)
    systems_column = forms.CharField(
        label="Encabezado de sistema(s)",
        required=False,
        help_text="Para una celda que indica Federal, Estatal o ambos.",
    )
    federal_column = forms.CharField(
        label="Encabezado indicador Federal",
        required=False,
        help_text="Use si Federal viene en una columna separada.",
    )
    state_column = forms.CharField(
        label="Encabezado indicador Estatal",
        required=False,
        help_text="Use si Estatal viene en una columna separada.",
    )
    federal_values = forms.CharField(
        label="Valores que significan Federal",
        required=False,
        help_text="Separe valores con coma; no se asumen valores del archivo real.",
    )
    state_values = forms.CharField(
        label="Valores que significan Estatal",
        required=False,
        help_text="Separe valores con coma; no se asumen valores del archivo real.",
    )
    active_values = forms.CharField(
        label="Valores que significan Activo",
        required=False,
        help_text="Separe valores con coma.",
    )
    inactive_values = forms.CharField(
        label="Valores que significan Inactivo",
        required=False,
        help_text="Separe valores con coma.",
    )

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        if not uploaded.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("En esta etapa solamente se aceptan archivos .xlsx.")
        from django.conf import settings

        if uploaded.size > settings.MAX_IMPORT_FILE_BYTES:
            raise forms.ValidationError("El archivo excede el límite configurado.")
        return uploaded

    def to_mapping(self):
        data = self.cleaned_data

        def split_values(name):
            return [item.strip() for item in data.get(name, "").split(",") if item.strip()]

        return {
            "sheet_name": data.get("sheet_name", "").strip(),
            "header_row": data["header_row"],
            "curp": data["curp_column"].strip(),
            "name": data.get("name_column", "").strip(),
            "employment_status": data.get("status_column", "").strip(),
            "systems": data.get("systems_column", "").strip(),
            "federal_flag": data.get("federal_column", "").strip(),
            "state_flag": data.get("state_column", "").strip(),
            "federal_values": split_values("federal_values"),
            "state_values": split_values("state_values"),
            "active_values": split_values("active_values"),
            "inactive_values": split_values("inactive_values"),
        }
