from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import e_Sensor, e_SensorAlarm, e_SensorObservation
from leaflet.forms.widgets import LeafletWidget
from django import forms
from .filters import SensorFilter
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView


def SensorListView(request):
    sensor_list = e_Sensor.objects.all()
    sensor_filter = SensorFilter(request.GET, queryset=sensor_list)
    return render(request, 'sensors/e_Sensor_list.html', {'filter': sensor_filter})

class SensorDetailView(DetailView):
    model = e_Sensor
    context_object_name = 'Sensor'
    template_name = 'sensors/e_Sensor_detail.html'

class SensorForm(forms.ModelForm):
    class Meta:
        model = e_Sensor
        fields = ['Name', 'type', 'modalityType', 'geom']
        widgets = {'geom': LeafletWidget()}

class SensorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Sensor
    form_class = SensorForm
    success_url = 'sensor-list'

    def test_func(self):
        if self.request.user.has_perm('can_update_sensors'):
            return True
        else:
            return False

    #only checking if he has permission to update sensors

class SensorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_Sensor
    context_object_name = 'Sensor'
    template_name = 'sensors/e_Sensor_confirm_delete.html'
    success_url = 'sensor_list'

    def test_func(self):
        if self.request.user.has_perm('can_delete_sensors'):
            return True
        else:
            return False

