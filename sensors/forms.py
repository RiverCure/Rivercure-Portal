from django import forms
from .models import Sensor
from leaflet.forms.widgets import LeafletWidget
from organization.models import Membership, Organization
from django.db.models import Q
from sensors.models import SensorClass, SensorClassProperty, SensorObservation, Unit

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
        model = Sensor
        fields = ['Name', 'lat', 'lng',]
        

class SensorForm(forms.ModelForm):
    # These fields are not the ones in the form - they are some who needed a bit customization
    code        = forms.CharField()
    name        = forms.CharField()
    description = forms.CharField(widget=forms.Textarea, required=False)
    isPublic    = forms.BooleanField(label='Public')
    lat         = forms.FloatField()
    lng         = forms.FloatField()

    class Meta:
        model = Sensor
        # These are the fields in the form, appearing by this order
        fields = ['code', 'name', 'organization', 'isPublic', 'description']
        # fields = ['code','Name','organization','isPublic','modalityType','type','description','version', 'timeZoneAbbreviation', 'timeZoneOffset',]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super(SensorForm, self).__init__(*args, **kwargs)
        # We only want to allow to choose options where the user is org_manager or org_contextManager of the organization
        memberships = Membership.objects.filter(user_id=user_id, access_granted=True, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager'))
        self.fields['organization'].queryset = Organization.objects.filter(membership__in=memberships)

class SensorObservationForm(forms.ModelForm):
    class Meta:
        model = SensorObservation
        fields = ['date', 'time']
        # fields = ['date','time','depth','discharge',]

class SensorClassForm(forms.ModelForm):
    code    = forms.CharField()
    name    = forms.CharField()
    vendor  = forms.CharField(required=False)
    version = forms.CharField(required=False)

    class Meta:
        model = SensorClass
        fields = ['code', 'name', 'state', 'vendor', 'version', 'modality', 'kind']

class SensorClassPropertyForm(forms.ModelForm):
    code                      = forms.CharField()
    name                      = forms.CharField()
    isOptional                = forms.BooleanField(label='Optional', required=False) # it actually is required. See the template for explanation
    thresholdLowerCritical    = forms.DecimalField(label='Threshold lower critical', required=False)
    thresholdLowerNoncritical = forms.DecimalField(label='Threshold lower non-critical', required=False)
    thresholdUpperCritical    = forms.DecimalField(label='Threshold upper critical', required=False)
    thresholdUpperNoncritical = forms.DecimalField(label='Threshold upper non-critical', required=False)
    unit                      = forms.ModelChoiceField(queryset=Unit.objects.all(), required=False)

    class Meta:
        model = SensorClassProperty
        fields = ['code', 'name', 'type', 'isOptional', 'thresholdLowerCritical', 'thresholdLowerNoncritical', 'thresholdUpperCritical', 'thresholdUpperNoncritical', 'unit']