from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Incident, IncidentType, PhysicalCount


class AssignmentForm(forms.Form):
    digitalizer = forms.ModelChoiceField(label="Digitalizador", queryset=get_user_model().objects.none())
    reason = forms.CharField(label="Nota o motivo", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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


class PhysicalCountForm(forms.ModelForm):
    class Meta:
        model = PhysicalCount
        fields = ("sheet_count", "correction_reason")
        labels = {"sheet_count": "Hojas físicas", "correction_reason": "Motivo del reconteo"}
        widgets = {"correction_reason": forms.Textarea(attrs={"rows": 2})}


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ("incident_type", "stage", "description")
        labels = {"incident_type": "Tipo", "stage": "Etapa", "description": "Notas o evidencia"}
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["incident_type"].queryset = IncidentType.objects.filter(active=True)


class NotesForm(forms.Form):
    notes = forms.CharField(label="Notas", required=False, widget=forms.Textarea(attrs={"rows": 2}))


class ResolutionForm(forms.Form):
    resolution = forms.CharField(label="Resolución", widget=forms.Textarea(attrs={"rows": 2}))
