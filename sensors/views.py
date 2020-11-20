from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import e_Sensor, e_SensorAlarm, e_SensorObservation
from leaflet.forms.widgets import LeafletWidget
from django import forms
from .filters import SensorFilter, ObservationFilter
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from context.models import e_ContextSensor, e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.urls  import reverse


class SensorObservationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/e_SensorObservation_detail.html'
    def test_func(self):
        if self.request.user.groups.filter(name='SensorManager').exists():
            return True
        else:
            return False


@permission_required('sensors.view_e_sensor_observation', raise_exception=True)
def SensorObservationListView(request):
    qs = e_SensorObservation.objects.all()
    obs_filter = ObservationFilter(request.GET, queryset=qs)
    
    obs = obs_filter.qs
   
    page = request.GET.get('page', 1)
    obs_paginator = Paginator(obs, 15)

    page_obj = obs_paginator.get_page(page)

    try:
       obs = obs_paginator.page(page)
    except EmptyPage :
       obs = obs_paginator.page(page)
    except PageNotAnInteger:
       obs = obs_paginator.page(page)
    
    context={
        'obs': obs,
        'filter' : obs_filter,
        'page_obj' : page_obj
        
    }

    return render(request, "sensors/e_Sensor_observations.html", context)


@permission_required('sensors.view_e_sensor', raise_exception=True)
def SensorListView(request):
    
    sensor_list = e_Sensor.objects.all()
    sensor_filter = SensorFilter(request.GET, queryset=sensor_list)
    context ={
        'filter': sensor_filter,
        
    }

    return render(request, 'sensors/e_Sensor_list.html', context)


class SensorDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_Sensor
    context_object_name = 'sensor'
    template_name = 'sensors/e_Sensor_detail.html'

    def test_func(self):
        if self.request.user.has_perm('sensors.view_e_sensor'):
            return True
        else:
            return False

class SensorForm(forms.ModelForm):
    class Meta:
        model = e_Sensor
        fields = ['code','Name','responsibleUser','modalityType','type','description','version', 'timeZoneAbbreviation', 'timeZoneOffset', 'geom',]
        widgets = {'geom': LeafletWidget()}

class SensorCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_Sensor
    form_class = SensorForm

    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        if self.request.user.groups.filter(name='SensorManager').exists():
            return True
        else:
            return False
            
class SensorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Sensor
    form_class = SensorForm
    

    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        if self.request.user.has_perm('sensors.change_e_sensor'):
            return True
        else:
            return False

    #only checking if he has permission to update sensors

class SensorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_Sensor
    context_object_name = 'Sensor'
    template_name = 'sensors/e_Sensor_confirm_delete.html'
    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        if self.request.user.has_perm('sensors.delete_e_sensor'):
            return True
        else:
            return False

