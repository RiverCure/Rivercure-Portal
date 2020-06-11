from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)
    institution = forms.CharField(required=False)
    phoneNumber = forms.CharField(max_length=12)


    class Meta:
        model = User
        fields = ['username', 'email', 'institution', 'phoneNumber','password1', 'password2']