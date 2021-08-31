from sensors.models import Sensor, SensorObservation
from sensors.forms import SensorObservationForm, SensorObservationsFileForm
from django.urls import reverse
from django.http import HttpResponse
from sensors.filters import ObservationFilter
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from sensors.authorization import sensor_general_create_permission_check, sensor_view_permission_check, sensor_edit_permission_check

class SensorObservationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = SensorObservationForm
    model = SensorObservation
    template_name = 'sensors/observations/form.html'
    context_object_name = 'observation'

    def get_success_url(self):
        return reverse('sensor-observation-list',args=(self.kwargs['pk'],))

    def form_valid(self, form):
        observation = form.save(commit=False)
        observation.sensor = Sensor.objects.get(pk=self.kwargs['pk'])
        observation.save()
        return super().form_valid(form)

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_general_create_permission_check(self.request.user)

def SensorObservationListView(request, pk):
    sensor_code = pk
    sensor = Sensor.objects.get(code=sensor_code)

    if not sensor_view_permission_check(request.user, sensor):
        return HttpResponse('Unauthorized', status=401)
    
    qs = SensorObservation.objects.filter(sensor=sensor_code)

    obs_filter = ObservationFilter(request.GET, queryset=qs)
    obs = obs_filter.qs

    page = request.GET.get('page', 1)
    obs_paginator = Paginator(obs, 30)

    page_obj = obs_paginator.get_page(page)

    try:
        obs = obs_paginator.page(page)
    except EmptyPage :
        obs = obs_paginator.page(page)
    except PageNotAnInteger:
        obs = obs_paginator.page(page)

    hasPerm = sensor_edit_permission_check(request.user, sensor)

    context= {
        'obs': obs,
        'filter' : obs_filter,
        'page_obj' : page_obj,
        'sensor': sensor,
        'hasPerm': hasPerm,
        'form': SensorObservationsFileForm()
    }

    return render(request, "sensors/observations/list.html", context)

class SensorObservationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/observations/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hasPerm"] = sensor_edit_permission_check(self.request.user, self.get_object().sensor)
        return context

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_view_permission_check(self.request.user, self.get_object().sensor)

class SensorObservationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = SensorObservationForm
    model = SensorObservation
    context_object_name = 'observation'

    def get_success_url(self):
        return reverse('sensor-observation-detail',args=(self.object.sensor.code,self.object.id,))

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_edit_permission_check(self.request.user, self.get_object().sensor)

class SensorObservationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/observations/confirm_delete.html'

    def get_success_url(self):
        return reverse('sensor-observation-list',args=(self.object.sensor.code,))
    
    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_edit_permission_check(self.request.user, self.get_object().sensor)