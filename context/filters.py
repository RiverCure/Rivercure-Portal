import django_filters
from .models import e_ContextEvent, e_ContextSensor
from django import forms
from django_filters import DateFilter



class EventSensorFilter(django_filters.FilterSet):
     class Meta:
        model = e_ContextSensor
        fields = ['sensor',]

class EventFilter(django_filters.FilterSet):  

    startDateTime = DateFilter(field_name='startDatetime', lookup_expr='gte')
    endDateTime = DateFilter(field_name='endDatetime', lookup_expr='lte')
    
    class Meta:
        model = e_ContextEvent
        fields = ['Name','type','context', 'startDateTime', 'endDateTime']
        
        
        