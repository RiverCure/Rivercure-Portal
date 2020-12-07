from django import forms
from .models import e_Sensor
from leaflet.forms.widgets import LeafletWidget



class SensorFileForm(forms.Form):
    excel_file = forms.FileField()

class SensorObservationsFileForm(forms.Form):
    excel_file = forms.FileField()

class SensorForm(forms.ModelForm):
    lat = forms.FloatField()
    lng = forms.FloatField()

    class Meta:
        model = e_Sensor
        fields = ['code','Name','responsibleUser','modalityType','type','description','version', 'timeZoneAbbreviation', 'timeZoneOffset', 'lat', 'lng',]