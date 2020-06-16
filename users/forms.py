from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
     
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    institution = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    class Meta:
        model = Profile
        fields = ['institution','image', 'first_name', 'last_name']