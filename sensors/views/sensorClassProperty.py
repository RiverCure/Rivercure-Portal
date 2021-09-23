from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from sensors.models import SensorClass, SensorClassProperty
from sensors.forms import SensorClassPropertyForm
from django.urls import reverse
from organization.authorization import is_org_manager_or_sensor_manager, belongs_to_organization
from django.shortcuts import get_object_or_404

class SensorClassPropertyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'properties'
    template_name = 'sensors/sensorClassProperty/list.html'
    paginate_by = 15
    ordering = ['code']

    def get_context_data(self, **kwargs):
        context = super(SensorClassPropertyListView, self).get_context_data(**kwargs) # get the default context data
        context['sensorClass'] = SensorClass.objects.get(pk=self.kwargs['sensorClassId'])
        return context

    def get_queryset(self):
        return SensorClassProperty.objects.filter(sensorClass=self.kwargs['sensorClassId'])

    def test_func(self):
        user = self.request.user
        organization = get_object_or_404(SensorClass, pk=self.kwargs['sensorClassId']).organization
        return belongs_to_organization(user, organization)

class SensorClassPropertyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SensorClassProperty
    context_object_name = 'property'
    form_class = SensorClassPropertyForm
    template_name = 'sensors/sensorClassProperty/form.html'

    def get_success_url(self):
        return reverse('sensor-class-property-list', args=(self.kwargs['sensorClassId'],))

    def get_form_kwargs(self):
        kwargs = super(SensorClassPropertyCreateView, self).get_form_kwargs()
        kwargs.update({'sensorClass': self.sensorClass, 'property': None})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(SensorClassPropertyCreateView, self).get_context_data(**kwargs) # get the default context data
        context['sensorClass'] = self.sensorClass
        return context

    def form_valid(self, form):
        SensorClassProperty = form.save(commit=False)
        SensorClassProperty.sensorClass = self.sensorClass
        SensorClassProperty.save()
        return super().form_valid(form)

    def test_func(self):
        user = self.request.user
        self.sensorClass = get_object_or_404(SensorClass, pk=self.kwargs['sensorClassId'])
        return is_org_manager_or_sensor_manager(user, self.sensorClass.organization)

class SensorClassPropertyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SensorClassProperty
    context_object_name = 'property'
    template_name = 'sensors/sensorClassProperty/detail.html'
    pk_url_kwarg = 'sensorClassPropertyId'

    def test_func(self):
        user = self.request.user
        organization = self.get_object().sensorClass.organization
        return belongs_to_organization(user, organization)

class SensorClassPropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SensorClassProperty
    context_object_name = 'property'
    form_class = SensorClassPropertyForm
    template_name = 'sensors/sensorClassProperty/form.html'
    pk_url_kwarg = 'sensorClassPropertyId'

    def get_success_url(self):
        return reverse('sensor-class-property-detail', args=(self.kwargs['sensorClassId'], self.kwargs['sensorClassPropertyId']))

    def get_form_kwargs(self):
        kwargs = super(SensorClassPropertyUpdateView, self).get_form_kwargs()
        kwargs.update({'sensorClass': self.get_object().sensorClass, 'property': self.get_object()})
        return kwargs

    def test_func(self):
        user = self.request.user
        organization = self.get_object().sensorClass.organization
        return is_org_manager_or_sensor_manager(user, organization)

class SensorClassPropertyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SensorClassProperty
    context_object_name = 'property'
    template_name = 'sensors/sensorClassProperty/confirm_delete.html'
    pk_url_kwarg = 'sensorClassPropertyId'
    
    def get_success_url(self):
        return reverse('sensor-class-property-list', args=(self.get_object().sensorClass.id,))

    def test_func(self):
        user = self.request.user
        organization = self.get_object().sensorClass.organization
        return is_org_manager_or_sensor_manager(user, organization)