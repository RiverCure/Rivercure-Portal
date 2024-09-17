import re

from django import forms

from django.forms import ValidationError

from django.db.models import Q

from organization.models import Organization, Membership

from .models import e_Context, e_ContextEvent
from .models import e_HydroFeature


class ContextDetailsForm(forms.ModelForm):

    hydroFeature = forms.ModelChoiceField(queryset=e_HydroFeature.objects.all(), required=False)
    picture = forms.ImageField(widget=forms.FileInput(attrs={'accept': 'image/*'}))

    def clean_Name(self):
        pattern = re.compile('^[\\w]+[-\\w]*$')
        data: str = self.cleaned_data['Name']
        if not bool(pattern.match(data)):
            raise ValidationError("Name must only have letters, numbers. These can be intercalated with slashes (-)")

        return data
    
    def clean_picture(self):
        picture = self.cleaned_data['picture']

        # Only accept a total size of 10mb
        if picture.size > 10485760:
            raise ValidationError("Size of file is too large ( > 10mb ).")
        
        return picture

    class Meta:
        model = e_Context
        fields = ['Name', 'hydroFeature', 'isPublic', 'description', 'picture']


class ContextInitialForm(forms.ModelForm):
    picture = forms.ImageField(required=False, widget=forms.FileInput(attrs={'accept': 'image/*'}))

    class Meta:
        model = e_Context
        fields = ['code', 'Name', 'hydroFeature', 'organization', 'isPublic', 'description', 'picture']
    
    def clean_picture(self):

        picture = self.cleaned_data['picture']
        
        if picture:
            # Only accept a total size of 10mb
            if picture.size > 10485760:
                raise ValidationError("Size of file is too large ( > 10mb ).")
        
        return picture

    def clean_code(self):
        pattern = re.compile('^[\\w]+[-\\w]*$')
        data: str = self.cleaned_data['code']
        if not bool(pattern.match(data)):
            raise ValidationError("Code must only have letters, numbers. These can be intercalated with slashes (-)")

        return data

    def clean_Name(self):
        pattern = re.compile('^[\\w]+[-\\w]*$')
        data: str = self.cleaned_data['Name']
        if not bool(pattern.match(data)):
            raise ValidationError("Name must only have letters, numbers. These can be intercalated with slashes (-)")

        return data

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super(ContextInitialForm, self).__init__(*args, **kwargs)
        # We only want to allow to choose options where the user is org_manager or org_contextManager of the organization
        memberships = Membership.objects.filter(user_id=user_id, access_granted=True, organization__is_active=True).filter(
            Q(permission='org_manager') | Q(permission='org_contextManager'))
        self.fields['organization'].queryset = Organization.objects.filter(membership__in=memberships)


class ContextForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    domain = forms.CharField(widget=forms.HiddenInput())
    alignment = forms.CharField(widget=forms.HiddenInput())
    refinement = forms.CharField(widget=forms.HiddenInput())
    boundaries = forms.CharField(widget=forms.HiddenInput())
    boundary_points = forms.CharField(widget=forms.HiddenInput())


class UploadContextForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    domain = forms.FileField(required=False)
    alignments = forms.FileField(required=False)
    refinements = forms.FileField(required=False)
    boundaries = forms.FileField(required=False)
    dtm_file = forms.FileField(required=False)
    friction_coefficient_file = forms.FileField(required=False)


class EventForm(forms.ModelForm):
    context_code = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = e_ContextEvent
        fields = ['Name', 'type', 'subtype', 'context_code', 'startDate', 'startTime', 'endDate', 'endTime', 'description',
                  'returnPeriod', 'warmUp', 'WritingPeriodicity', 'WritingPeriodicityUnit', 'UpdateMaximumValue', 'UpdateMaximumValueUnit']
        widgets = {
            'startDate': forms.TextInput(attrs={'placeholder': 'yyyy-mm-dd'}),
            'endDate': forms.TextInput(attrs={'placeholder': 'yyyy-mm-dd'}),
            'startTime': forms.TextInput(attrs={'placeholder': 'hh:mm:ss'}),
            'endTime': forms.TextInput(attrs={'placeholder': 'hh:mm:ss'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter description here'}),
        }

    def clean(self):
        super(EventForm, self).clean()

        if self.cleaned_data['startDate'] > self.cleaned_data['endDate']:
            self.add_error('startDate', 'Start date must be before or equal to end date')
        elif self.cleaned_data['startDate'] == self.cleaned_data['endDate']:
            if self.cleaned_data['startTime'] > self.cleaned_data['endTime']:
                self.add_error('startTime', 'Start time must be before or equal to end time')

        return self.cleaned_data
