from sensors.models import Sensor, SensorClassProperty, SensorObservation, SensorObservationValue
from sensors.forms import SensorObservationForm, SensorObservationsFileForm
from django.urls import reverse
from django.http import HttpResponse
from sensors.filters import ObservationFilter
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, render
from sensors.authorization import sensor_general_create_permission_check, sensor_view_permission_check, sensor_edit_permission_check
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os

class SensorObservationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'observations'
    template_name = 'sensors/observations/list.html'
    paginate_by = 15

    def setup(self, request, *args, **kwargs):
        self.sensor =  get_object_or_404(Sensor, pk=kwargs['sensorId'])
        self.queryset = SensorObservation.objects.filter(sensor=self.sensor).order_by('id')
        return super().setup(request, *args, **kwargs)

    def get_queryset(self):
        self.filter = ObservationFilter(self.request.GET, queryset=self.queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(SensorObservationListView, self).get_context_data(**kwargs)
        context['hasPerm'] = sensor_edit_permission_check(self.request.user, self.sensor)
        context['form'] = SensorObservationsFileForm()
        context['sensor'] = self.sensor
        context['filter'] = self.filter

        return context

    def test_func(self):
        return sensor_view_permission_check(self.request.user, self.sensor)

class SensorObservationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = SensorObservationForm
    model = SensorObservation
    template_name = 'sensors/observations/form.html'
    context_object_name = 'observation'

    def setup(self, request, *args, **kwargs):
        self.sensor =  get_object_or_404(Sensor, pk=kwargs['sensorId'])
        return super().setup(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('sensor-observation-list',args=(self.sensor.pk,))

    def get_form_kwargs(self):
        kwargs = super(SensorObservationCreateView, self).get_form_kwargs()
        # Pass the sensor to the form (SensorObservationForm)
        kwargs.update({'sensor': self.sensor})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(SensorObservationCreateView, self).get_context_data(**kwargs)
        context['sensor'] = self.sensor
        return context

    def form_valid(self, form):
        observation = form.save(commit=False)
        observation.sensor = self.sensor
        observation.save()

        # Save SensorObservationValue depending on the prop type
        for prop in form.cleaned_data['properties']:
            tag = f'value_of_{prop.name}'
            if prop.type == 'image':
                extension = form.cleaned_data[tag].content_type.split("/",1)[1]
                path = default_storage.save(f'observation_files/Sensor-{observation.id}_Property-{prop.id}.{extension}', ContentFile(form.cleaned_data[tag].read()))
                tmp_file = os.path.join(settings.MEDIA_ROOT, path)
                SensorObservationValue.objects.create(property=prop, observation=observation, value=path)
            else:
                SensorObservationValue.objects.create(property=prop, observation=observation, value=form.cleaned_data[tag])

        return super().form_valid(form)

    def test_func(self):
        return sensor_general_create_permission_check(self.request.user)

class SensorObservationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/observations/detail.html'
    pk_url_kwarg = 'observationId'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hasPerm'] = sensor_edit_permission_check(self.request.user, self.get_object().sensor)
        return context

    def test_func(self):
        return sensor_view_permission_check(self.request.user, self.get_object().sensor)

class SensorObservationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = SensorObservationForm
    model = SensorObservation
    template_name = 'sensors/observations/form.html'
    context_object_name = 'observation'
    pk_url_kwarg = 'observationId'

    def setup(self, request, *args, **kwargs):
        self.sensor =  get_object_or_404(Sensor, pk=kwargs['sensorId'])
        return super().setup(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('sensor-observation-detail',args=(self.sensor.pk,self.object.pk))

    def get_form_kwargs(self):
        kwargs = super(SensorObservationUpdateView, self).get_form_kwargs()
        # Pass the sensor to the form (SensorObservationForm)
        kwargs.update({'sensor': self.sensor})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(SensorObservationUpdateView, self).get_context_data(**kwargs)
        context['sensor'] = self.sensor
        return context

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object().sensor)

class SensorObservationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/observations/confirm_delete.html'
    pk_url_kwarg = 'observationId'

    def get_success_url(self):
        return reverse('sensor-observation-list',args=(self.object.sensor.pk,))
    
    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object().sensor)