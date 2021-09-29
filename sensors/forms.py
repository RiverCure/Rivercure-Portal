from django import forms
from .models import Sensor
from leaflet.forms.widgets import LeafletWidget
from organization.models import Membership, Organization
from django.db.models import Q
from sensors.models import QuantityKind, SensorCategory, SensorClass, SensorClassProperty, SensorObservation, SensorObservationValue, Unit
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

    def __init__(self, *args, **kwargs):
        super(GeoSensorForm, self).__init__(*args, **kwargs)
        self.initial['lng'] = self.instance.local.x
        self.initial['lat'] = self.instance.local.y
    
    class Meta:
        model = Sensor
        fields = ['name', 'lat', 'lng']
        
class SensorForm(forms.ModelForm):
    code        = forms.CharField()
    name        = forms.CharField()
    description = forms.CharField(widget=forms.Textarea, required=False)
    isPublic    = forms.BooleanField(label='Public', required=False)
    lat         = forms.FloatField(label='Latitude')
    lng         = forms.FloatField(label='Longitude')

    def __init__(self, *args, **kwargs):
        organization_name = kwargs.pop('organizationName')
        super(SensorForm, self).__init__(*args, **kwargs)
        # Only allow to choose organizations where the user is org_manager, org_sensorManager or org_contextManager of the organization
        organization = Organization.objects.get(name=organization_name)
        # Only allow to choose sensor classes where the user is member of that organization
        self.fields['sensorClass'].queryset = SensorClass.objects.filter(organization=organization)
        self.fields['sensorClass'].label = 'Sensor class'

        if self.instance.pk and self.instance.local: # the user is editing
            self.initial['lng'] = self.instance.local.x
            self.initial['lat'] = self.instance.local.y

    def clean(self):
        super().clean()
        form_data = self.cleaned_data

        if not SensorClassProperty.objects.filter(sensorClass=form_data['sensorClass']).exists():
            raise ValidationError('The selected sensor class does\'t yet have any property, thus a sensor with that sensor class cannot be created')

        return form_data

    class Meta:
        model = Sensor
        fields = ['code', 'name', 'isPublic', 'state', 'description', 'sensorClass']

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
            
            dependant_prop = self.fields['properties'].queryset.filter(name=prop.dependantOf)
            if prop.dependantOf is not None and dependant_prop.exists():
                dependant_tag = f'value_of_{prop.dependantOf}'
                if self.cleaned_data[dependant_tag] == '':
                    self.add_error(tag, f'This property is dependant on another ({dependant_prop[0].name}), so that property must be filled')

        return self.cleaned_data
    
    class Meta:
        model = SensorObservation
        fields = ['date', 'time', 'severity', 'properties']

class SensorClassForm(forms.ModelForm):
    code    = forms.CharField()
    name    = forms.CharField()
    vendor  = forms.CharField(required=False)
    version = forms.CharField(required=False)

    def __init__(self,*args,**kwargs):
        self.organization = kwargs.pop('organization')
        self.sensorClass = kwargs.pop('sensorClass')
        super(SensorClassForm,self).__init__(*args,**kwargs)

    def clean(self):
        super(SensorClassForm, self).clean()

        # Two sensorClasses of the same organization can't have the same code
        sensorClass = SensorClass.objects.filter(code=self.cleaned_data['code'], organization=self.organization)
        if sensorClass.exists() and self.sensorClass == None:
            self.add_error('code', 'A sensor class with that code already exists within the organization')
        
        if sensorClass.exists() and self.sensorClass != None and self.sensorClass != sensorClass[0]:
            self.add_error('code', 'A sensor class with that code already exists within the organization')
        
        return self.cleaned_data

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

    def __init__(self,*args,**kwargs):
        self.sensorClass = kwargs.pop('sensorClass')
        self.property = kwargs.pop('property')
        super(SensorClassPropertyForm,self).__init__(*args,**kwargs)
        self.fields['dependantOf'].queryset = SensorClassProperty.objects.filter(sensorClass=self.sensorClass)

    def clean(self):
        super(SensorClassPropertyForm, self).clean()

        # Two sensorClasses of the same organization can't have the same code
        sensorClassProperty = SensorClassProperty.objects.filter(code=self.cleaned_data['code'], sensorClass=self.sensorClass)
        if sensorClassProperty.exists() and self.property == None:
            self.add_error('code', 'A sensor class property with that code already exists in this sensor class')
        
        if sensorClassProperty.exists() and self.property != None and self.property != sensorClassProperty[0]:
            self.add_error('code', 'A sensor class property with that code already exists in this sensor class')
        
        return self.cleaned_data

    class Meta:
        model = SensorClassProperty
        fields = ['code', 'name', 'type', 'isOptional', 'dependantOf', 'thresholdLowerCritical', 'thresholdLowerNoncritical', 'thresholdUpperCritical', 'thresholdUpperNoncritical', 'unit']