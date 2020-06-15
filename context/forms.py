from django import forms
from django.forms import Form
from .models import e_Context
from .models import e_HydroFeature

class ContextForm(Form):
    code = forms.CharField(required=True)
    Name = forms.CharField(required=True)
    hydroFeature = forms.ModelChoiceField(
        required=True,
        queryset=e_HydroFeature.objects.all()
        
    )

 