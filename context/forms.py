from django import forms
from django.forms import ModelForm
from django.contrib.gis.forms import fields
from .models import e_Context, e_ContextEvent
from .models import e_HydroFeature
from leaflet.forms.widgets import LeafletWidget


class ContextForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField()
    # dtm_file = forms.FileField(required=False)
    # contour_lines = forms.FileField(required=False)
    hydroFeature = forms.ModelChoiceField(queryset=e_HydroFeature.objects.all(), required=False)
    domain = forms.CharField(widget=forms.HiddenInput())
    alignment = forms.CharField(widget=forms.HiddenInput())
    refinement = forms.CharField(widget=forms.HiddenInput())
    boundaries = forms.CharField(widget=forms.HiddenInput())
    boundary_points = forms.CharField(widget=forms.HiddenInput())

class UploadContextForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    domain = forms.FileField(required=False)
    alignments = forms.FileField(required=False)
    refinements = forms.FileField(required=False)
    boundaries = forms.FileField(required=False)
    # boundaries_points = forms.FileField(required=False)
    dtm_file = forms.FileField(required=False)
    friction_coefficient_file = forms.FileField(required=False)

class EventForm(forms.ModelForm):

    context_code = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = e_ContextEvent
        fields = ['Name', 'type', 'subtype', 'context_code', 'startDate', 'startTime', 'endDate', 'endTime', 'description', 'returnPeriod', 'warmUp', 'WritingPeriodicity', 'WritingPeriodicityUnit', 'UpdateMaximumValue', 'UpdateMaximumValueUnit']
        widgets = {
            'startDate': forms.TextInput(attrs={'placeholder': 'yyyy-mm-dd'}),
            'endDate': forms.TextInput(attrs={'placeholder': 'yyyy-mm-dd'}),
            'startTime': forms.TextInput(attrs={'placeholder': 'hh:mm:ss'}),
            'endTime': forms.TextInput(attrs={'placeholder': 'hh:mm:ss'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter description here'}),
        }

class EventEditForm(forms.ModelForm):
      class Meta:
        model = e_ContextEvent
        fields = ['Name', 'type', 'subtype', 'context', 'state', 'startDate', 'startTime', 'endDate', 'endTime', 'description', 'returnPeriod', 'warmUp', 'WritingPeriodicity', 'WritingPeriodicityUnit', 'UpdateMaximumValue', 'UpdateMaximumValueUnit']