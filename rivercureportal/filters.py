import django_filters
from users.models import User, Profile
from django import forms
from django_filters import DateFilter
from django.forms.widgets import TextInput
from .models import e_HydroFeature

        
class UserFilter(django_filters.FilterSet): 
    username = django_filters.CharFilter(label="Username", lookup_expr='icontains')
    
    class Meta:
        model = User
        fields = ['username', 'groups']    

class HydroFeatureFilter(django_filters.FilterSet):
    Name = django_filters.CharFilter(label="Name", lookup_expr='icontains')

    class Meta:
        model = e_HydroFeature
        fields = ['Name','type']