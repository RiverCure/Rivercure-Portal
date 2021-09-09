from django import forms
from .models import Sensor
from leaflet.forms.widgets import LeafletWidget
from organization.models import Membership, Organization
from django.db.models import Q
from sensors.models import SensorClass, SensorClassProperty, SensorObservation, SensorObservationValue, Unit
from django.core.exceptions import ValidationError
from django.conf import settings
import os

class SensorFileForm(forms.Form):
    excel_file = forms.FileField()

class SensorObservationsFileForm(forms.Form):
    excel_file = forms.FileField()

class GeoSensorForm(forms.ModelForm):
    name = forms.CharField(disabled=True)
    lat = forms.FloatField()
    lng = forms.FloatField()
    
    class Meta:
        model = Sensor
        fields = ['name', 'lat', 'lng']
        
class SensorForm(forms.ModelForm):
    # These fields are not the ones in the form - they are some who needed a bit customization
    code        = forms.CharField()
    name        = forms.CharField()
    description = forms.CharField(widget=forms.Textarea, required=False)
    isPublic    = forms.BooleanField(label='Public', required=False)
    lat         = forms.FloatField(label='Latitude')
    lng         = forms.FloatField(label='Longitude')

    def clean(self):
        super().clean()
        form_data = self.cleaned_data
        if form_data['sensorClass'].organization != form_data['organization']:
            self._errors['sensorClass'] = ['Sensor class\'s organization must match organization field'] 
            self._errors['organization'] = ['Organization must match the organization of sensor class\'s field'] 
        return form_data

    class Meta:
        model = Sensor
        # These are the fields in the form, appearing by this order
        fields = ['code', 'name', 'organization', 'isPublic', 'description', 'sensorClass']

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super(SensorForm, self).__init__(*args, **kwargs)
        # Only allow to choose organizations where the user is org_manager, org_sensorManager or org_contextManager of the organization
        memberships = Membership.objects.filter(user_id=user_id, access_granted=True, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager'))
        self.fields['organization'].queryset = Organization.objects.filter(membership__in=memberships)
        # Only allow to choose sensor classes where the user is member of that organization
        self.fields['sensorClass'].queryset = SensorClass.objects.filter(organization__in=self.fields['organization'].queryset)
        self.fields['sensorClass'].label = 'Sensor class'

# Enables to have property - (type) labels in the properties choice field
class CustomModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, property):
        return f'{property.name}-{property.get_type_display()}'

class SensorObservationForm(forms.ModelForm):
    time       = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    properties = CustomModelMultipleChoiceField(queryset=SensorClassProperty.objects.none(), widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        # Extract the sensor received from the View (SensorObservationCreateView or SensorObservationUpdateView)
        self.sensor = kwargs.pop('sensor')
        super(SensorObservationForm, self).__init__(*args, **kwargs)
        # Get the sensor class properties of that sensor's sensor class
        self.fields['properties'].queryset = SensorClassProperty.objects.filter(sensorClass=self.sensor.sensorClass)

        optionalProps = ''
        for prop in self.fields['properties'].queryset:
            tag = f'value_of_{prop}'
            optionalProps += f'{prop.isOptional},'
            
            if prop.type == 'number':
                self.fields[tag] = forms.DecimalField(required=not prop.isOptional)
            elif prop.type == 'image':
                self.fields[tag] = forms.ImageField(required=not prop.isOptional)
            else: # string and others
                self.fields[tag] = forms.CharField(required=not prop.isOptional)

            # Can't set a default field for an image
            if self.instance.pk is not None and self.instance.sensorobservationvalue_set.filter(property=prop).exists():
                    self.initial[tag] = self.instance.sensorobservationvalue_set.get(property=prop).value
        
        self.fields['properties'].widget.attrs['optionalvalues'] = optionalProps[:-1]

    def clean(self):
        super(SensorObservationForm, self).clean()

        for prop in self.fields['properties'].queryset:
            if prop.sensorClass != self.sensor.sensorClass:
                raise ValidationError('Sensor\'s sensor class must match properties sensor class')

            # All non-optional fields must be filled
            tag = f'value_of_{prop.name}'
            if self.cleaned_data[tag] == '' and (not prop.isOptional):
                self.add_error(tag, 'Mandatory fields must be filled')
        
        return self.cleaned_data
    
    class Meta:
        model = SensorObservation
        fields = ['date', 'time', 'severity', 'properties']

class SensorClassForm(forms.ModelForm):
    code    = forms.CharField()
    name    = forms.CharField()
    vendor  = forms.CharField(required=False)
    version = forms.CharField(required=False)

    class Meta:
        model = SensorClass
        fields = ['code', 'name', 'state', 'vendor', 'version', 'modality', 'category']

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