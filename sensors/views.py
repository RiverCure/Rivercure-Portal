import xlrd, datetime
from datetime import time, date
from django.shortcuts import get_object_or_404, redirect, render
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
from .forms import SensorObservationsFileForm, SensorForm, SensorFileForm, GeoSensorForm
from django.contrib.gis.geos import Point
from django.http import HttpResponse, HttpResponseRedirect
from organization.models import Membership, Organization
from sensors.forms import SensorObservationForm
from django.contrib import messages
from django.db import IntegrityError

def sensor_general_create_permission_check(user):
    return Membership.objects.filter(user=user, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager')).exists()
# To view is enough to be in the organization
def sensor_view_permission_check(user, sensor):
    return sensor.isPublic or Membership.objects.filter(user=user, organization=sensor.organization, access_granted=True).exists()

def sensor_edit_permission_check(user, sensor):
    return Membership.objects.filter(user=user, organization=sensor.organization, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager')).exists()

class SensorObservationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/e_SensorObservation_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hasPerm"] = sensor_edit_permission_check(self.request.user, self.get_object().sensor)
        return context

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_view_permission_check(self.request.user, self.get_object().sensor)
        

class SensorObservationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = SensorObservationForm
    model = e_SensorObservation
    template_name = 'sensors/e_sensorobservation_form.html'
    context_object_name = 'observation'

    def get_success_url(self):
        return reverse('sensor-observation-list',args=(self.kwargs['pk'],))

    def form_valid(self, form):
        observation = form.save(commit=False)
        observation.sensor = e_Sensor.objects.get(pk=self.kwargs['pk'])
        observation.save()
        return super().form_valid(form)

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_general_create_permission_check(self.request.user)

class SensorObservationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = SensorObservationForm
    model = e_SensorObservation
    context_object_name = 'observation'

    def get_success_url(self):
        return reverse('sensor-observation-detail',args=(self.object.sensor.code,self.object.id,))

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_edit_permission_check(self.request.user, self.get_object().sensor)


class SensorObservationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = e_SensorObservation
    context_object_name = 'observation'
    template_name = 'sensors/e_SensorObservation_confirm_delete.html'

    def get_success_url(self):
        return reverse('sensor-observation-list',args=(self.object.sensor.code,))
    
    def test_func(self):
        # We only want the sensors that are either public or are private and this user is the responsible user
        return sensor_edit_permission_check(self.request.user, self.get_object().sensor)


def SensorObservationListView(request, pk):
    sensor_code = pk
    sensor = e_Sensor.objects.get(code=sensor_code)

    if not sensor_view_permission_check(request.user, sensor):
        return HttpResponse('Unauthorized', status=401)
    
    qs = e_SensorObservation.objects.filter(sensor=sensor_code)

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

    hasPerm = sensor_edit_permission_check(request.user, sensor)

    context= {
        'obs': obs,
        'filter' : obs_filter,
        'page_obj' : page_obj,
        'sensor': sensor,
        'hasPerm': hasPerm,
        'form': SensorObservationsFileForm()
    }

    return render(request, "sensors/e_Sensor_observations.html", context)

class SensorListView(LoginRequiredMixin, ListView):
    model = e_Sensor
    context_object_name = 'sensor'
    template_name = 'sensors/e_Sensor_list.html'
    paginate_by = 15
    ordering = ['code']

    def get_queryset(self):
        # Public sensors + Private sensors where the current user is member of the organization
        queryset = (e_Sensor.objects.filter(isPublic=True) | e_Sensor.objects.filter(isPublic=False, organization__membership__in=Membership.objects.filter(user=self.request.user, access_granted=True))).distinct()
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
    model = e_Sensor
    context_object_name = 'sensor'
    template_name = 'sensors/e_Sensor_detail.html'

    def test_func(self):
        # We only want the sensors that are either public or are private and this user is in the organization
        sensor = self.get_object()
        return sensor.isPublic or sensor_view_permission_check(self.request.user, sensor)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SensorObservationsFileForm()
        context["hasPerm"] = sensor_edit_permission_check(self.request.user, self.get_object())
        return context
    
class SensorCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_Sensor
    form_class = SensorForm

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
    model = e_Sensor
    form_class = GeoSensorForm
    object_name = 'sensor'

    def get_success_url(self):
        return reverse('sensor-list')
    
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.geom = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        obj.save()
        return super().form_valid(form)

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object())

class SensorUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_Sensor
    form_class = SensorForm

    def get_form_kwargs(self):
        kwargs = super(SensorUpdateView, self).get_form_kwargs()
        kwargs.update({'user_id': self.request.user.id})
        return kwargs
    
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.geom = Point(form.cleaned_data["lng"], form.cleaned_data["lat"])
        obj.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object())

class SensorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_Sensor
    context_object_name = 'Sensor'
    template_name = 'sensors/e_Sensor_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('sensor-list')

    def test_func(self):
        return sensor_edit_permission_check(self.request.user, self.get_object())

def sensor_observations_upload(request, pk):
    if request.method == 'POST':
        form = SensorObservationsFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file'].read()
            try:
                print(request.FILES['excel_file'])
                handle_uploaded_observations_file(f)
                messages.success(request, 'Observations uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing observation\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing observation\'s Excel file: {error}')

            return redirect('sensor-observation-list', pk=pk)

    return redirect('sensor-observation-list', pk=pk)

def sensor_upload(request):
    if request.method == 'POST':
        form = SensorFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['excel_file'].read()
            # Sensors
            try:
                handle_uploaded_sensors_file(f)
                messages.success(request, 'Sensors uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing sensor\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing sensor\'s Excel file: {error}')
            # Observations
            try:
                handle_uploaded_observations_file(f)
                messages.success(request, 'Observations uploaded successfully')
            except Exception as error:
                if hasattr(error, 'message'):
                    messages.error(request, f'Error parsing observation\'s Excel file: {error.message}')
                else:
                    messages.error(request, f'Error parsing observation\'s Excel file: {error}')


            return HttpResponseRedirect('/sensors/')

    return HttpResponseRedirect('/sensors/')

def handle_uploaded_observations_file(file):
    sensors_file = xlrd.open_workbook(file_contents=file)
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
        try:
            observation.save()
            print('Observation saved!')
        except Exception as error:
            if type(error) is not IntegrityError: # if it isn't an error of duplicate entry in database, raise it
                raise Exception(error)
                return



def handle_uploaded_sensors_file(file):
    sensors_file = xlrd.open_workbook(file_contents=file)
    sensors_sheet = sensors_file.sheet_by_index(0)
    
    for i in range(6, sensors_sheet.nrows):
        if(sensors_sheet.cell_value == ''):
            break

        sensor = e_Sensor()

        check_float = isinstance(sensors_sheet.cell_value(i,0), float)
        if check_float:
            if int(sensors_sheet.cell_value(i,0)) == sensors_sheet.cell_value(i,0):
                sensor_code = str(int(sensors_sheet.cell_value(i,0)))
            else:
                sensor_code = str(sensors_sheet.cell_value(i,0))
        
        else:
            sensor_code = str(sensors_sheet.cell_value(i,0))

        sensor.code = sensor_code
        sensor.Name = sensors_sheet.cell_value(i,1)
        try:
            sensor.organization = Organization.objects.get(name=sensors_sheet.cell_value(i,2))
        except:
            raise Exception('That organization doesn\'t exist')
            return

        sensor.type = sensors_sheet.cell_value(i,3)
        sensor.modalityType = sensors_sheet.cell_value(i,4)
        sensor.description = sensors_sheet.cell_value(i,5)

        if sensors_sheet.cell_value(i,6) == '': sensor.version = None
        else: sensor.version = sensors_sheet.cell_value(i,6)
        
        if sensors_sheet.cell_value(i,7) == '': sensor.responsibleUser = None 
        else: sensor.responsibleUser = sensors_sheet.cell_value(i,7)
        
        sensor.timeZoneAbbreviation = 'GMT'
        sensor.timeZoneOffset = 1

        if sensors_sheet.cell_value(i,10) == '': srid = 3763
        else: srid = int(sensors_sheet.cell_value(i,10))

        coord_str = sensors_sheet.cell_value(i,11)
        coords = coord_str.split(',')

        sensor.geom = Point(float(coords[0]), float(coords[1]), srid=srid)

        sensor.save()
        print('Sensor saved!')