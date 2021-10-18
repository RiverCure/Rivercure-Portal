from django import forms
from django.contrib.auth.models import User
from .models import Organization

class CreateOrganizationForm(forms.ModelForm):
    code    = forms.CharField(help_text='The code must be a no-whitespace string that identifies uniquely the organization (e.g.: APA)')
    name    = forms.CharField(help_text='The name should be the organization\'s full name (e.g.: Agência Portuguesa do Ambiente)')
    manager = forms.ModelChoiceField(queryset=User.objects, help_text='This is the first manager of the organization. More managers can be added by the first manager')
    
    class Meta:
        model = Organization
        fields = ['code', 'name']