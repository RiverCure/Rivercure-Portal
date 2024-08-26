import django_filters

from django_filters.widgets import RangeWidget

from django.forms.widgets import TextInput, Select
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import User

from organization.models import Organization
from rivercureportal.models import e_HydroFeature
from contributions.models import e_ContextContribution, ContributionStatus, SituationChoices
from challenges.models import e_Challenge, DIFFICULTY_LEVEL, ChallengeState

from .models import e_ContextEvent, e_ContextSensor, e_Context

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
    Name = django_filters.CharFilter(label='Context Name', lookup_expr='icontains',
                                     widget=TextInput(attrs={
                                                    'placeholder': _('Search by name...'),
                                                    'type': 'search',
                                                    'class': 'form-control',
                                                }))
    hydroFeature = django_filters.ModelChoiceFilter(label='HydroFeature', queryset=e_HydroFeature.objects.all(),
                                                    widget=Select(attrs={'class': 'form-control',}))
    organization = django_filters.ModelChoiceFilter(label=_('Organization'), queryset=Organization.objects.all(),
                                                    widget=Select(attrs={'class': 'form-control',}))
    # hydroFeatureType = django_filters.ChoiceFilter(label='HydroFeature Type', choices=HYDROFEATUREKIND_CHOICES)

    class Meta:
        model = e_Context
        fields = ['Name', 'hydroFeature', 'organization']

##############
# Moderators 
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
    user__username = django_filters.CharFilter(label=_('Username'), field_name='user__username', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': _('Search by username...'),
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))
    user__email = django_filters.CharFilter(label=_('Email Address'), field_name='user__email', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': _('Search by email address...'),
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))
    grant_date = django_filters.DateFromToRangeFilter(label=_('Date granted'),
                                                        help_text=_('The permission was given in between the specified dates. <i>Hint:</i> You may also just search for permission dates more recent than the date on the left, or older than the date on the right.'),
                                                        widget=RangeWidget(attrs={
                                                            'placeholder': 'yyyy-mm-dd',
                                                            'type': 'date'
                                                        }))

    class Meta:
        Model = User
        fields = ['user__username', 'user__email', 'grant_date']


class ModeratorContextFilter(django_filters.FilterSet):
    Name = django_filters.CharFilter(label=_('Context Name'),
                                        field_name='context__Name',
                                        lookup_expr='icontains',
                                        widget=TextInput(attrs={
                                                    'placeholder': _('Search by Context name...'),
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))
    hydroFeature = django_filters.ModelChoiceFilter(field_name='context__hydroFeature', label='HydroFeature', queryset=e_HydroFeature.objects.all())
    organization = django_filters.ModelChoiceFilter(field_name='context__organization', label=_('Organization'), queryset=Organization.objects.all())

    class Meta:
        Model = e_Context
        fields = ['Name', 'hydroFeature', 'organization']


class ModeratorContextContributionFilter(django_filters.FilterSet):
    state = django_filters.ChoiceFilter(label=_('State'),
                                        choices=ContributionStatus.choices)
    situationObserved = django_filters.ChoiceFilter(choices=SituationChoices.choices, label=_('Situation Observed'))
    observationDate = django_filters.DateFromToRangeFilter(label=_('Observation Date'),
                                                           help_text=_('The observation was made in between the specified dates. <i>Hint:</i> You may also just search for observations more recent than the date on the left, or older than the date on the right.'),
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label=_('Submission Date'),
                                                           help_text=_('The Contribution was submitted in between the specified dates. <i>Hint:</i> You may also just search for Contributions more recent than the date on the left, or older than the date on the right.'),
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    createdBy__username = django_filters.CharFilter(label=_('Author'), field_name='createdBy__username', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': _('Search by username...'),
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))

    class Meta:
        Model = e_ContextContribution
        fields = ['state', 'situationObserved', 'observationDate', 'creationDateTime', 'createdBy__username']

##############
# Quiz Managers 
##############
class QuizManagerFilter(django_filters.FilterSet): # TODO: Since this is repeated code from ManagerFilter, maybe let's combine both into one single MemberFilter filter instead?
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
        
        
class QuizManagerAddFilter(django_filters.FilterSet):
    user__username = django_filters.CharFilter(label='', field_name='user__username', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': 'Search by username...',
                                                    'type': 'search',
                                                    'class': 'flex-fill mr-2 form-control',
                                                }))

    class Meta:
        Model = User
        fields = ['user__username']

# TODO: This is the same as ModeratorContextFilter. Merge
class QuizManagerContextFilter(django_filters.FilterSet):
    Name = django_filters.CharFilter(label=_('Context Name'),
                                        field_name='context__Name',
                                        lookup_expr='icontains',
                                        widget=TextInput(attrs={
                                                    'placeholder': _('Search by Context name...'),
                                                    'class': 'form-control',
                                                    'type': 'search',
                                                }))
    organization = django_filters.ModelChoiceFilter(field_name='context__organization', label=_('Organization'), queryset=Organization.objects.all())

    class Meta:
        Model = e_Context
        fields = ['Name', 'organization']

class MyChallengesFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label=_('Challenge Title'),
                                      lookup_expr='icontains',
                                      widget=TextInput(attrs={
                                                    'placeholder': _('Search by title...'),
                                                    'type': 'search',
                                                    'class': 'form-control',
                                                    }))
    difficulty_level = django_filters.ChoiceFilter(choices=DIFFICULTY_LEVEL, label=_('Difficulty Level'))
    event = django_filters.CharFilter(label=_('Event'),
                                      field_name='event__Name', lookup_expr='icontains',
                                      widget=TextInput(attrs={
                                        'placeholder': _('Search by Event name...'),
                                        'type': 'search',
                                      }))
    state = django_filters.ChoiceFilter(label=_('Challenge State'),
                                        choices=ChallengeState.choices)
    creation_datetime = django_filters.DateFromToRangeFilter(label=_('Creation Date'),
                                                           help_text=_('The Challenge was created in between the specified dates. <i>Hint:</i> You may also just search for dates more recent than the date on the left, or older than the date on the right.'),
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))

    class Meta:
        Model = e_Challenge
        fields = ['title', 'difficulty_level', 'event', 'state', 'creation_datetime']

############
# Challenges
############
class EventChallengeListFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label='Challenge Title',
                                      lookup_expr='icontains',
                                      widget=TextInput(attrs={
                                                    'placeholder': 'Search by title...',
                                                    'type': 'search',
                                                    'class': 'form-control',
                                                    }))
    difficulty_level = django_filters.ChoiceFilter(choices=DIFFICULTY_LEVEL, label='Difficulty Level')

    class Meta:
        Model = e_Challenge
        fields = ['title', 'difficulty_level']