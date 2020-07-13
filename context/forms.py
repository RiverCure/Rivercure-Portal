from django import forms
from django.forms import ModelForm
from django.contrib.gis.forms import fields
from .models import e_Context
from .models import e_HydroFeature
from leaflet.forms.widgets import LeafletWidget

class ContextForm(forms.Form):
    code = forms.CharField(readonly=True)
    name = forms.CharField()
    hydroFeature = forms.ModelChoiceField(queryset=e_HydroFeature.objects.all())
    domain = forms.CharField(widget=forms.HiddenInput())
    alignment = forms.CharField(widget=forms.HiddenInput())
    refinement = forms.CharField(widget=forms.HiddenInput())
    boundaries = forms.CharField(widget=forms.HiddenInput())
