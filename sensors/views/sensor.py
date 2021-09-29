from sensors.models import Sensor
from sensors.filters import OtherSensorFilter, SensorFilter
from organization.models import Organization
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.gis.geos import Point
from sensors.forms import GeoSensorForm, SensorFileForm, SensorForm, SensorObservationsFileForm
from django.urls import reverse
from sensors.authorization import sensor_general_create_permission_check, sensor_view_permission_check, sensor_edit_permission_check
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

class SensorListView(LoginRequiredMixin, ListView):
    context_object_name = 'sensors'
    template_name = 'sensors/sensors/list.html'
    paginate_by = 10
    ordering = ['code']

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.session['organizationName'] is not None:
                return super(SensorListView, self).dispatch(request, *args, **kwargs)
            else:
                raise Exception
        except:
            messages.warning(request, 'Please first choose an organization')
            return redirect('organization-list')

    def get_queryset(self):
        # Public sensors + Private sensors where the current user is member of the organization
        organizationName = self.request.session['organizationName']
        organization = get_object_or_404(Organization, name=organizationName)

        queryset = Sensor.objects.filter(state='active', sensorClass__organization=organization)
        filter = SensorFilter(self.request.GET, queryset.order_by('code'), organizationName=organizationName)
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        organizationName = self.request.session['organizationName']

        context['hasPerm'] = sensor_general_create_permission_check(self.request.user)
        context['form'] = SensorFileForm()
        queryset = self.get_queryset()
        filter = SensorFilter(self.request.GET, queryset, organizationName=organizationName)
        context['filter'] = filter
        return context

class OtherSensorListView(LoginRequiredMixin, ListView):
    context_object_name = 'sensors'
    template_name = 'sensors/sensors/otherSensors_list.html'
    paginate_by = 10
    ordering = ['code']

    def get_queryset(self):
        organization = get_object_or_404(Organization, name=self.request.session['organizationName'])
        queryset = Sensor.objects.exclude(sensorClass__organization=organization).exclude(isPublic=False)
        filter = OtherSensorFilter(self.request.GET, queryset.order_by('code'))
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        filter = OtherSensorFilter(self.request.GET, queryset)
        context['filter'] = filter
        return context

class SensorDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Sensor
    context_object_name = 'sensor'
    template_name = 'sensors/sensors/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SensorObservationsFileForm()
        context['hasPerm'] = sensor_edit_permission_check(self.request.user, self.get_object())
        return context
    
    def test_func(self):
        sensor = self.get_object()
        return sensor.isPublic or sensor_view_permission_check(self.request.user, sensor)

class SensorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Sensor
    form_class = SensorForm
    template_name = 'sensors/sensors/form.html'

    def get_success_url(self):
        return reverse('sensor-list')

    def get_form_kwargs(self):
        kwargs = super(SensorCreateView, self).get_form_kwargs()
        kwargs.update({'organizationName': self.request.session['organizationName']})
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.local = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        obj.save()
        return super().form_valid(form)

    def test_func(self):
        return sensor_general_create_permission_check(self.request.user)

class SensorGeoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sensor
    form_class = GeoSensorForm
    object_name = 'sensor'
    template_name = 'sensors/sensors/form.html'

    def get_success_url(self):
        return reverse('sensor-list')
    
    def form_valid(self, form):
        sensor = form.save(commit=False)
        sensor.local = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        sensor.save()
        return super().form_valid(form)

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object())

class SensorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sensor
    form_class = SensorForm
    object_name = 'sensor'
    template_name = 'sensors/sensors/form.html'

    def get_form_kwargs(self):
        kwargs = super(SensorUpdateView, self).get_form_kwargs()
        kwargs.update({'organizationName': self.request.session['organizationName']})
        return kwargs
    
    def form_valid(self, form):
        sensor = form.save(commit=False)
        sensor.local = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        sensor.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object())

class SensorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sensor
    context_object_name = 'sensor'
    template_name = 'sensors/sensors/confirm_delete.html'
    
    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object())