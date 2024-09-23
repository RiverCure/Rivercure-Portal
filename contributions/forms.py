from datetime import datetime

from leaflet.forms.widgets import LeafletWidget

from django import forms
from django.forms import ValidationError

from django.utils.translation import gettext_lazy as _

from .models import e_ContextContribution, SituationChoices, TornadoType

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
                                              help_text=_('Date in which you have made your observation.'),
                                              label=_('Observation Date'))
    observationDescription = forms.CharField(widget=forms.Textarea(attrs={'placeholder': _('Enter a description of what you observed. Example: The water level reached 2 meters.')}),
                                             help_text=_('Text description of the observation you made.'),
                                             label=_('Description'))
    situationObserved = forms.ChoiceField(choices=SituationChoices.choices,
                                          help_text=_('Type of situation you observed.'),
                                          label=_('Situation Observed'))
    lat = forms.FloatField(label='Latitude', widget=forms.NumberInput(attrs={'readonly': 'readonly'}))
    lng = forms.FloatField(label='Longitude', widget=forms.NumberInput(attrs={'readonly': 'readonly'}))
    file_field = MultipleFileField(help_text=_('Optional: Submit any photos or videos you have related to the situation you observed. Only submit up to 10 files, with a total size of 10mb.'),
                                   label=_('Images and videos'),
                                   required=False)
    floating_objects_time = forms.DurationField(label=_('Transit Time of Floating Objects'),
                                                required=False,
                                                widget=forms.TextInput(attrs={'placeholder': 'Time in seconds.',}),
                                                help_text=_('Write in total number of seconds or in the format HH:MM:SS. For example, writing 00:01:30 or 90 is the same (both mean 90 seconds).'))
    water_height = forms.FloatField(label=_('Water Height'),
                                    required=False,
                                    widget=forms.NumberInput(attrs={'placeholder': _('Height in meters.'),}))
    velocity = forms.IntegerField(label=_('Velocity'),
                                  required=False,
                                  widget=forms.NumberInput(attrs={'placeholder': _('Velocity in km/h.')}))
    tornado_type = forms.ChoiceField(choices=TornadoType.choices,
                                     label=_('Tornado Type'),
                                     required=False)

    class Meta:
        model = e_ContextContribution
        fields = ['id', 'situationObserved', 'observationDescription', 'observationDate', 'observationPlace']
        labels = {
            'observationPlace': _('Observation Place'),
        }
        help_texts = {
            'observationPlace': _('Move the map around to pick the location. Alternatively, you can text search for the desired location.')
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
            raise ValidationError(_("Too many files submitted. Only submit up to 10 files."))
        

        total_size = 0
        for file in files:
            if file:
                total_size = total_size + file.size
            else:
                raise forms.ValidationError(_("Could not read uploaded file."))
        
        # Only accept a total size of 10mb
        if total_size > 10485760:
            raise ValidationError(_("Total size of files is too large ( > 10mb )."))
        
        return files



class RejectionForm(forms.Form):
    last_rejection_reason = forms.CharField(max_length=500,
                                      widget=forms.Textarea(attrs={
                                            'placeholder': _('Enter a reason for the rejection.'),
                                            'class': 'form-control',
                                        }))

class ReportForm(forms.Form):
    reason = forms.CharField(max_length=500,
                                      widget=forms.Textarea(attrs={
                                            'placeholder': _('Enter a reason for reporting.'),
                                            'class': 'form-control',
                                        }))