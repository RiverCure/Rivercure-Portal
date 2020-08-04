from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import e_Sensor, e_SensorAlarm, e_SensorObservation
from leaflet.forms.widgets import LeafletWidget
from django import forms
from .filters import SensorFilter


def SensorListView(request):
    sensor_list = e_Sensor.objects.all()
    sensor_filter = SensorFilter(request.GET, queryset=sensor_list)
    return render(request, 'sensors/e_Sensor_list.html', {'filter': sensor_filter})

#class HydroFeatureDetailView(DetailView):
    #model = e_HydroFeature
    #context_object_name = 'Hydrofeatures'
    #template_name = 'rivercureportal/e_HydroFeature_detail.html'