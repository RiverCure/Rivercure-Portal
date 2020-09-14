from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import e_Sensor, e_SensorAlarm, e_SensorObservation
from leaflet.forms.widgets import LeafletWidget
from django import forms
from .filters import SensorFilter
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from context.models import e_ContextSensor, e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint

class SensorObservationDetailView(DetailView):
    model = e_SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/e_SensorObservation_detail.html'


def SensorObservationListView(request):
    qs = e_SensorObservation.objects.all()
    sensor_contains_query = request.GET.get('query')
    
    if sensor_contains_query !='' and sensor_contains_query is not None:
        qs = qs.filter(Q(sensorType__icontains=sensor_contains_query) | Q(sensor__Name__icontains=sensor_contains_query))
    
    context={
        'queryset': qs
    }

    return render(request, "sensors/e_Sensor_observations.html", context)



def SensorListView(request):
    
    sensor_list = e_Sensor.objects.all()
    sensor_filter = SensorFilter(request.GET, queryset=sensor_list)

    #complex_query=''

    #filter_code = '55'

    #if complex_query is not None:
        #complex_query = e_ContextSensor.objects.all().filter(code__iexact=filter_code).boundary_point.contextBoundaryLine.context
      

    context ={
        'filter': sensor_filter,
    }

    return render(request, 'sensors/e_Sensor_list.html', context)

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

