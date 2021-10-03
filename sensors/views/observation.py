from django.db import connection
from sensors.models import Sensor, SensorClassProperty, SensorObservation, SensorObservationValue
from sensors.forms import SensorObservationForm, SensorObservationsFileForm
from django.urls import reverse
from sensors.filters import ObservationFilter
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from sensors.authorization import sensor_general_create_permission_check, sensor_view_permission_check, sensor_edit_permission_check
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import imghdr

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

def calculate_computed_prop(derivedPropValue, instruction):
    globals = {'__builtins__': None} # prevents use of other methods
    locals = {'otherValue': derivedPropValue}
    exec(instruction, globals, locals)
    propValue = locals['newValue'] # extract the computed value
    return propValue

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
            propValue = form.cleaned_data[tag]                

            if prop.type == 'image' and propValue is not None:
                extension = imghdr.what(propValue)
                path = default_storage.save(f'observation_files/Sensor-{observation.id}_Property-{prop.id}.{extension}', ContentFile(propValue.read()))
                SensorObservationValue.objects.create(property=prop, observation=observation, value=path)
            elif propValue is not None: # any other type
                    SensorObservationValue.objects.create(property=prop, observation=observation, value=propValue)

        
        # Derived properties
        derivedProps = SensorClassProperty.objects.filter(sensorClass=self.sensor.sensorClass, derivedBy__isnull=False, isImmediate=True)
        for prop in derivedProps:
            propValue = calculate_computed_prop(form.cleaned_data[f'value_of_{prop.derivedBy.name}'], prop.instruction)
            if propValue is not None:
                SensorObservationValue.objects.create(property=prop, observation=observation, value=propValue)

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