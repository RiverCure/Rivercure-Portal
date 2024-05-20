import django_filters

from django_filters.widgets import RangeWidget

from .models import e_ChallengeAnswer

class MyChallengeParticipationsFilter(django_filters.FilterSet):
    creation_datetime = django_filters.DateFromToRangeFilter(label='Creation date',
                                                           help_text='The participation was submitted in between the specified dates. <i>Hint:</i> You may also just search for dates more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))

    class Meta:
        Model = e_ChallengeAnswer
        fields = ['creation_datetime']