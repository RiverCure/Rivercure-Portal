import django_filters
from django import forms
from .models import e_Sensor, e_SensorObservation
from context.models import e_ContextSensor
from django_filters import DateFilter
from django.forms.widgets import TextInput


class SensorFilter(django_filters.FilterSet):   
    class Meta:
        model = e_Sensor
        fields = ['type', 'code',]
    
class ObservationFilter(django_filters.FilterSet):

    Date = DateFilter(field_name='date', lookup_expr='gte',  widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
    Date2 = DateFilter(field_name='date', lookup_expr='lte', widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
   
    class Meta:
        model = e_SensorObservation
        fields = ['Date', 'Date2', 'sensor',]
        