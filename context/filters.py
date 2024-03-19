import django_filters
from django.forms.widgets import TextInput

from .models import e_ContextEvent, e_ContextSensor, e_Context
from rivercureportal.models import e_HydroFeature, HYDROFEATUREKIND_CHOICES


class ContextSensorFilter(django_filters.FilterSet):

    class Meta:
        model = e_ContextSensor
        fields = ['sensor__sensorClass__category', 'sensor__name']

class EventFilter(django_filters.FilterSet):  

    Name = django_filters.CharFilter(label="Name", lookup_expr='icontains')
    date1 = django_filters.DateFilter(field_name='startDate', lookup_expr='gte', widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
    date2 = django_filters.DateFilter(field_name='endDate', lookup_expr='lte', widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
    
    class Meta:
        model = e_ContextEvent
        fields = ['Name','type','date1', 'date2',]
        
class ContextFilter(django_filters.FilterSet):
    Name = django_filters.CharFilter(label='Context Name', lookup_expr='icontains')
    hydroFeature = django_filters.ModelChoiceFilter(label='HydroFeature', queryset=e_HydroFeature.objects.all())
    # hydroFeatureType = django_filters.ChoiceFilter(label='HydroFeature Type', choices=HYDROFEATUREKIND_CHOICES)

    class Meta:
        model = e_Context
        fields = ['Name', 'hydroFeature', 'organization']