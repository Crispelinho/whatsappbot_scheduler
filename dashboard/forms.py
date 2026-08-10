from django import forms
from sales.models import Operator, ServiceType

class OperatorForm(forms.ModelForm):
    service_types = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tipos de servicio"
    )
    class Meta:
        model = Operator
        fields = ["name", "phone_number", "commission_percentage", "service_types"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "commission_percentage": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
