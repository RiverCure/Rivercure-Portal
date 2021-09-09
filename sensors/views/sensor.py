from sensors.models import Sensor
from sensors.filters import SensorFilter
from organization.models import Membership
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.gis.geos import Point
from sensors.forms import GeoSensorForm, SensorFileForm, SensorForm, SensorObservationsFileForm
from django.urls import reverse
from sensors.authorization import sensor_general_create_permission_check, sensor_view_permission_check, sensor_edit_permission_check

class SensorListView(LoginRequiredMixin, ListView):
    context_object_name = 'sensor'
    template_name = 'sensors/sensors/list.html'
    paginate_by = 15
    ordering = ['code']

    def get_queryset(self):
        # Public sensors + Private sensors where the current user is member of the organization
        queryset = (Sensor.objects.filter(isPublic=True) | Sensor.objects.filter(isPublic=False, organization__membership__in=Membership.objects.filter(user=self.request.user, access_granted=True))).distinct()
        filter = SensorFilter(self.request.GET, queryset.order_by('code'))
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)

        context["hasPerm"] = sensor_general_create_permission_check(self.request.user)
        context["form"] = SensorFileForm()
        queryset = self.get_queryset()
        filter = SensorFilter(self.request.GET, queryset)
        context["filter"] = filter

        return context


class SensorDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Sensor
    context_object_name = 'sensor'
    template_name = 'sensors/sensors/detail.html'

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is in the organization
        sensor = self.get_object()
        return sensor.isPublic or sensor_view_permission_check(self.request.user, sensor)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SensorObservationsFileForm()
        context["hasPerm"] = sensor_edit_permission_check(self.request.user, self.get_object())
        return context

class SensorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Sensor
    form_class = SensorForm
    template_name = 'sensors/sensors/form.html'

    def get_success_url(self):
        return reverse('sensor-list')

    def get_form_kwargs(self):
        kwargs = super(SensorCreateView, self).get_form_kwargs()
        kwargs.update({'user_id': self.request.user.id})
        return kwargs

    def test_func(self):
        return sensor_general_create_permission_check(self.request.user)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.geom = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        obj.save()
        return super().form_valid(form)

class SensorGeoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Sensor
    form_class = GeoSensorForm
    object_name = 'sensor'
    template_name = 'sensors/sensors/form.html'

    def get_success_url(self):
        return reverse('sensor-list')
    
    def form_valid(self, form):
        sensor = form.save(commit=False)
        sensor.geom = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
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
        kwargs.update({'user_id': self.request.user.id})
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