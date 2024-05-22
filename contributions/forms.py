from django import forms
from django.forms import ValidationError

from datetime import datetime

from .models import e_ContextContribution
from context.models import EVENTKIND_CHOICES
from leaflet.forms.widgets import LeafletWidget

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'accept': 'image/*, video/mp4, video/webm, video/ogg'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result
    

class ContributionInitialForm(forms.ModelForm):
    observationDate = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date','max': datetime.now().date()}),
                                              help_text='This is the date at which you have made your observation.',
                                              label='Observation Date')
    observationDescription = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Enter a description of what you observed. Example: The water level reached 2 meters.'}),
                                             help_text='This is a text description of the observation you made.',
                                             label='Description')
    situationObserved = forms.ChoiceField(choices=EVENTKIND_CHOICES,
                                          help_text='This is the type of situation you observed.',
                                          label='Situation Observed')
    lat = forms.FloatField(label='Latitude', widget=forms.NumberInput(attrs={'readonly': 'readonly'}))
    lng = forms.FloatField(label='Longitude', widget=forms.NumberInput(attrs={'readonly': 'readonly'}))
    file_field = MultipleFileField(help_text='Optional: Submit any photos or videos you have related to the situation you observed. Only submit up to 10 files, with a total size of 10mb.',
                                   label='Images and videos',
                                   required=False)

    class Meta:
        model = e_ContextContribution
        fields = ['id', 'situationObserved', 'observationDescription', 'observationDate', 'observationPlace']
        labels = {
            'observationPlace': 'Observation Place',
        }
        help_texts = {
            'observationPlace': 'Move the map around to pick the location. Alternatively, you can text search for the desired position.'
        }
        widgets = {'observationPlace': LeafletWidget()}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['observationDate'].initial = datetime.now() # Automatically show in form today's date as the observation date
        self.fields['observationPlace'].required = False
    
    def clean_file_field(self):
        files = self.files.getlist('file_field')

        # Only accept up to 10 files
        if len(files) > 10:
            raise ValidationError("Too many files submitted. Only submit up to 10 files.")
        

        total_size = 0
        for file in files:
            if file:
                total_size = total_size + file.size
            else:
                raise forms.ValidationError("Could not read uploaded file.")
        
        # Only accept a total size of 10mb
        if total_size > 10485760:
            raise ValidationError("Total size of files is too large ( > 10mb ).")
        
        return files



class RejectionForm(forms.Form):
    last_rejection_reason = forms.CharField(max_length=500,
                                      widget=forms.Textarea(attrs={
                                            'placeholder': 'Enter a reason for the rejection.',
                                            'class': 'form-control',
                                        }))

class ReportForm(forms.Form):
    reason = forms.CharField(max_length=500,
                                      widget=forms.Textarea(attrs={
                                            'placeholder': 'Enter a reason for reporting.',
                                            'class': 'form-control',
                                        }))