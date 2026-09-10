from django import forms

from .models import QualityReview, ReviewDecision


class QualityReviewForm(forms.ModelForm):
    class Meta:
        model = QualityReview
        fields = (
            "decision",
            "observations",
            "verified_physical_count",
            "verified_digital_count",
            "verified_individual_count",
            "verified_multi_count",
        )
        labels = {
            "decision": "Decisión",
            "observations": "Observaciones",
            "verified_physical_count": "Hojas físicas verificadas",
            "verified_digital_count": "TIFF verificados",
            "verified_individual_count": "TIFF individuales verificados",
            "verified_multi_count": "TIFF multi verificados",
        }
        widgets = {"observations": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        if user and user.has_perm("quality.observe_record"):
            choices.append((ReviewDecision.OBSERVED, ReviewDecision.OBSERVED.label))
        if user and user.has_perm("quality.validate_record"):
            choices.append((ReviewDecision.VALIDATED, ReviewDecision.VALIDATED.label))
        self.fields["decision"].choices = choices

    def clean(self):
        cleaned = super().clean()
        digital = cleaned.get("verified_digital_count")
        individual = cleaned.get("verified_individual_count")
        multi = cleaned.get("verified_multi_count")
        if None not in (digital, individual, multi) and individual + multi != digital:
            raise forms.ValidationError("Individuales + multi debe coincidir con TIFF verificados.")
        return cleaned
