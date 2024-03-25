import django_filters
from django.forms.widgets import TextInput
from django.contrib.auth.models import User
from django_filters.widgets import RangeWidget

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

class ModeratorAddFilter(django_filters.FilterSet):
    user__username = django_filters.CharFilter(label='', field_name='user__username', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': 'Search by username...',
                                                    'type': 'search',
                                                    'class': 'flex-fill mr-2 form-control',
                                                }))

    class Meta:
        Model = User
        fields = ['user__username']

class ModeratorFilter(django_filters.FilterSet):
    user__username = django_filters.CharFilter(label='Username', field_name='user__username', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': 'Search by username...',
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))
    user__email = django_filters.CharFilter(label='Email address', field_name='user__email', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': 'Search by email address...',
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))
    grant_date = django_filters.DateFromToRangeFilter(label='Date granted',
                                                        help_text='The permission was given in between the specified dates. Hint: You may also just search for permission dates more recent than the date on the left, or older than the date on the right.',
                                                        widget=RangeWidget(attrs={
                                                            'placeholder': 'yyyy-mm-dd',
                                                            'type': 'date'
                                                        }))

    class Meta:
        Model = User
        fields = ['user__username', 'user__email', 'grant_date']