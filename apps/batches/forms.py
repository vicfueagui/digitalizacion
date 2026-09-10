from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.people.models import AdministrativeSystem
from apps.records.models import PersonnelRecord, RecordStatus
from apps.sources.models import ImportStatus, PayrollImport

from .models import IntakeBatch


class DateInput(forms.DateInput):
    input_type = "date"


class IntakeBatchForm(forms.ModelForm):
    class Meta:
        model = IntakeBatch
        fields = ("code", "received_at", "responsible", "expected_system", "expected_records", "notes")
        widgets = {"received_at": DateInput(), "notes": forms.Textarea(attrs={"rows": 3})}
        labels = {
            "code": "Identificador del lote",
            "received_at": "Fecha de recepción",
            "responsible": "Responsable que recibe",
            "expected_system": "Sistema esperado para el trabajo",
            "expected_records": "Expedientes físicos esperados",
            "notes": "Observaciones",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsible"].queryset = get_user_model().objects.filter(is_active=True).order_by("username")
        self.fields["expected_system"].queryset = AdministrativeSystem.objects.filter(active=True)


class ManualRecordForm(forms.Form):
    curp = forms.CharField(label="CURP", max_length=30)
    full_name = forms.CharField(label="Nombre", max_length=250, required=False)
    physical_identifier = forms.CharField(
        label="Identificador físico del folder", max_length=120, required=False
    )
    declared_systems = forms.ModelMultipleChoiceField(
        label="Sistemas declarados",
        queryset=AdministrativeSystem.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["declared_systems"].queryset = AdministrativeSystem.objects.filter(active=True)

    def clean_curp(self):
        from apps.people.validators import normalize_curp, validate_curp

        value = normalize_curp(self.cleaned_data["curp"])
        validate_curp(value)
        return value


class BulkAssignmentForm(forms.Form):
    records = forms.ModelMultipleChoiceField(
        label="Expedientes",
        queryset=PersonnelRecord.objects.none(),
        widget=forms.CheckboxSelectMultiple,
    )
    digitalizer = forms.ModelChoiceField(
        label="Digitalizador",
        queryset=get_user_model().objects.none(),
    )
    reason = forms.CharField(label="Nota o motivo", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, batch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["records"].queryset = (
            batch.records.filter(status__in=(RecordStatus.RECEIVED, RecordStatus.ASSIGNED)).select_related("person")
            if batch is not None
            else PersonnelRecord.objects.none()
        )
        self.fields["digitalizer"].queryset = (
            get_user_model()
            .objects.filter(is_active=True)
            .filter(
                Q(is_superuser=True)
                | Q(
                    groups__permissions__content_type__app_label="records",
                    groups__permissions__codename="work_on_record",
                )
                | Q(
                    user_permissions__content_type__app_label="records",
                    user_permissions__codename="work_on_record",
                )
            )
            .distinct()
            .order_by("username")
        )


class ExistingSourceForm(forms.Form):
    source_import = forms.ModelChoiceField(
        label="Fuente ya importada",
        queryset=PayrollImport.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_import"].queryset = PayrollImport.objects.filter(
            status__in=(ImportStatus.COMPLETED, ImportStatus.COMPLETED_WITH_ERRORS)
        ).order_by("-imported_at")
