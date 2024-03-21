import django_filters
from django_filters.widgets import RangeWidget

from .models import e_ContextContribution, ContributionStatus
from context.models import EVENTKIND_CHOICES

class ContributionFilter(django_filters.FilterSet):
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label='Situation Observed')
    observationDate = django_filters.DateFromToRangeFilter(label='Observation date',
                                                           help_text='The observation was made in between the specified dates. Hint: You may also just search for observations more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label='Submission date',
                                                           help_text='The contribution was submitted in between the specified dates. Hint: You may also just search for contributions more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))

    class Meta:
        model = e_ContextContribution
        fields = ['situationObserved', 'observationDate', 'creationDateTime']



class MyContributionsFilter(django_filters.FilterSet):
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label='Situation Observed')
    observationDate = django_filters.DateFromToRangeFilter(label='Observation date',
                                                           help_text='The observation was made in between the specified dates. Hint: You may also just search for observations more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label='Submission date',
                                                           help_text='The contribution was submitted in between the specified dates. Hint: You may also just search for contributions more recent than the date on the left, or older than the date on the right.',
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