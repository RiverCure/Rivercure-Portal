from django import forms

from .models import e_ContextContribution
from context.models import e_Context

class ContributionInitialForm(forms.ModelForm):
    context = forms.ModelChoiceField(queryset=e_Context.objects,
                                     help_text='This is the context in which you have made your observation.')
    observationDateTime = forms.DateTimeField(help_text='This is the date and time at which you have made your observation.',
                                              label='Observation time and date')

    class Meta:
        model = e_ContextContribution
        fields = ['id', 'observationDateTime', 'observationDescription', 'situationObserved']