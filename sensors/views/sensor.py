from sensors.models import Sensor, SensorThresholdsValues
from sensors.filters import OtherSensorFilter, SensorFilter
from organization.models import Organization
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.gis.geos import Point
from sensors.forms import GeoSensorForm, SensorFileForm, SensorForm, SensorObservationsFileForm, SensorThresholdForm
from django.urls import reverse
from sensors.authorization import sensor_general_create_permission_check, sensor_view_permission_check, sensor_edit_permission_check
from django.shortcuts import get_object_or_404


class SensorListView(LoginRequiredMixin, ListView):
    context_object_name = 'sensors'
    template_name = 'sensors/sensors/list.html'
    paginate_by = 10
    ordering = ['code']

    def get_queryset(self):
        # Public sensors + Private sensors where the current user is member of the organization
        organizationCode = self.request.session['organizationCode']
        if organizationCode:
            organization = get_object_or_404(Organization, code=organizationCode)
            queryset = Sensor.objects.filter(state='active', sensorClass__organization=organizationCode)
        else:
            queryset = Sensor.objects.filter(state='active', sensorClass__organization=None)

        filter = SensorFilter(self.request.GET, queryset.order_by('code'), organizationCode=organizationCode)
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        organizationCode = self.request.session['organizationCode']

        context['hasPerm'] = sensor_general_create_permission_check(self.request.user)
        context['form'] = SensorFileForm()
        queryset = self.get_queryset()
        filter = SensorFilter(self.request.GET, queryset, organizationCode=organizationCode)
        context['filter'] = filter
        return context


class OtherSensorListView(LoginRequiredMixin, ListView):
    context_object_name = 'sensors'
    template_name = 'sensors/sensors/otherSensors_list.html'
    paginate_by = 10
    ordering = ['code']

    def get_queryset(self):
        organizationCode = self.request.session['organizationCode']
        if organizationCode:
            organization = get_object_or_404(Organization, code=organizationCode)
            queryset = Sensor.objects.exclude(sensorClass__organization=organization).exclude(isPublic=False)
        else:
            queryset = Sensor.objects.exclude(isPublic=False)

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
        kwargs.update({'organizationCode': self.request.session['organizationCode']})
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
        kwargs.update({'organizationCode': self.request.session['organizationCode']})
        return kwargs

    def form_valid(self, form):
        sensor = form.save(commit=False)
        sensor.local = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        sensor.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('sensor-detail', args=(self.kwargs['pk'],))

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


class SensorThresholdUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sensor
    form_class = SensorThresholdForm
    object_name = 'sensor'
    template_name = 'sensors/sensors/form-thresholds.html'

    def get_form_kwargs(self):
        kwargs = super(SensorThresholdUpdateView, self).get_form_kwargs()
        kwargs.update({'sensor': self.get_object()})
        return kwargs

    def form_valid(self, form):
        sensor = form.save()
        for prop in form.cleaned_data["properties"]:
            lower_critical = form.cleaned_data[f'value_of_{prop}_threshold_lower_critical']
            upper_critical = form.cleaned_data[f'value_of_{prop}_threshold_upper_critical']
            lower_noncritical = form.cleaned_data[f'value_of_{prop}_threshold_lower_noncritical']
            upper_noncritical = form.cleaned_data[f'value_of_{prop}_threshold_upper_noncritical']

            SensorThresholdsValues.objects.update_or_create(
                sensor=sensor, property=prop,
                thresholdLowerCritical=lower_critical,
                thresholdUpperCritical=upper_critical,
                thresholdLowerNoncritical=lower_noncritical,
                thresholdUpperNoncritical=upper_noncritical)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('sensor-detail', args=(self.kwargs['pk'],))

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object())
