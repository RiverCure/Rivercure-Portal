import django_filters

from django_filters.widgets import RangeWidget

from django.forms.widgets import TextInput

from .models import e_Challenge, ChallengeState, DIFFICULTY_LEVEL

class MyContextsChallengesFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label='Challenge Title',
                                      lookup_expr='icontains',
                                      widget=TextInput(attrs={
                                                    'placeholder': 'Search by title...',
                                                    'type': 'search',
                                                    'class': 'form-control',
                                                    }))
    difficulty_level = django_filters.ChoiceFilter(choices=DIFFICULTY_LEVEL, label='Difficulty Level')
    event = django_filters.CharFilter(label='Event',
                                      field_name='event__Name', lookup_expr='icontains',
                                      widget=TextInput(attrs={
                                        'placeholder': 'Search by Event name...',
                                        'type': 'search',
                                      }))
    state = django_filters.ChoiceFilter(label='Challenge State',
                                        choices=ChallengeState.choices)
    creation_datetime = django_filters.DateFromToRangeFilter(label='Creation date',
                                                           help_text='The Challenge was created in between the specified dates. <i>Hint:</i> You may also just search for dates more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))

    class Meta:
        Model = e_Challenge
        fields = ['title', 'difficulty_level', 'event', 'state', 'creation_datetime']
