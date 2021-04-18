from django import forms
from django.contrib.auth.models import User
from .models import Organization

class CreateOrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']
    
    manager = forms.ModelChoiceField(queryset=User.objects)