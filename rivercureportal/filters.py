import django_filters
from users.models import User, Profile
from django import forms
from django_filters import DateFilter
from django.forms.widgets import TextInput
from .models import e_HydroFeature

        
class UserFilter(django_filters.FilterSet):  
    class Meta:
        model = User
        fields = ['username', 'groups']    

class HydroFeatureFilter(django_filters.FilterSet):
    class Meta:
        model = e_HydroFeature
        fields = ['type',]