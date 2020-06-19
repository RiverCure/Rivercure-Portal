from django import forms
from django.forms import ModelForm
from django.contrib.gis.forms import fields
from .models import e_Context
from .models import e_HydroFeature
from leaflet.forms.widgets import LeafletWidget

class ContextForm(ModelForm):
    class Meta:
        model = e_Context
        fields = ('code', 'Name', 'hydroFeature')
        # widgets = {'hydroFeature': LeafletWidget(),
        #             'geom': LeafletWidget()}
        