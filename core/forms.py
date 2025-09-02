from django import forms
from .models import Project, Indicator

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "start_year", "end_year", "active"]

# ✅ New form for KPI/Indicator
class IndicatorForm(forms.ModelForm):
    class Meta:
        model = Indicator
        fields = ["name", "unit", "target", "is_kpi"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "target": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_kpi": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

