from django import forms
from .models import e_Sensor
from leaflet.forms.widgets import LeafletWidget
from organization.models import Membership, Organization
from django.db.models import Q
from sensors.models import e_SensorObservation



class SensorFileForm(forms.Form):
    excel_file = forms.FileField()

class SensorObservationsFileForm(forms.Form):
    excel_file = forms.FileField()


class GeoSensorForm(forms.ModelForm):
    
    lat = forms.FloatField()
    lng = forms.FloatField()
    #code = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    Name = forms.CharField(disabled=True)
    class Meta:
        model = e_Sensor
        fields = ['Name', 'lat', 'lng',]
        

class SensorForm(forms.ModelForm):
    lat = forms.FloatField()
    lng = forms.FloatField()

    class Meta:
        model = e_Sensor
        fields = ['code','Name','organization','isPublic','modalityType','type','description','version', 'timeZoneAbbreviation', 'timeZoneOffset',]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super(SensorForm, self).__init__(*args, **kwargs)
        # We only want to allow to choose options where the user is org_manager or org_contextManager of the organization
        memberships = Membership.objects.filter(user_id=user_id, access_granted=True, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager'))
        self.fields['organization'].queryset = Organization.objects.filter(membership__in=memberships)

class SensorObservationForm(forms.ModelForm):
    class Meta:
        model = e_SensorObservation
        fields = ['date','time','depth','discharge',]