from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from sensors.forms import SensorClassForm
from sensors.models import SensorClass, SensorObservation
from django.urls import reverse
from sensors.authorization import sensor_general_create_permission_check
from organization.models import Organization
from organization.authorization import is_org_or_sensor_manager
from django.shortcuts import get_object_or_404

class SensorClassListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'sensorClass'
    template_name = 'sensors/sensorClass/list.html'
    paginate_by = 15
    ordering = ['code']

    def get_queryset(self):
        return SensorClass.objects.filter(organization=self.kwargs['organizationId'])

    def get_context_data(self, **kwargs):
        context = super(SensorClassListView, self).get_context_data(**kwargs) # get the default context data
        context['organization'] = Organization.objects.get(pk=self.kwargs['organizationId'])
        return context

    def test_func(self):
        user = self.request.user
        organization = get_object_or_404(Organization, pk=self.kwargs['organizationId'])
        return is_org_or_sensor_manager(user, organization)

class SensorClassCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SensorClass
    context_object_name = 'sensorClass'
    form_class = SensorClassForm
    template_name = 'sensors/sensorClass/form.html'

    def get_success_url(self):
        return reverse('sensor-class-list', args=(self.kwargs['organizationId'],))

    def form_valid(self, form):
        sensorClass = form.save(commit=False)
        sensorClass.organization = Organization.objects.get(pk=self.kwargs['organizationId'])
        sensorClass.save()
        return super().form_valid(form)

    def test_func(self):
        user = self.request.user
        organization = get_object_or_404(Organization, pk=self.kwargs['organizationId'])
        return is_org_or_sensor_manager(user, organization)

class SensorClassDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SensorClass
    context_object_name = 'sensorClass'
    template_name = 'sensors/sensorClass/detail.html'
    pk_url_kwarg = 'sensorClassId'

    def test_func(self):
        user = self.request.user
        organization = self.get_object().organization
        return is_org_or_sensor_manager(user, organization)

class SensorClassUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SensorClass
    context_object_name = 'sensorClass'
    form_class = SensorClassForm
    template_name = 'sensors/sensorClass/form.html'
    pk_url_kwarg = 'sensorClassId'

    def get_success_url(self):
        return reverse('sensor-class-detail', args=(self.kwargs['sensorClassId'],))

    def test_func(self):
        user = self.request.user
        organization = self.get_object().organization
        return is_org_or_sensor_manager(user, organization)


class SensorClassDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SensorClass
    context_object_name = 'sensorClass'
    template_name = 'sensors/sensorClass/confirm_delete.html'
    pk_url_kwarg = 'sensorClassId'
    
    def get_success_url(self):
        return reverse('sensor-class-list', args=(self.get_object().organization.id,))

    def test_func(self):
        user = self.request.user
        organization = self.get_object().organization
        return is_org_or_sensor_manager(user, organization)