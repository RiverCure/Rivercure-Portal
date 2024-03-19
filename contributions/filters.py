import django_filters
from django_filters.widgets import RangeWidget

from .models import e_ContextContribution, ContributionStatus
from context.models import EVENTKIND_CHOICES

class ContributionFilter(django_filters.FilterSet):
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label='Situation Observed')
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



class MyContributionsFilter(django_filters.FilterSet):
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label='Situation Observed')
    observationDate = django_filters.DateFromToRangeFilter(label='Date of observation',
                                                           help_text='The observation was made in between the specified dates. You may also just search for observations older than the date on the left, or more recent than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label='Date of contribution',
                                                           help_text='The contribution was submitted in between the specified dates. You may also just search for contributions older than the date on the left, or more recent than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    context = django_filters.CharFilter(label='Context',
                                        help_text='Search the context by name.',
                                        field_name='context__Name', lookup_expr='icontains')
    state = django_filters.ChoiceFilter(label='Contribution State',
                                        choices=ContributionStatus.choices)

    class Meta:
        models = e_ContextContribution
        fields = ['situationObserved', 'observationDate', 'creationDateTime', 'context', 'state']