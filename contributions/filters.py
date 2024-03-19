import django_filters
from django_filters.widgets import RangeWidget

from .models import e_ContextContribution
from context.models import EVENTKIND_CHOICES

class ContributionFilter(django_filters.FilterSet):
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label='Situation Observed')

    # observationDateGTE = django_filters.DateFilter(field_name='observationDate', lookup_expr='gte',
    #                                                label='Observation Date >=', help_text='Observations more recent than that of the date you specify.',
    #                                                widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd'}))
    # observationDateLTE = django_filters.DateFilter(field_name='observationDate', lookup_expr='lte',
    #                                                label='Observation Date <=', help_text='Observations older than that of the date you specify.',
    #                                                widget=TextInput(attrs={'placeholder': 'yyyy-mm-dd',
    #                                                                        'type': 'date'}))
    observationDate = django_filters.DateFromToRangeFilter(label='Date of observation',
                                                           help_text='The observation was made in between the specified dates. You may also just search for observations older than the date on the left, or more recent than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label='Date of contribution',
                                                           help_text='The contribution was submitted in between the specified dates. You may also just search for contributions older than the date on the left, or more recent than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))

    class Meta:
        model = e_ContextContribution
        fields = ['situationObserved', 'observationDate', 'creationDateTime']