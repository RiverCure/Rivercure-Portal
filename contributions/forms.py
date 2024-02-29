from django import forms

from datetime import datetime

from .models import e_ContextContribution
from context.models import e_Context
from context.models import EVENTKIND_CHOICES

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result
    

class ContributionInitialForm(forms.ModelForm):
    context = forms.ModelChoiceField(queryset=e_Context.objects,
                                     help_text='This is the context in which you have made your observation.')
    observationDate = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date','max': datetime.now().date()}),
                                              help_text='This is the date at which you have made your observation.',
                                              label='Observation Date')
    observationDescription = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter a description of what you observed.'}),
                                             label='Description')
    situationObserved = forms.ChoiceField(choices=EVENTKIND_CHOICES,
                                          help_text='This is the situation you observed.',
                                          label='Situation Observed')
    file_field = MultipleFileField()

    class Meta:
        model = e_ContextContribution
        fields = ['id', 'observationDate', 'context', 'observationDescription', 'situationObserved']