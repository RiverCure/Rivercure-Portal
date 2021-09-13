import django_filters
from django import forms
from .models import Sensor, SensorObservation
from django_filters import DateFilter
from django.forms.widgets import TextInput


class SensorFilter(django_filters.FilterSet): 
    code = django_filters.CharFilter(label="Code", lookup_expr='icontains')
    
    class Meta:
        model = Sensor
        fields = ['code']
    
class ObservationFilter(django_filters.FilterSet):

    Date = DateFilter(field_name='date', lookup_expr='gte',  widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
    Date2 = DateFilter(field_name='date', lookup_expr='lte', widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))

    class Meta:
        model = SensorObservation
        fields = ['Date', 'Date2', ]
        