import django_filters
from users.models import User, Profile
from django import forms
from django_filters import DateFilter
from django.forms.widgets import TextInput

        
class UserFilter(django_filters.FilterSet):  
    class Meta:
        model = User
        fields = ['username', 'groups']    
        