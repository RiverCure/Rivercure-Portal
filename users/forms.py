from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from organization.models import Organization, Membership

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
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)

        # Get the sensor class properties of that sensor's sensor class
        self.fields['defaultOrganization'].queryset = Organization.objects.filter(membership__in=Membership.objects.filter(user=self.user, access_granted=True, organization__is_active=True))
        self.fields['defaultOrganization'].required = False
        self.fields['defaultOrganization'].label = 'Default organization'

    class Meta:
        model = Profile
        fields = ['image', 'first_name', 'last_name', 'defaultOrganization']