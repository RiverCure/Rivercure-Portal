import django_filters

from django_filters.widgets import RangeWidget

from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

from .models import e_ContextContribution, ContributionStatus
from context.models import EVENTKIND_CHOICES

class ContributionFilter(django_filters.FilterSet):
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label='Situation Observed')
    observationDate = django_filters.DateFromToRangeFilter(label='Observation date',
                                                           help_text='The observation was made in between the specified dates. <i>Hint:</i> You may also just search for observations more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label='Submission date',
                                                           help_text='The contribution was submitted in between the specified dates. <i>Hint:</i> You may also just search for contributions more recent than the date on the left, or older than the date on the right.',
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))

    class Meta:
        model = e_ContextContribution
        fields = ['situationObserved', 'observationDate', 'creationDateTime']



class MyContributionsFilter(django_filters.FilterSet):
    situationObserved = django_filters.ChoiceFilter(choices=EVENTKIND_CHOICES, label=_('Situation Observed'))
    observationDate = django_filters.DateFromToRangeFilter(label=_('Observation Date'),
                                                           help_text=_('The observation was made in between the specified dates. <i>Hint:</i> You may also just search for dates more recent than the date on the left, or older than the date on the right.'),
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    creationDateTime = django_filters.DateFromToRangeFilter(label=_('Submission Date'),
                                                           help_text=_('The Contribution was submitted in between the specified dates. <i>Hint:</i> You may also just search for dates more recent than the date on the left, or older than the date on the right.'),
                                                           widget=RangeWidget(attrs={'placeholder': 'yyyy-mm-dd',
                                                                                     'type': 'date'}))
    context = django_filters.CharFilter(label=_('Context'),
                                        field_name='context__Name', lookup_expr='icontains',
                                        widget=TextInput(attrs={
                                                    'placeholder': _('Search by Context name...'),
                                                    'type': 'search',
                                                }))
    state = django_filters.ChoiceFilter(label=_('Contribution State'),
                                        choices=ContributionStatus.choices)

    class Meta:
        models = e_ContextContribution
        fields = ['situationObserved', 'observationDate', 'creationDateTime', 'context', 'state']