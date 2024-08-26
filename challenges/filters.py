import django_filters

from django_filters.widgets import RangeWidget

from django.forms.widgets import TextInput, Select
from django.utils.translation import gettext_lazy as _

from context.models import e_ContextEvent

from .models import e_Challenge, e_ChallengeAnswer, DIFFICULTY_LEVEL


class MyChallengeParticipationsFilter(django_filters.FilterSet):
    creation_datetime = django_filters.DateFromToRangeFilter(label='Creation date',
                                                           help_text='The participation was submitted in between the specified dates. <i>Hint:</i> You may also just search for dates more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))

    class Meta:
        Model = e_ChallengeAnswer
        fields = ['creation_datetime']

class ChallengeParticipationsFilter(django_filters.FilterSet):
    created_by__username = django_filters.CharFilter(label='', field_name='created_by__username', lookup_expr='icontains',
                                               widget=TextInput(attrs={
                                                    'placeholder': 'Search by username...',
                                                    'type': 'search',
                                                    'class': 'flex-fill mr-2 form-control',
                                                }))
    creation_datetime = django_filters.DateFromToRangeFilter(label='Creation date',
                                                           help_text='The participation was submitted in between the specified dates. <i>Hint:</i> You may also just search for dates more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    
    class Meta:
        Model = e_ChallengeAnswer
        fields = ['created_by','creation_datetime']

class ChallengesFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label=_('Title'),
                                      field_name='challenge__title', lookup_expr='icontains',
                                      widget=TextInput(attrs={
                                                    'placeholder': _('Search by Quiz title...'),
                                                    'type': 'search',
                                                }))
    event = django_filters.CharFilter(label=_('Event'),
                                      field_name='event__title', lookup_expr='icontains',
                                      widget=TextInput(attrs={
                                                    'placeholder': _('Search by Event title...'),
                                                    'type': 'search',
                                                }))
    difficulty_level = django_filters.ChoiceFilter(choices=DIFFICULTY_LEVEL,
                                                   label=_('Difficulty Level'))
    
    class Meta:
            Model = e_Challenge
            fields = ['title', 'event', 'difficulty_level']