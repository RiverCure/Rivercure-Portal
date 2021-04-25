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
from django.urls import reverse_lazy
from django_filters.views import FilterView
from notifications.models import Notification
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    try:
        return user.groups.filter(name='Admin').exists()
    except:
        return False

def is_admin_or_manager(user):
    try:
        return user.groups.filter(name='Admin').exists() or user.groups.filter(name='Manager').exists()
    except:
        return False

class ProfileDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    context_object_name = 'u'
    template_name = 'rivercureportal/userprofile.html'

    def test_func(self):
        return is_admin(self.request.user) or self.request.user == self.get_object()

@user_passes_test(is_admin)
def users(request):
    if not is_admin(request.user):
        return HttpResponse('Unauthorized', status=401)

    user_list = User.objects.all()
    user_filter = UserFilter(request.GET, queryset=user_list)

    context = {
        'users': user_list,
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
    paginate_by = 12
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = HydroFeatureFilter(self.request.GET, queryset=e_HydroFeature.objects.all())
        return context

class HydroFeatureForm(forms.ModelForm):
    class Meta:
        model = e_HydroFeature
        fields = ['Name', 'type', 'PartOf', 'flowsInto', 'geom']
        widgets = {'geom': LeafletWidget()}
        
    
class HydroFeatureCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_HydroFeature
    form_class = HydroFeatureForm
    success_url = reverse_lazy('hydrofeature-list')

    def test_func(self):
        return is_admin_or_manager(self.request.user)

class HydroFeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_HydroFeature
    form_class = HydroFeatureForm
    success_url = reverse_lazy('hydrofeature-list')

    def test_func(self):
        return is_admin_or_manager(self.request.user)


class HydroFeatureDetailView(DetailView):
    model = e_HydroFeature
    context_object_name = 'Hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_detail.html'

class HydroFeatureDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_HydroFeature
    context_object_name = 'Hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_confirm_delete.html'
    success_url = reverse_lazy('hydrofeature-list')

    def test_func(self):
        return is_admin_or_manager(self.request.user)

@login_required
def clearNotifications(request):
    notifications = Notification.objects.filter(recipient=request.user)
    if notifications.exists():
        notifications.delete()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))