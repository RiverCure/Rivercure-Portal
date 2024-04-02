import django_filters
from django.forms.widgets import TextInput
from django.contrib.auth.models import User
from django_filters.widgets import RangeWidget

from .models import e_ContextEvent, e_ContextSensor, e_Context, EVENTKIND_CHOICES
from contributions.models import e_ContextContribution, ContributionStatus
from rivercureportal.models import e_HydroFeature
from organization.models import Organization


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

##############
# Moderators #
##############
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
                                                        help_text='The permission was given in between the specified dates. <i>Hint:</i> You may also just search for permission dates more recent than the date on the left, or older than the date on the right.',
                                                        widget=RangeWidget(attrs={
                                                            'placeholder': 'yyyy-mm-dd',
                                                            'type': 'date'
                                                        }))

    class Meta:
        Model = User
        fields = ['user__username', 'user__email', 'grant_date']


class ModeratorContextFilter(django_filters.FilterSet):
    Name = django_filters.CharFilter(label='Context Name',
                                        field_name='context__Name',
                                        lookup_expr='icontains',
                                        widget=TextInput(attrs={
                                                    'placeholder': 'Search by Context name...',
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))
    hydroFeature = django_filters.ModelChoiceFilter(field_name='context__hydroFeature', label='HydroFeature', queryset=e_HydroFeature.objects.all())
    organization = django_filters.ModelChoiceFilter(field_name='context__organization', label='Organization', queryset=Organization.objects.all())

    class Meta:
        Model = e_Context
        fields = ['Name', 'hydroFeature', 'organization']


class ModeratorContextContributionFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(label='State',
                                        choices=ContributionStatus.choices)
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label='Situation Observed')
    observationDate = django_filters.DateFromToRangeFilter(label='Observation date',
                                                           help_text='The observation was made in between the specified dates. <i>Hint:</i> You may also just search for observations more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label='Submission date',
                                                           help_text='The contribution was submitted in between the specified dates. <i>Hint:</i> You may also just search for contributions more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    createdBy__username = django_filters.CharFilter(label='Author', field_name='createdBy__username', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': 'Search by author username...',
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))

    class Meta:
        Model = e_ContextContribution
        fields = ['state', 'situationObserved', 'observationDate', 'creationDateTime', 'createdBy__username']