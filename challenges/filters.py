import django_filters

from django_filters.widgets import RangeWidget

from django.forms.widgets import TextInput

from .models import e_ChallengeAnswer

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