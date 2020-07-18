from django import forms
from django.forms import ModelForm
from django.contrib.gis.forms import fields
from .models import e_Context
from .models import e_HydroFeature
from leaflet.forms.widgets import LeafletWidget

class ContextForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField()
    hydroFeature = forms.ModelChoiceField(queryset=e_HydroFeature.objects.all())
    domain = forms.CharField(widget=forms.HiddenInput())
    # CLExternalBoundary = forms.IntegerField()
    alignment = forms.CharField(widget=forms.HiddenInput())
    # CLAlignment = forms.IntegerField()
    refinement = forms.CharField(widget=forms.HiddenInput())
    # CLInternalBoundary = forms.IntegerField()
    boundaries = forms.CharField(widget=forms.HiddenInput())