from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import e_District, e_HydroFeature
from context.models import e_Context
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from leaflet.forms.widgets import LeafletWidget


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
    #context_object_name = 'e_Hydrofeatures'
    
class HydroFeatureCreateView(LoginRequiredMixin,CreateView):
    model = e_HydroFeature
    fields = ['Name', 'type', 'area', 'length','PartOf', 'flowsInto', 'geom']
    widgets = {'geom': LeafletWidget()}
    success_url = 'rivercure-hydrofeatures'

class HydroFeatureUpdateView(LoginRequiredMixin,UpdateView):
    model = e_HydroFeature
    fields = ['Name', 'type', 'area', 'length','PartOf', 'flowsInto', 'geom']
    #widgets = {'geom': LeafletWidget()}
    success_url = 'rivercure-hydrofeatures'