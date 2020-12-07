import xlrd, datetime
from datetime import time, date
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import e_Sensor, e_SensorAlarm, e_SensorObservation
from leaflet.forms.widgets import LeafletWidget
from django import forms
from .filters import SensorFilter, ObservationFilter
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.db.models import Q
from context.models import e_ContextSensor, e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.urls  import reverse, reverse_lazy
from django.core.files.storage import FileSystemStorage
from .forms import SensorObservationsFileForm, SensorForm, SensorFileForm
from django.contrib.gis.geos import Point
from django.http import HttpResponseRedirect

class SensorObservationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/e_SensorObservation_detail.html'

    def test_func(self):
        if  self.request.user.has_perm('sensors.view_e_sensorobservation'):
            return True
        else:
            return False

class SensorObservationForm(forms.ModelForm):
    class Meta:
        model = e_SensorObservation
        fields = ['date','time','depth','discharge',]
        

class SensorObservationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = SensorObservationForm
    model = e_SensorObservation
    template_name = 'sensors/e_sensorobservation_form.html'
    context_object_name = 'observation'

    def get_success_url(self):
        return reverse('sensor-observation-detail',args=(self.object.id,))
   
    def test_func(self):
        if self.request.user.groups.filter(name='SensorManager').exists():
            return True
        else:
            return False

class SensorObservationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = SensorObservationForm
    model = e_SensorObservation
    context_object_name = 'observation'
   
    def get_success_url(self):
        return reverse('sensor-observation-detail',args=(self.object.id,))


    def test_func(self):
        if self.request.user.groups.filter(name='SensorManager').exists():
            return True
        else:
            return False

    #def get_success_url(self):
          # if you are passing 'pk' from 'urls' to 'DeleteView' for company
          # capture that 'pk' as companyid and pass it to 'reverse_lazy()' function
          #observationid=self.kwargs['pk']
          #return reverse_lazy('sensor-observation-detail', kwargs={'pk': companyid})


class SensorObservationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_SensorObservation
    context_object_name = 'observation'
    success_url = reverse_lazy('sensor-list') #to fix
    template_name = 'sensors/e_SensorObservation_confirm_delete.html'
    
    def test_func(self):
        if self.request.user.groups.filter(name='SensorManager').exists():
            return True
        else:
            return False



@permission_required('sensors.view_e_sensorobservation', raise_exception=True)
def SensorObservationListView(request):
    
    qs = e_SensorObservation.objects.filter(sensor=request.GET.get('sensor'))

    sensor_name = e_Sensor.objects.get(code=request.GET.get('sensor'))

    obs_filter = ObservationFilter(request.GET, queryset=qs)
    obs = obs_filter.qs
   
    page = request.GET.get('page', 1)
    obs_paginator = Paginator(obs, 30)

    page_obj = obs_paginator.get_page(page)

    try:
       obs = obs_paginator.page(page)
    except EmptyPage :
       obs = obs_paginator.page(page)
    except PageNotAnInteger:
       obs = obs_paginator.page(page)


    
    context={
        'obs': obs,
        'filter' : obs_filter,
        'page_obj' : page_obj,
        'sensor_name' : sensor_name,
        'sensor_code': request.GET.get('sensor'),
        'form': SensorObservationsFileForm(),
        
    }

    return render(request, "sensors/e_Sensor_observations.html", context)



# @permission_required('sensors.view_e_sensor_observation', raise_exception=True)
# def SensorObservationListView(request):
#     qs = e_SensorObservation.objects.all()
#     obs_filter = ObservationFilter(request.GET, queryset=qs)
    
#     obs = obs_filter.qs
   
#     page = request.GET.get('page', 1)
#     obs_paginator = Paginator(obs, 15)

#     page_obj = obs_paginator.get_page(page)

#     try:
#        obs = obs_paginator.page(page)
#     except EmptyPage :
#        obs = obs_paginator.page(page)
#     except PageNotAnInteger:
#        obs = obs_paginator.page(page)
    
#     context={
#         'obs': obs,
#         'filter' : obs_filter,
#         'page_obj' : page_obj
        
#     }

#     return render(request, "sensors/e_Sensor_observations.html", context)


@permission_required('sensors.view_e_sensor', raise_exception=True)
def SensorListView(request):
    
    sensor_list = e_Sensor.objects.all()
    sensor_filter = SensorFilter(request.GET, queryset=sensor_list)
    context ={
        'filter': sensor_filter,
        'form': SensorFileForm(),
        
    }

    return render(request, 'sensors/e_Sensor_list.html', context)


class SensorDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_Sensor
    context_object_name = 'sensor'
    template_name = 'sensors/e_Sensor_detail.html'

    def test_func(self):
        if self.request.user.has_perm('sensors.view_e_sensor'):
            return True
        else:
            return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SensorObservationsFileForm()
        return context
    

class SensorCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_Sensor
    form_class = SensorForm

    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        if self.request.user.groups.filter(name='SensorManager').exists():
            return True
        else:
            return False

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.geom = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        obj.save()
        return super().form_valid(form)
            
class SensorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Sensor
    form_class = SensorForm
    

    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        if self.request.user.has_perm('sensors.change_e_sensor'):
            return True
        else:
            return False

class SensorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_Sensor
    context_object_name = 'Sensor'
    template_name = 'sensors/e_Sensor_confirm_delete.html'
    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        if self.request.user.has_perm('sensors.delete_e_sensor'):
            return True
        else:
            return False

def sensor_observations_upload(request):
    if request.method == 'POST':
        form = SensorObservationsFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_observations_file(request.FILES['excel_file'])
            return HttpResponseRedirect('/sensors/')

    return HttpResponseRedirect('/sensors/')

def sensor_upload(request):
    if request.method == 'POST':
        form = SensorFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_sensors_file(request.FILES['excel_file'])
            return HttpResponseRedirect('/sensors/')

    return HttpResponseRedirect('/sensors/')

def handle_uploaded_observations_file(file):
    sensors_file = xlrd.open_workbook(file_contents=file.read())
    observation_sheet = sensors_file.sheet_by_index(1)
    
    for i in range(6, observation_sheet.nrows):
        if(observation_sheet.cell_value(i,0) == ''):
            break
        
        observation = e_SensorObservation()

        check_float = isinstance(observation_sheet.cell_value(i,0), float)
        if check_float:
            print(observation_sheet.cell_value(i,0))
            if int(observation_sheet.cell_value(i,0)) == observation_sheet.cell_value(i,0):
                sensor_code = str(int(observation_sheet.cell_value(i,0)))
                observation.sensor = e_Sensor.objects.filter(code=sensor_code).first()
            else:
                sensor_code = str(observation_sheet.cell_value(i,0))
                observation.sensor = e_Sensor.objects.filter(code=sensor_code).first()
                print("float")
        
        else:
            sensor_code = str(observation_sheet.cell_value(i,0))
            observation.sensor = e_Sensor.objects.filter(code=sensor_code).first()
        
        observation.sensorType = 'HydrometricSensor'
        
        raw_time = observation_sheet.cell_value(i,2) #time - float
        converted_time = xlrd.xldate_as_tuple(raw_time,  sensors_file.datemode)
        time_value = time(*converted_time[3:])
        observation.time = time_value

        raw_date = observation_sheet.cell_value(i,1)
        converted_date = xlrd.xldate_as_tuple(raw_date, sensors_file.datemode)
        observation.date = datetime.datetime(*converted_date)

        if observation_sheet.cell_value(i,3) == '': 
            observation.depth = None
        else: 
            observation.depth = observation_sheet.cell_value(i,3)

        if observation_sheet.cell_value(i,4) == '': 
            observation.discharge = None
        else: 
            observation.discharge = observation_sheet.cell_value(i,4)

        observation.save()
        print('Observation saved!')


def handle_uploaded_sensors_file(file):
    sensors_file = xlrd.open_workbook(file_contents=file.read())
    sensors_sheet = sensors_file.sheet_by_index(0)
    
    for i in range(6, sensors_sheet.nrows):
        if(sensors_sheet.cell_value == ''):
            break

        sensor = e_Sensor()

        check_float = isinstance(sensors_sheet.cell_value(i,1), float)
        if check_float:
            if int(sensors_sheet.cell_value(i,1)) == sensors_sheet.cell_value(i,1):
                sensor_code = str(int(sensors_sheet.cell_value(i,1)))
                print("int")
            else:
                sensor_code = str(sensors_sheet.cell_value(i,1))
                print("float")
        
        else:
            sensor_code = str(sensors_sheet.cell_value(i,1))

        sensor.code = sensor_code
        sensor.Name = sensors_sheet.cell_value(i,2)
        sensor.type = sensors_sheet.cell_value(i,3)
        sensor.modalityType = sensors_sheet.cell_value(i,4)
        sensor.description = sensors_sheet.cell_value(i,5)

        if sensors_sheet.cell_value(i,6) == '': sensor.version = None
        else: sensor.version = sensors_sheet.cell_value(i,6)
        
        if sensors_sheet.cell_value(i,7) == '': sensor.responsibleUser = None 
        else: sensor.responsibleUser = sensors_sheet.cell_value(i,7)
        
        sensor.timeZoneAbbreviation = 'GMT'
        sensor.timeZoneOffset = 1
    
        srid = int(sensors_sheet.cell_value(i,10))
        coord_str = sensors_sheet.cell_value(i,11)
        coords = coord_str.split(',')

        sensor.geom = Point(float(coords[0]), float(coords[1]), srid=srid)

        sensor.save()
        print('Sensor saved!')