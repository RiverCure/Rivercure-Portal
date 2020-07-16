from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import e_District, e_HydroFeature
from context.models import e_Context
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from leaflet.forms.widgets import LeafletWidget
from django import forms


class ContextListView(ListView):
    model = e_Context
    template_name = 'rivercureportal/home.html'
    context_object_name = 'contexts'
    ordering = ['Name']

class ContextDetailView(DetailView):
    model = e_Context
    template_name = 'rivercureportal/e_Context_detail.html'

def about(request):
    return render(request, 'rivercureportal/about.html')

class HydroFeatureListView(ListView):
    model = e_HydroFeature
    context_object_name = 'hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_list.html'

class HydroFeatureForm(forms.ModelForm):
    class Meta:
        model = e_HydroFeature
        fields = ['Name', 'type', 'area', 'length','PartOf', 'flowsInto', 'geom']
        widgets = {'geom': LeafletWidget()}
    
class HydroFeatureCreateView(LoginRequiredMixin,CreateView):
    model = e_HydroFeature
    form_class = HydroFeatureForm
    success_url = 'hydrofeature-list'

class HydroFeatureUpdateView(LoginRequiredMixin,UpdateView):
    model = e_HydroFeature
    fields = ['Name', 'type', 'area', 'length','PartOf', 'flowsInto', 'geom']
    success_url = 'hydrofeature-list'

class HydroFeatureDetailView(DetailView):
    model = e_HydroFeature
    context_object_name = 'Hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_detail.html'


