from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import e_District, e_HydroFeature
from context.models import e_Context, e_ContextEvent
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from leaflet.forms.widgets import LeafletWidget
from django import forms
from users.models import User
from django.contrib.auth.models import Group


def home(request):
    context = {
        'users': User.objects.all(),
        'groups': Group.objects.all()
        
    }
    return render(request, 'rivercureportal/home.html', context)


class ContextListView(ListView):
    model = e_Context
    template_name = 'rivercureportal/e_Context_list.html'
    context_object_name = 'contexts'
    ordering = ['Name']

class ContextDetailView(DetailView):
    model = e_Context
    context_object_name = 'context'
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
        
    
class HydroFeatureCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_HydroFeature
    form_class = HydroFeatureForm
    success_url = 'hydrofeature-list'

    def test_func(self):
        if self.request.user.has_perm('can_add_hydrofeatures'):
            return True
        else:
            return False

class HydroFeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_HydroFeature
    form_class = HydroFeatureForm
    success_url = 'hydrofeature-list'

    def test_func(self):
        if self.request.user.has_perm('can_update_hydrofeatures'):
            return True
        else:
            return False

    #only checking if he has permission to update hydrofeatures

class HydroFeatureDetailView(DetailView):
    model = e_HydroFeature
    context_object_name = 'Hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_detail.html'

class HydroFeatureDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_HydroFeature
    context_object_name = 'Hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_confirm_delete.html'
    success_url = 'hydrofeature_list'

    def test_func(self):
        if self.request.user.has_perm('can_delete_hydrofeatures'):
            return True
        else:
            return False
    

