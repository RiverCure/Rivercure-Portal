from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from leaflet.forms.widgets import LeafletWidget
from django.contrib.auth.models import Group
from django import forms
from users.models import User, Profile
from context.models import e_Context
from .models import e_HydroFeature
from sensors.models import Sensor
from .filters import UserFilter, HydroFeatureFilter
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse, reverse_lazy
from django_filters.views import FilterView
from notifications.models import Notification
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from rivercureportal.authorization import is_platform_admin, is_platform_admin_or_manager

class ProfileDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    context_object_name = 'u'
    template_name = 'rivercureportal/userprofile.html'

    def test_func(self):
        return is_platform_admin(self.request.user) or self.request.user == self.get_object()

@user_passes_test(is_platform_admin)
def users(request):
    if not is_platform_admin(request.user):
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
        'recent_sensor' : Sensor.objects.all().first()
    }

    return render(request, 'rivercureportal/home.html', context)

def about(request):
    return render(request, 'rivercureportal/about.html')

class HydroFeatureListView(LoginRequiredMixin, ListView):
    model = e_HydroFeature
    context_object_name = 'hydrofeatures'
    template_name = 'rivercureportal/e_HydroFeature_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = e_HydroFeature.objects.all()
        filter = HydroFeatureFilter(self.request.GET, queryset.order_by('Name'))
        return filter.qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        filter = HydroFeatureFilter(self.request.GET, queryset)
        context["filter"] = filter
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
        return is_platform_admin_or_manager(self.request.user)

class HydroFeatureUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_HydroFeature
    context_object_name = 'hydrofeature'
    form_class = HydroFeatureForm
    success_url = reverse_lazy('hydrofeature-list')

    def test_func(self):
        return is_platform_admin_or_manager(self.request.user)


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
        return is_platform_admin_or_manager(self.request.user)

@login_required
def clearNotifications(request):
    notifications = Notification.objects.filter(recipient=request.user)
    if notifications.exists():
        notifications.mark_all_as_read()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    context_object_name = 'notifications'
    template_name = 'rivercureportal/notification_list.html'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        if 'HTTP_REFERER' in self.request.META:
            context["previous_page"] = self.request.META['HTTP_REFERER']
        else:
            context["previous_page"] = reverse('rivercure-home')
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    name = 'Edit user'
    model = User
    context_object_name = 'u'
    template_name = 'rivercureportal/user_form.html'
    fields = ['groups']

    def get_success_url(self):
        return reverse_lazy('profile-detail', args=(self.get_object().pk,))

    def test_func(self):
        return is_platform_admin(self)