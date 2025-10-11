from django import forms
from django.utils import timezone
from .models import Project, Indicator, IndicatorTarget, Donor, Facility
from django.contrib.auth.models import User

# -----------------------------
# Project Form (Multiple Donors + Coordinator Support)
# -----------------------------
class ProjectForm(forms.ModelForm):
    donors = forms.ModelMultipleChoiceField(
        queryset=Donor.objects.all().order_by('name'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        help_text='Select one or more donors for this project (use Ctrl/Cmd to select multiple).'
    )

    coordinator = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Select Coordinator",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Assign a project coordinator."
    )

    class Meta:
        model = Project
        fields = ["name", "description", "start_date", "end_date", "main_donor", "donors",
                  "is_active", "facilities", "coordinator"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter project name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter project description"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format='%Y-%m-%d'),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format='%Y-%m-%d'),
            "main_donor": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "facilities": forms.SelectMultiple(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['main_donor'].queryset = Donor.objects.all().order_by('name')
        self.fields['main_donor'].empty_label = "Select a donor"

        if self.instance and self.instance.pk:
            self.fields['donors'].initial = self.instance.donors.all()
            self.fields['coordinator'].initial = self.instance.coordinator
            for field in ['start_date', 'end_date']:
                date_val = getattr(self.instance, field)
                if date_val:
                    self.fields[field].initial = date_val.strftime('%Y-%m-%d')


# -----------------------------
# Indicator Form (with Target + Year selection)
# -----------------------------
class IndicatorForm(forms.ModelForm):
    target = forms.IntegerField(
        required=False,
        min_value=0,
        label="Annual Target",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        error_messages={"invalid": "Target value must be a whole number."},
    )

    year = forms.ChoiceField(
        label="Year",
        choices=[(y, y) for y in range(timezone.now().year, timezone.now().year + 6)],
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Indicator
        fields = ["name", "unit", "is_kpi", "is_active", "target", "year"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "is_kpi": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = timezone.now().year
        self.fields["year"].initial = current_year
        if self.instance and self.instance.pk:
            selected_year = self.initial.get("year", current_year)
            target_obj = self.instance.targets.filter(year=selected_year).first()
            if target_obj:
                self.fields["target"].initial = target_obj.value

    def clean_target(self):
        value = self.cleaned_data.get("target")
        if value is not None and not isinstance(value, int):
            raise forms.ValidationError("Target value must be a whole number.")
        return value

    def save(self, commit=True):
        indicator = super().save(commit=False)
        if commit:
            indicator.save()
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
# Indicator Target Form
# -----------------------------
class IndicatorTargetForm(forms.ModelForm):
    class Meta:
        model = IndicatorTarget
        fields = ["indicator", "year", "value"]
        widgets = {
            "indicator": forms.Select(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
            "value": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        }

    def clean_value(self):
        value = self.cleaned_data.get("value")
        if value is None:
            raise forms.ValidationError("Value cannot be empty.")
        if not isinstance(value, int):
            raise forms.ValidationError("Value must be a whole number.")
        return value


# -----------------------------
# Donor Form
# -----------------------------
class DonorForm(forms.ModelForm):
    projects_from_form = forms.ModelMultipleChoiceField(
        queryset=Project.objects.all().order_by('name'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
        label="Projects Funded",
        help_text="Select the projects funded by this donor (use Ctrl/Cmd to select multiple)."
    )

    facilities = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.all().order_by('name'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
        label="Linked Facilities",
        help_text="Select the facilities linked to this donor (use Ctrl/Cmd to select multiple)."
    )

    class Meta:
        model = Donor
        fields = ['name', 'contact_email', 'phone', 'projects_from_form', 'facilities']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Donor Name', 'required': True}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Donor.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A donor with this name already exists.")
        return name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['projects_from_form'].initial = self.instance.projects_from_form.all()
            self.fields['facilities'].initial = self.instance.facilities.all()


# -----------------------------
# Facility Form (for Facilities Map)
# -----------------------------
class FacilityForm(forms.ModelForm):
    projects = forms.ModelMultipleChoiceField(
        queryset=Project.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        help_text='Select one or more projects linked to this facility.'
    )

    class Meta:
        model = Facility
        fields = ['name', 'latitude', 'longitude', 'projects']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Facility Name'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Latitude'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Longitude'}),
        }
