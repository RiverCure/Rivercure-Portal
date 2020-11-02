from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from leaflet.forms.widgets import LeafletWidget
from django.contrib.auth.models import Group
from django import forms
from users.models import User, Profile
from context.models import e_Context
from .models import e_HydroFeature
from sensors.models import e_Sensor
from .filters import UserFilter, HydroFeatureFilter
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

class ProfileDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    context_object_name = 'u'
    template_name = 'rivercureportal/userprofile.html'
    def test_func(self):
        if self.request.user.groups.filter(name='Administration').exists():
            return True
        else:
            return False

def users(request):

    user_list = User.objects.all().distinct('username')
    user_filter = UserFilter(request.GET, queryset=user_list)

    context = {
        'users': User.objects.all(),
        'groups': Group.objects.all(),
        'filter' :  user_filter,
    }

    return render(request, 'rivercureportal/users.html', context)

def home(request):
    context = {
        'users': User.objects.all(),
        'groups': Group.objects.all(),
        'contexts' : e_Context.objects.all(),
        'recent_context' : e_Context.objects.all().first(),
        'recent_sensor' : e_Sensor.objects.all().first()     
    }

    return render(request, 'rivercureportal/home.html', context)

def about(request):
    return render(request, 'rivercureportal/about.html')

class HydroFeatureListView(LoginRequiredMixin, ListView):
    model = e_HydroFeature
    context_object_name = 'hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_list.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = HydroFeatureFilter(self.request.GET, queryset=self.get_queryset())
        #context['string'] = 'stringgg'
        return context


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
        if self.request.user.groups.filter(name='Manager').exists():
            return True
        else:
            return False

class HydroFeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_HydroFeature
    form_class = HydroFeatureForm
    success_url = 'hydrofeature-list'

    def test_func(self):
        if self.request.user.groups.filter(name='Manager').exists():
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
        if self.request.user.groups.filter(name='Manager').exists():
            return True
        else:
            return False
