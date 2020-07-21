from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import e_Sensor, e_SensorAlarm, e_SensorObservation
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from leaflet.forms.widgets import LeafletWidget
from django import forms

class SensorListView(ListView):
    model = e_Sensor
    template_name = 'sensors/e_Sensor_list.html'
    context_object_name = 'sensors'
    ordering = ['Name']

