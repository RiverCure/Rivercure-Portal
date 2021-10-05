from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from sensors.forms import SensorClassForm
from sensors.models import SensorClass
from django.urls import reverse
from organization.models import Organization
from organization.authorization import belongs_to_organization, is_org_manager_or_sensor_manager
from django.shortcuts import get_object_or_404

class SensorClassListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'sensorClass'
    template_name = 'sensors/sensorClass/list.html'
    paginate_by = 15
    ordering = ['code']

    def setup(self, request, *args, **kwargs):
        self.organization =  get_object_or_404(Organization, pk=kwargs['organizationId'])
        return super().setup(request, *args, **kwargs)

    def get_queryset(self):
        return SensorClass.objects.filter(organization=self.organization).order_by('name')

    def get_context_data(self, **kwargs):
        context = super(SensorClassListView, self).get_context_data(**kwargs) # get the default context data
        context['organization'] = self.organization
        context['hasPerm'] = is_org_manager_or_sensor_manager(self.request.user, context['organization'])
        return context

    def test_func(self):
        return belongs_to_organization(self.request.user, self.organization)

class SensorClassCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SensorClass
    context_object_name = 'sensorClass'
    form_class = SensorClassForm
    template_name = 'sensors/sensorClass/form.html'

    def get_success_url(self):
        return reverse('sensor-class-list', args=(self.kwargs['organizationId'],))

    def get_form_kwargs(self):
        kwargs = super(SensorClassCreateView, self).get_form_kwargs()
        kwargs.update({'organization': self.organization, 'sensorClass': None})
        return kwargs

    def form_valid(self, form):
        sensorClass = form.save(commit=False)
        sensorClass.organization = self.organization
        sensorClass.save()
        return super().form_valid(form)

    def test_func(self):
        user = self.request.user
        self.organization = get_object_or_404(Organization, pk=self.kwargs['organizationId'])
        return is_org_manager_or_sensor_manager(user, self.organization)

class SensorClassDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SensorClass
    context_object_name = 'sensorClass'
    template_name = 'sensors/sensorClass/detail.html'
    pk_url_kwarg = 'sensorClassId'

    def test_func(self):
        return belongs_to_organization(self.request.user, self.get_object().organization)

class SensorClassUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SensorClass
    context_object_name = 'sensorClass'
    form_class = SensorClassForm
    template_name = 'sensors/sensorClass/form.html'
    pk_url_kwarg = 'sensorClassId'

    def get_success_url(self):
        return reverse('sensor-class-detail', args=(self.kwargs['sensorClassId'],))

    def get_form_kwargs(self):
        kwargs = super(SensorClassUpdateView, self).get_form_kwargs()
        kwargs.update({'organization': self.get_object().organization, 'sensorClass': self.get_object()})
        return kwargs

    def test_func(self):
        return is_org_manager_or_sensor_manager(self.request.user, self.get_object().organization)


class SensorClassDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SensorClass
    context_object_name = 'sensorClass'
    template_name = 'sensors/sensorClass/confirm_delete.html'
    pk_url_kwarg = 'sensorClassId'
    
    def get_success_url(self):
        return reverse('sensor-class-list', args=(self.get_object().organization.id,))

    def test_func(self):
        return is_org_manager_or_sensor_manager(self.request.user, self.get_object().organization)