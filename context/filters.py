import django_filters
from .models import e_ContextEvent, e_ContextSensor, e_Context
from django import forms
from django_filters import DateFilter
from django.forms.widgets import TextInput



class ContextSensorFilter(django_filters.FilterSet):
    class Meta:
        model = e_ContextSensor
        fields = ['sensor', ]

class EventFilter(django_filters.FilterSet):  

    date1 = DateFilter(field_name='startDate', lookup_expr='gte', widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
    date2 = DateFilter(field_name='endDate', lookup_expr='lte', widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
    
    class Meta:
        model = e_ContextEvent
        fields = ['Name','type','date1', 'date2',]
        
class ContextFilter(django_filters.FilterSet):  
    class Meta:
        model = e_Context
        fields = ['Name', 'hydroFeature', 'organization']    

    # Overrides filter 'organization' to only contain correct organizations
    def __init__(self, *args, **kwargs):
        organizations = kwargs['organizations']
        del kwargs['organizations']
        super(ContextFilter, self).__init__(*args, **kwargs)
        print(self.filters['organization'])
        self.filters['organization'].extra.update({'queryset': organizations})
        self.filters['organization'].queryset = organizations
        