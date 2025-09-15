from django import forms
from .models import Project, Indicator, IndicatorTarget
from django.utils import timezone
from decimal import Decimal, InvalidOperation


# -----------------------------
# Project Form
# -----------------------------
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "start_year", "end_year", "active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "start_year": forms.NumberInput(attrs={"class": "form-control"}),
            "end_year": forms.NumberInput(attrs={"class": "form-control"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# -----------------------------
# Indicator Form (with Target + Year selection)
# -----------------------------
class IndicatorForm(forms.ModelForm):
    # Target value
    target = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        label="Annual Target",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        error_messages={"invalid": "Target value must be numeric."},
    )

    # Year selection dropdown
    year = forms.ChoiceField(
        label="Year",
        choices=[(y, y) for y in range(timezone.now().year, timezone.now().year + 6)],
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Indicator
        fields = ["name", "unit", "is_kpi", "target", "year"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "is_kpi": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_year = timezone.now().year
        self.fields["year"].initial = current_year  # default selection

        # If instance exists, prefill target for selected year
        if self.instance and self.instance.pk:
            selected_year = self.initial.get("year", current_year)
            target_obj = self.instance.targets.filter(year=selected_year).first()
            if target_obj:
                self.fields["target"].initial = target_obj.value

    def clean_target(self):
        value = self.cleaned_data.get("target")
        if value is not None:
            try:
                Decimal(value)
            except (InvalidOperation, TypeError):
                raise forms.ValidationError("Target value must be numeric.")
        return value

    def save(self, commit=True):
        # Save the Indicator instance first
        indicator = super().save(commit=False)
        if commit:
            indicator.save()  # Must save before using in related filters

        # Save or update the target for chosen year
        target_val = self.cleaned_data.get("target")
        selected_year = int(self.cleaned_data.get("year"))

        if target_val is not None and indicator.pk:
            IndicatorTarget.objects.update_or_create(
                indicator=indicator,
                year=selected_year,
                defaults={"value": target_val},
            )

        return indicator


# -----------------------------
# Indicator Target Form (per year, for editing existing targets)
# -----------------------------
class IndicatorTargetForm(forms.ModelForm):
    class Meta:
        model = IndicatorTarget
        fields = ["indicator", "year", "value"]
        widgets = {
            "indicator": forms.Select(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "value": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def clean_value(self):
        value = self.cleaned_data.get("value")
        if value is None:
            raise forms.ValidationError("Value cannot be empty.")
        try:
            Decimal(value)
        except (InvalidOperation, TypeError):
            raise forms.ValidationError("Value must be numeric.")
        return value
