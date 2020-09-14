import django_filters
from django import forms
from .models import e_Sensor
from context.models import e_ContextSensor



class SensorFilter(django_filters.FilterSet):   
    class Meta:
        model = e_Sensor
        fields = ['type', 'code',]
    
