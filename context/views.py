import json, os, geojson, tempfile, datetime, requests
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import transaction, connection
from django.utils import timezone
from .forms import ContextForm, UploadContextForm, EventForm
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context, e_ContextDTM, e_ContextDTMFile, e_ContextFrictionCoeff, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextEvent, e_ContextSensor, e_ContextEventResult
from raster.models import RasterLayer
from sensors.models import e_Sensor, e_SensorObservation
from rest_framework import viewsets
from django.core.serializers import serialize
from .serializers import ContextSerializer
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry, Point, fromfile
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .filters import EventFilter, ContextFilter, ContextSensorFilter
from django.contrib.gis.gdal import SpatialReference, CoordTransform, GDALRaster
from io import BytesIO, StringIO
from zipfile import ZipFile
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from pprint import pprint
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse_lazy
from context.forms import ContextDetailsForm
from organization.models import Membership, Organization
from .tasks import post_files
from notifications.signals import notify

# Checks if the user is a manager or contextManager on any organization. If so, he can add contexts (from which organization is seen in the create view)
def context_general_create_permission_check(user):
    try:
        return Membership.objects.filter(user=user, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager')).exists()
    except:
        return False

def context_general_event_create_permission_check(user):
    try:
        return Membership.objects.filter(user=user, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager') | Q(permission='org_eventManager')).exists()
    except:
        return False

# Checks if the user is a manager or contextManager of an organization
def context_organization_edit_permission_check(user, organization):
    try:
        return Membership.objects.filter(user=user, organization=organization, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager')).exists()
    except:
        return False

# Checks if the user is a manager or eventManager of an organization
def context_organization_event_permission_check(user, organization):
    try:
        return Membership.objects.filter(user=user, organization=organization, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager') | Q(permission='org_eventManager')).exists()
    except:
        return False

def belongs_to_organization(user, organization):
    try:
        return Membership.objects.filter(user=user, organization=organization, access_granted=True).exists()
    except:
        return False

class ContextDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView ):
    model = e_Context
    context_object_name = 'context'
    template_name = 'context/e_context_confirm_delete.html'
    success_url = reverse_lazy('context-list')

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, self.get_object().organization)

class ContextUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView ):
    model = e_Context
    form_class = ContextDetailsForm
    context_object_name = 'context'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['current_view'] = 'edit'
        return context
    
    def get_success_url(self):
        return reverse('context-detail',args=(self.object.code,))

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, self.get_object().organization)

@login_required
def ContextListView(request):
    
    organizations = Organization.objects.filter(membership__in=Membership.objects.filter(user=request.user, access_granted=True))
    context_list = e_Context.objects.filter(organization__in=organizations)

    context_filter = ContextFilter(request.GET, queryset=context_list, organizations=organizations)

    # Needs to have permission to add in, at least, one organization. The choice list in add form is then filtered to the ones he is actually capable of adding
    permission_to_add = context_general_create_permission_check(request.user)

    context = {
        'permission_to_add': permission_to_add,
        'filter' : context_filter
    }

    return render(request, 'context/e_Context_list.html', context)

@login_required
def OtherContextListView(request):
    # Exclude (the contexts) with organizations the user is in
    other_context_list = e_Context.objects.exclude(organization__in=Organization.objects.filter(members=request.user)).exclude(isPublic=False)
    other_context_filter = ContextFilter(request.GET, queryset=other_context_list, organizations=Organization.objects.exclude(members=request.user))

    context = {
        'context_list': other_context_list,
        'filter': other_context_filter
    }
    return render(request, 'context/e_OtherContext_list.html', context)


class ContextInitialForm(forms.ModelForm):
    class Meta:
        model = e_Context
        fields = ['code','Name', 'hydroFeature', 'organization', 'isPublic',]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super(ContextInitialForm, self).__init__(*args, **kwargs)
        # We only want to allow to choose options where the user is org_manager or org_contextManager of the organization
        memberships = Membership.objects.filter(user_id=user_id, access_granted=True, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager'))
        self.fields['organization'].queryset = Organization.objects.filter(membership__in=memberships)
    

class ContextCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = e_Context
    form_class = ContextInitialForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_view'] = 'create'
        return context

    def get_form_kwargs(self):
        kwargs = super(ContextCreateView, self).get_form_kwargs()
        kwargs.update({'user_id': self.request.user.id})
        return kwargs

    def form_valid(self, form):
        currentTime = datetime.datetime.now()
        organization = form.save(commit=False)
        # Add metadata to organization
        organization.creator = self.request.user
        organization.create_date = currentTime
        organization.save()

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('context-list')

    def test_func(self):
        return context_general_create_permission_check(self.request.user)

class ContextDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = e_Context
    context_object_name = 'context'
    template_name = 'context/e_Context_detail.html'

    def test_func(self, *args , **kwargs):
        context = self.get_object()
        return context.isPublic or Membership.objects.filter(user=self.request.user, organization=context.organization).exists()

    def get_context_data(self, **kwargs):
        user = self.request.user
        organization = self.get_object().organization

        web_host = os.environ['CONTEXT_API']
        context = super().get_context_data(**kwargs)
        context['api'] = f'http://{web_host}/contexts/api/context/'
        context['sensors'] = get_context_sensors(self.get_object().pk)
        context['form'] = UploadContextForm()
        context['canEdit'] = context_organization_edit_permission_check(user, organization)

        return context

@login_required
def ContextSensorListView(request, context_code):
    context = get_object_or_404(e_Context, code=context_code)
    
    if not( context.isPublic or belongs_to_organization(request.user, context.organization)):
        return HttpResponseRedirect(reverse('context-detail', kwargs={'pk': context.code}))
    
    context_sensor_list = e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context__code=context.code).distinct('sensor')

    context_sensor_filter = ContextSensorFilter(request.GET, queryset=context_sensor_list)
    
    context= {
        'filter' :  context_sensor_filter,
        'context': context
    }

    return render(request, 'context/e_ContextSensor_list.html', context )

class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = e_ContextEvent
    template_name = 'context/e_Event_create.html'
    form_class = EventForm
    pk_url_kwarg = 'event_id'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = get_object_or_404(e_Context, pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse('context-event-list',args=(self.get_object().context.code, ))

    def test_func(self):
        return context_organization_event_permission_check(self.request.user, self.get_object().context.organization)

class EventCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_ContextEvent
    template_name = 'context/e_Event_create.html'
    form_class = EventForm
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['context'] = get_object_or_404(e_Context, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        context = e_Context.objects.get(code=form.cleaned_data['context_code'])
        writing_period = form.cleaned_data['WritingPeriodicity']
        max_update_period = form.cleaned_data['UpdateMaximumValue']
        writing_unit = form.cleaned_data['WritingPeriodicityUnit']
        update_unit = form.cleaned_data['UpdateMaximumValueUnit']
        init_date = form.cleaned_data['startDate']
        end_date = form.cleaned_data['endDate']
        init_time = form.cleaned_data['startTime']
        end_time = form.cleaned_data['endTime']
        
        obj = form.save(commit=False)
        obj.context = context
        obj.save() 

        return HttpResponseRedirect(reverse('event-detail',args=(context.code, obj.id,)))

    def test_func(self):
        organization = e_Context.objects.get(pk=self.kwargs['pk']).organization
        return context_organization_event_permission_check(self.request.user, organization)


def runsimulationview(request, pk, event_id):
    event = get_object_or_404(e_ContextEvent, id=event_id)
    if not context_organization_event_permission_check(request.user, event.context.organization):
        return HttpResponseRedirect(reverse('event-detail', args=(pk, event_id, )))
    
    try:
        r = request_simulation(event.context, event.id, event.WritingPeriodicity, event.UpdateMaximumValue, event.WritingPeriodicityUnit, 
        event.UpdateMaximumValueUnit, event.startDate, event.endDate, event.startTime, event.endTime)
        if r.text == 'success':
            messages.success(request,f'Simulation request successful') 
        else:
            messages.warning(request,f'Simulation request failed') 
    except Exception as e:
        print(f'Failed simulation request!\nException: {e}')
        messages.warning(request,f'Simulation request failed') 
    
    print("RUN SIMULATION")
    return HttpResponseRedirect(reverse('event-detail', args=(pk, event.id,)))


def ContextEventListView(request, context_code):
    context = get_object_or_404(e_Context, pk=context_code)

    if not (context.isPublic or belongs_to_organization(request.user, context.organization)):
        return HttpResponse('Unauthorized', status=401)

    qs = e_ContextEvent.objects.filter(context=context)
    
    event_filter = EventFilter(request.GET, queryset=qs)
    events_list = event_filter.qs
    
    context = {
        'events': events_list,
        'filter': event_filter,
        'context': e_Context.objects.get(code=context_code),
        'hasPerm': context_organization_event_permission_check(request.user, context.organization)
    }
    return render(request, 'context/e_Event_list.html', context)

# class EventDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
class EventDetailView(LoginRequiredMixin, DetailView):
    model = e_ContextEvent
    context_object_name = 'event'
    pk_url_kwarg = 'event_id'
    template_name = 'context/e_Event_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context['hasPerm'] = context_organization_event_permission_check(self.request.user, self.get_object().context.organization)
        return context


def get_context_sensors(context_code):
    context_sensors = e_Sensor.objects.filter(isPublic=True, organization__is_active=True)
    context_sensors = context_sensors | e_Sensor.objects.filter(organization=e_Context.objects.get(pk=context_code).organization, organization__is_active=True)
    
    previous_context_sensors = set()
    for elem in e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context=get_object_or_404(e_Context, pk=context_code)):
        previous_context_sensors.add(elem.sensor.pk)
    # Adds previously added sensors (from other organizations that are suspended) to the queryset
    context_sensors = context_sensors | e_Sensor.objects.filter(pk__in=previous_context_sensors)
    return context_sensors

def manage_context(request, context_code):
    web_host = os.environ['CONTEXT_API']

    context = {
        # 'contexts': e_Context.objects.filter(user__username=request.user).order_by('Name'),
        # 'sensors': e_Sensor.objects.filter(isPublic=True) | e_Sensor.objects.filter(organization=e_Context.objects.get(pk=context_code).organization),
        'sensors': get_context_sensors(context_code),
        'form': ContextForm(),
        'api': f'http://{web_host}/contexts/api/context/',
        # 'context': request.GET.get('context_code'),
    }
    if request.method == 'POST':
        if not request.user.is_authenticated: # if user is not authenticated
            return render(request, 'context/context.html', context)
        
        form = ContextForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    e_context = context_creation(form, request.user)
                    e_context.save()

                    # initialize and save refinement
                    refinement_creation(form, e_context)
                    # initialize and save alignment
                    alignment_creation(form, e_context)

                    # initialize and save boundaries & boundary points
                    boundaryline_creation(form, e_context)

                messages.success(request,f'Context updated with success!') 
                
                return HttpResponseRedirect(reverse('context-detail', kwargs={'pk': e_context.code}))
            except Exception as e:
                print(f'Error saving context: {e}')
                messages.warning(request,f'Context update failed')

        else:
            messages.warning(request,f'Context info is not complete') 
    else:
        context['context'] = e_Context.objects.get(code=context_code)

    return render(request, 'context/context.html', context)

#aux functions for manage_context()
def handle_upload_raster(context, raster_file): #function to handle the upload of the raster file
    try:
        dtm = e_ContextDTM.objects.get(context=context) 
        dtm.contextDTM.datatype='co'
        dtm.contextDTM.name = str(dtm)
        dtm.contextDTM.rasterfile = raster_file
    except e_ContextDTM.DoesNotExist:
        dtm = e_ContextDTM()
        dtm.context = context
        raster = RasterLayer()
        raster.datatype='co'
        raster.name = str(dtm)
        raster.rasterfile = raster_file
        raster.save()
        dtm.contextDTM = raster
   
    dtm.save()

def handle_upload_raster_file(context, raster_file):
    dtm = e_ContextDTMFile.objects.get_or_create(context=context)
    file_name = f'{context.Name}_dtm.tif'
    with open(f'media/{file_name}', 'wb+') as destination:
        for chunk in raster_file.chunks():
            destination.write(chunk)
    
    dtm[0].raster = file_name
    dtm[0].save()

def handle_friction_coeff_upload(context, friction_coeff_file): #function to handle the upload of the contour lines file
    friction_coeff = e_ContextFrictionCoeff.objects.get_or_create(context=context)
    file_name = f'{context.Name}_frictionCoef.tif'
    with open(f'media/{file_name}', 'wb+') as destination:
        for chunk in friction_coeff_file.chunks():
            destination.write(chunk)


    friction_coeff[0].raster = friction_coeff_file
    friction_coeff[0].save()

def context_creation(form, user): # function to initialize and save the context given a form and the user that submited the form
    context = e_Context.objects.get(pk=form.cleaned_data['code']) # get the model from the database
    organization_members = Organization.objects.get(pk=context.organization.id).members.all()

    if user not in organization_members: # if user doesn't own the context
        print('User that doesn\'t own the context tried to change it!')
        return None
                
    context.geomExternalBoundary = MultiPolygon(Polygon(json.loads(form.cleaned_data['domain'])['geometry']['coordinates'][0]))
    context.CLExternalBoundary = json.loads(form.cleaned_data['domain'])['properties']['CL']
    context.hasMesh = False
    return context

def refinement_creation(form, context):
    e_ContextRefinement.objects.filter(context=context).delete()
    for feature in json.loads(form.cleaned_data['refinement'])['features']:
        refinement = e_ContextRefinement()
        refinement.context = context
        refinement.CL = feature['properties']['CL']
        refinement.geom = Polygon(feature['geometry']['coordinates'][0])
        refinement.save()

def alignment_creation(form, context):
    e_ContextAlignment.objects.filter(context=context).delete()
    for feature in json.loads(form.cleaned_data['alignment'])['features']:
        alignment = e_ContextAlignment()
        alignment.context = context
        alignment.CL = feature['properties']['CL']
        alignment.geom = LineString(feature['geometry']['coordinates'])
        alignment.save()

def boundaryline_creation(form, context): # function to create the several lines
    e_ContextBoundaryLine.objects.filter(context=context).delete()
    e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context=context).delete()
    boundary_points = json.loads(form.cleaned_data['boundary_points'])['features']
    for feature in json.loads(form.cleaned_data['boundaries'])['features']:
        boundary = e_ContextBoundaryLine()
        boundary.context = context
        boundary.geom = LineString(feature['geometry']['coordinates'])
        boundary.type = feature['properties']['type']
        boundary.dataType = feature['properties']['dataType']
        boundary.save()
        
        # Save the points on the boundary line
        for point in boundary_points:
            if(point['properties']['boundaryLineId'] == feature['properties']['id']):
                boundary_point = e_ContextBoundaryPoint()
                boundary_point.contextBoundaryLine = boundary
                boundary_point.geom = Point(point['geometry']['coordinates'])
                boundary_point.save()
                
                # Handle sensors on point
                for sensor in point['properties']['sensors']:
                    boundary_point_sensor = e_ContextSensor()
                    boundary_point_sensor.associateDatetime = timezone.now()
                    boundary_point_sensor.sensor = e_Sensor.objects.get(code=sensor)
                    boundary_point_sensor.boundary_point = boundary_point
                    boundary_point_sensor.save()
                
#end of aux functions for manage_context()

class ContextViewSet(viewsets.ModelViewSet):
    queryset = e_Context.objects.all()
    lookup_field = 'code'
    serializer_class = ContextSerializer

  
class UploadContext(LoginRequiredMixin, UserPassesTestMixin, FormView):
    http_method_names = ['post']
    template_name = 'context/context_upload.html'
    form_class = UploadContextForm

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, get_object_or_404(e_Context, pk=self.kwargs['pk']).organization)

    def form_valid(self, form):
        message = ''
        try:
            with transaction.atomic():
                context = e_Context.objects.get(code=form.cleaned_data['code'])
                try:
                    if form.cleaned_data['domain'] is not None:
                        handle_domain(form.cleaned_data['domain'], context, self.request.user)
                    
                    #Mark edited context for mesh regeneration need
                    context.hasMesh = False
                    context.save()
                except Exception as e:
                    message = 'Error in Domain definition'
                    raise Exception(e)

                try:
                    if form.cleaned_data['alignments'] is not None:
                        handle_alignment(form.cleaned_data['alignments'], context)
                except Exception as e:
                    message = 'Error in Alignment definition'
                    raise Exception(e)
                try:
                    if form.cleaned_data['refinements'] is not None:
                        handle_refinement(form.cleaned_data['refinements'], context)
                except Exception as e:
                    message = 'Error in Refinement definition'
                    raise Exception(e)
                try:
                    if form.cleaned_data['boundaries'] is not None:
                        handle_boundaries(form.cleaned_data['boundaries'], context)
                except Exception as e:
                    message = 'Error in Boundary definition'
                    raise Exception(e)

                #Save dtm from raster file field
                try:
                    dtm = self.request.FILES.get('dtm_file')
                    if dtm is not None:
                        # handle_upload_raster(context, dtm)
                        handle_upload_raster_file(context, dtm)
                except Exception as e:
                    message = 'Error in DTM definition'
                    raise Exception(e)
                #Save contour lines from file
                
                try:
                    friction_coeff = self.request.FILES.get('friction_coefficient_file')
                    if friction_coeff is not None:
                        handle_friction_coeff_upload(context, friction_coeff)
                except Exception as e:
                    message = 'Error in Friction coefficient definition'
                    raise Exception(e)

                messages.success(self.request, 'Context Uploaded')
        except Exception as e:
            print(f'Error loading the files:\n{e}')
            messages.warning(self.request, f'Context Upload Failed. Detail: {message}') 

        
        return super().form_valid(form)

    def get_success_url(self):
        action = self.request.GET.get('value')
        if action == "finished":
            return reverse('context-detail', args=[self.kwargs['pk']])
        elif action == "continue":
            return reverse('context_manage', args=[self.kwargs['pk']])
        else:
            return reverse('context-detail', args=[self.kwargs['pk']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = e_Context.objects.get(code=self.kwargs['pk'])
        return context
    
def handle_domain(f, context, user): #handle the loading of domain from a geojson
    domain_features = json.load(f)
    try:
        srid = SpatialReference(domain_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    # context.Name = str.title(domain_features['name'].split('_')[0]) # might cause problems
    # context.hydroFeature = None
    context.CLExternalBoundary = domain_features['features'][0]['properties']['CL']
    try:
        domain_geom = MultiPolygon(Polygon(domain_features['features'][0]['geometry']['coordinates'][0][0], srid=srid), srid=srid)
    except:
        print('Domain geojson doesn\'t contain a MultiPolygon\nTrying simple Polygon')
        domain_geom = MultiPolygon(Polygon(domain_features['features'][0]['geometry']['coordinates'][0], srid=srid), srid=srid)
    context.geomExternalBoundary = domain_geom
    # context.geomExternalBoundary.transform(SpatialReference(4326))
    # context.user = user

    context.save()
    
def handle_alignment(f, context): #handle the loading of alignment from a geojson
    alignment_features = json.load(f)
    e_ContextAlignment.objects.filter(context=context).delete()
    try:
        srid = SpatialReference(alignment_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    for feature in alignment_features['features']:
        alignment = e_ContextAlignment()
        alignment.context = context
        alignment.CL = feature['properties']['CL']
        try:
            alignment.geom = LineString(feature['geometry']['coordinates'][0], srid=srid)
        except:
            print('Alignment geojson doesn\'t contain a MultiLineString\nTrying simple LineString')
            alignment.geom = LineString(feature['geometry']['coordinates'], srid=srid)
        alignment.save()

def handle_refinement(f, context): #handle the loading of refinement from a geojson
    e_ContextRefinement.objects.filter(context=context).delete()
    refinement_features = json.load(f)
    try:
        srid = SpatialReference(refinement_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    for feature in refinement_features['features']:
        refinement = e_ContextRefinement()
        refinement.context = context
        refinement.CL = feature['properties']['CL']
        try:
            refinement.geom = Polygon(feature['geometry']['coordinates'][0][0], srid=srid)
        except:
            print('Refinement geojson doesn\'t contain a MultiPolygon\nTrying simple Polygon')
            refinement.geom = Polygon(feature['geometry']['coordinates'][0], srid=srid)
        refinement.save()

def handle_boundaries(f, context): #handle the loading of boundaries from a geojson
    # boundary_points = json.load(f_points)['features']
    e_ContextBoundaryLine.objects.filter(context=context).delete()
    e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context=context).delete()
    boundary_features = json.load(f)
    try:
        srid = SpatialReference(boundary_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    for feature in boundary_features['features']:
        boundary = e_ContextBoundaryLine()
        boundary.context = context  
        try:
            boundary.geom = LineString(feature['geometry']['coordinates'][0], srid=srid)
        except:
            print('Boundary geojson doesn\'t contain a MultiLineString\nTrying simple LineString')
            boundary.geom = LineString(feature['geometry']['coordinates'], srid=srid)

        boundary.dataType = feature['properties']['Type']
        # boundary.type = feature['properties']['dataType']
        boundary.save()
        # Save the points on the boundary line
        for point in boundary.geom.coords:
            boundary_point = e_ContextBoundaryPoint()
            boundary_point.contextBoundaryLine = boundary
            boundary_point.geom = Point(point, srid=srid)
            boundary_point.save()
            # if(boundary.geom.intersects(Point(point['geometry']['coordinates'], srid=srid))):
                # boundary_point = e_ContextBoundaryPoint()
                # boundary_point.contextBoundaryLine = boundary
                # boundary_point.geom = Point(point['geometry']['coordinates'], srid=srid)
                # boundary_point.save()

@login_required
def download_context(request, context_code): #function that allows the download of an context
    if not context_organization_edit_permission_check(request.user, e_Context.objects.get(code=context_code).organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    message = None  #Message to send to user in case of failure
    #prepare geojson for download

    #Need to check if context code exists
    try:
        #------------------ Domain --------------------------------
        domain_file = prepare_domain(context_code)
        context_name = domain_file['name']
        #------------------ Alignment --------------------------------
        alignment_file = prepare_alignment(context_code, context_name)
        #------------------ Refinement --------------------------------  
        refinement_file = prepare_refinement(context_code, context_name)
        #------------------ Boundary --------------------------------
        boundary_file = prepare_boundaries(context_code, context_name)
        #------------------ Boundary Points --------------------------------
        boundary_point_file = prepare_boundary_points(context_code, context_name)
        #endof json preparation

        mem_file = BytesIO() #memory where the zip file will be created
        with ZipFile(mem_file, 'w') as zipFolder: #create a zipped folder to return to the user
            zipFolder.writestr(f'{context_name}_domain.geojson', geojson.dumps(domain_file))
            if alignment_file is not None:
                zipFolder.writestr(f'{context_name}_alignments.geojson', geojson.dumps(alignment_file))
            if refinement_file is not None:
                zipFolder.writestr(f'{context_name}_refinements.geojson', geojson.dumps(refinement_file))
            if boundary_file is not None:
                zipFolder.writestr(f'{context_name}_boundaries.geojson', geojson.dumps(boundary_file))
            if boundary_point_file is not None:
                zipFolder.writestr(f'{context_name}_boundaries_points.geojson', geojson.dumps(boundary_point_file))

        mem_file.seek(0)
        response = FileResponse(mem_file, content_type="application/zip")
        response['Content-Disposition'] = f'attachment; filename="{context_name}.zip"'
        return response
    except Exception as e:
        messages.warning(request,f'Context not complete for download') 
        print(f'Error downloading context: {e}')
        return redirect(request.META['HTTP_REFERER'])

#aux functions for download_context
def prepare_domain(context_code):
    with connection.cursor() as cursor:
        cursor.execute('''SELECT ST_AsText(ST_Transform("geomExternalBoundary", 3763)), "Name", "CLExternalBoundary" 
                        FROM public.context_e_context WHERE code= %s''', [context_code])
        row = cursor.fetchone()
        context_domain = GEOSGeometry(row[0])
        context_name = row[1]
        context_CL = row[2]

    context_main = geojson.Feature(geometry= geojson.Polygon(context_domain.coords[0]), #Maybe this should be a simple polygon for pre processor
                        properties = {"Geometry type": 'Domain',
                                    "CL": context_CL})

    features = []
    features.append(context_main)
    domain_file = geojson.FeatureCollection(features)
    domain_file['name'] = context_name
    domain_file['code'] = context_code
    domain_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763"} } # str(context.geomExternalBoundary.srid)

    return domain_file

def prepare_alignment(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute('SELECT ST_AsText(ST_Transform("geom", 3763)), "CL" FROM public.context_e_contextalignment WHERE context_id= %s', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for alignment in rows:
            alignment_geom = GEOSGeometry(alignment[0])
            context_alignment = geojson.Feature(geometry= geojson.LineString(alignment_geom.coords),
                                properties = {"Geometry type": 'Alignment',
                                            "CL": alignment[1]})

            features.append(context_alignment)

    alignment_file = geojson.FeatureCollection(features)
    alignment_file['name'] = context_name + '_alignments'
    alignment_file['Context code'] = context_code
    alignment_file['Context name'] = context_name
    alignment_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

    return alignment_file

def prepare_refinement(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute('''SELECT ST_AsText(ST_Transform("geom", 3763)), "CL" 
                        FROM public.context_e_contextrefinement WHERE context_id= %s''', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for refinement in rows:
            refinement_geom = GEOSGeometry(refinement[0])
            context_refinement = geojson.Feature(geometry= geojson.Polygon(refinement_geom.coords),
                                properties = {"Geometry type": 'Refinement',
                                            "CL": refinement[1]})

            features.append(context_refinement)

    refinement_file = geojson.FeatureCollection(features)
    refinement_file['name'] = context_name + '_refinements'
    refinement_file['Context code'] = context_code
    refinement_file['Context name'] = context_name
    refinement_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

    return refinement_file

def prepare_boundaries(context_code, context_name):
    features = []
    
    with connection.cursor() as cursor:
        cursor.execute('SELECT ST_AsText(ST_Transform("geom", 3763)), "type", "dataType" FROM public.context_e_contextboundaryline WHERE context_id= %s', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for boundary in rows:
            boundary_geom = GEOSGeometry(boundary[0])
            context_boundary = geojson.Feature(geometry= geojson.LineString(boundary_geom.coords),
                                properties = {"Geometry type": 'Boundary Line',
                                            "Type": boundary[1],
                                            "Data type": boundary[2]})

            features.append(context_boundary)

    boundary_file = geojson.FeatureCollection(features)
    boundary_file['name'] = context_name + '_boundaries'
    boundary_file['Context code'] = context_code
    boundary_file['Context name'] = context_name
    boundary_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

    return boundary_file

def prepare_boundary_points(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute('''SELECT ST_AsText(ST_Transform("context_e_contextboundarypoint"."geom", 3763)), "context_e_contextboundaryline"."id", "context_e_contextsensor"."sensor_id", "context_e_contextboundaryline"."dataType"
                            FROM public.context_e_contextboundarypoint 
                            INNER JOIN "context_e_contextboundaryline" 
                            ON ("context_e_contextboundarypoint"."contextBoundaryLine_id" = "context_e_contextboundaryline"."id") 
                            INNER JOIN "context_e_contextsensor" 
                            ON ("context_e_contextboundarypoint"."id" = "context_e_contextsensor"."boundary_point_id") 
                            WHERE "context_e_contextboundaryline"."context_id" = %s''', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for boundary_point in rows:
            boundary_point_geom = GEOSGeometry(boundary_point[0])
            context_boundary_points = geojson.Feature(geometry= geojson.Point(boundary_point_geom.coords),
                                properties = {"Geometry type": 'Boundary Point',
                                            "Boundary": boundary_point[1],
                                            "Series": f'sensor_{boundary_point[2]}.bnd',
                                            "Type": boundary_point[3]}) 

            features.append(context_boundary_points)

    boundary_point_file = geojson.FeatureCollection(features)
    boundary_point_file['name'] = context_name + '_boundary_points'
    boundary_point_file['Context code'] = context_code
    boundary_point_file['Context name'] = context_name
    boundary_point_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

    return boundary_point_file

@login_required
def request_pre_processing(request, context_code):
    context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)
        
    simulator_address = os.environ['SIMULATOR_ADDRESS']
    url = simulator_address + 'process/'

    try:
        r = requests.get(simulator_address) # ping iStav to check if it's online
        result = post_files.delay(url, context_code)
        # Combination hasMesh = False + task_id = val means it's processing
        context.hasMesh = False # Assume there is no mesh generated
        context.task_id = result.task_id
        context.requester = request.user
        context.save()
        messages.success(request, 'Mesh generation request sent')
    except: # iStav not online
        messages.error(request, 'Couldn\'t connect to iStav')

    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('context-detail', pk=context_code)

@login_required
def preprocessing_results(request): # function to redirect the user to the paraviewweb visualizer
    paraviewweb_visualizer_url = 'http://localhost:8090'
    return redirect(paraviewweb_visualizer_url)

@login_required
def download_preprocessing_results(request, context_code): # function to redirect the user to the paraviewweb visualizer
    context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    url = os.environ['SIMULATOR_ADDRESS']
    payload = {'context_name': context.Name}
    request = requests.get(f'{url}pre-processing/results/', params=payload, stream=True)
    print(f'Pre-processing results requested for context {context.Name}')
    response = FileResponse(BytesIO(request.content))
    response['Content-Disposition'] = f'attachment; filename="{context.Name}_mesh.vtk"'

    return response

    # messages.warning(self.request, 'Mesh download failed') 
    # return redirect(reverse('context-detail', kwargs={'pk': context_code}))

    

def request_simulation(context, event_id, writing_perio, max_update_perio, writing_unit, update_unit, init_date, end_date, init_time, end_time): # function to request a simulation for a certain context
    url = os.environ['SIMULATOR_ADDRESS'] + 'simulate/'

    payload = {'context_name': context.Name,
                'event_id': event_id}

    #prepare files

    frequency_file = prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit)
    time_file = prepare_time_file(init_date, end_date, init_time, end_time)
    boundary_file = prepare_boundaries_file(context)

    files = prepare_gauge_file(context, init_date, end_date, init_time, end_time)

    files.append(('frequency', frequency_file))
    files.append(('time', time_file))
    files.append(('boundaries', boundary_file))

    r = requests.post(url, files=files, params=payload)

    return r


def prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit): # prepare output.cnt file for simulation
    # transform periodicity
    if(writing_unit == 'hour'):
        writing_perio *= 60 * 60
    elif(writing_unit == 'minute'):
        writing_perio *= 60

    if(update_unit == 'hour'):
        max_update_perio *= 60 * 60
    elif(update_unit == 'minute'):
        max_update_perio *= 60
    
    writing_freq = 1/writing_perio
    max_update_freq = 1/max_update_perio
    #end transform

    output_file_data = f'{writing_freq}\r\n{max_update_freq}'

    return output_file_data
    
def prepare_time_file(init_date, end_date, init_time, end_time): #prepare time file
    init_time = datetime.datetime.combine(datetime.date.today(), init_time)
    end_time = datetime.datetime.combine(datetime.date.today(), end_time)
    duration = (end_date - init_date).seconds + (end_time - init_time).seconds
    time_file = f'0\r\n{duration}'
    return time_file

def prepare_gauge_file(context, init_date, end_date, init_time, end_time):
    files = []

    # context_points = e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context=context)
    context_points = e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context=context).distinct('sensor')
    for point in context_points: 
        sensor_obs = e_SensorObservation.objects.filter(sensor=point.sensor)
        sensor_obs_valid = sensor_obs.filter(date__gte=init_date).filter(date__lte=end_date).filter(time__gte=init_time).filter(time__lte=end_time)
        file_data = ''
        instant = 0
        
        for obs in sensor_obs_valid:
            if sensor_obs_valid.first().depth is not None:
                line = f'{instant}\t{obs.depth}\r\n' #must be changed according to value
            elif sensor_obs_valid.first().discharge is not None:
                line = f'{instant}\t{obs.discharge}\r\n' #must be changed according to value
            elif sensor_obs_valid.first().volume is not None:
                line = f'{instant}\t{obs.volume}\r\n' #must be changed according to value
            elif sensor_obs_valid.first().velocity is not None:
                line = f'{instant}\t{obs.velocity}\r\n' #must be changed according to value
            elif sensor_obs_valid.first().elevation is not None:
                line = f'{instant}\t{obs.elevation}\r\n' #must be changed according to value

            file_data += line
            instant += 60

        files.append((f'sensor_{point.sensor.code}.bnd', file_data))
        
    return files

def prepare_boundaries_file(context):
    boundaries = e_ContextBoundaryLine.objects.filter(context=context)
    i = 0
    result = ''

    for boundary in boundaries:
        result += f'{i}\r\n'
        i += 1

        if boundary.type.lower() == 'input':
            result += '2\r\n'
        elif boundary.type.lower() == 'output':
            result += '3\r\n'
        else:
            result += '4\r\n'

        result += '0.0\r\n10.0\r\n\r\n'

    return result

# Return last line of output
def get_last_line(status:str):
    if status == "":
        return ""
    lines:list = status.splitlines()
    if lines[-1] == "" or lines[-1].isspace():
        return get_last_line("\n".join(lines[0:len(lines)-1]))
    return lines[-1]

# Enhance this
def get_status(last_line:str):
    if ("Permission denied" in last_line) or ("Fail" in last_line) or ("Error" in last_line):
        return "Fail"
    elif ("all files written in" in last_line) or ("--:--:--" in last_line):
        return "Finished successfully"
    else:
        return "Processing"

@login_required
def mesh_status_progress(request, context_name):
    context = get_object_or_404(e_Context, Name=context_name)
    get_object_or_404(Membership, organization=context.organization, user=request.user)
    simulator_address = os.environ['SIMULATOR_ADDRESS']
    url = simulator_address + 'process-status/'

    try:
        payload = {'context_name': context_name}
        response = requests.get(url, params=payload)
        if response.status_code != 200:
            return HttpResponse(status=400)
        
        body = response.content
        lastline = get_last_line(body.decode("utf-8"))
        status = get_status(lastline)

        # Notification
        if ("Fail" in status) or ("Finished successfully" in status):
            notify.send(sender=context, recipient=context.requester, action_object=context.organization, verb=f"Context {context.Name} has finished its processing with status '{status}'")

        return JsonResponse({'status' : status, 'message' : lastline})
    except: # iStav not online
        # 503 = service unavailable
        return HttpResponse(status=503)
    

def mesh_status_change(request, context_name): # Function to mark mesh has generated
    context = e_Context.objects.get(Name=context_name)
    if request.GET.get('status'):
        context.hasMesh = True
        context.task_id = None # task finished
    else:
        context.hasMesh = False

    context.save()

    return HttpResponse(status=200)

def inform_mesh_status(request, context_code): # Function to inform if mesh is generated
    context = e_Context.objects.get(code=context_code)
    if context.hasMesh:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=400)

# TODO: check for permissions
@login_required
def download_simulation_results(request, event_id): #function to download simulation results
    url = os.environ['SIMULATOR_ADDRESS']

    try:
        context_event = e_ContextEvent.objects.get(pk=event_id)
    except:
        messages.warning(request, 'Request unsuccesful')
        return HttpResponseRedirect(reverse('event-list'))

    context_name = context_event.context.Name

    payload = {'context_name': context_name, 'event_id': event_id}
    request = requests.get(f'{url}simulation/results/', params=payload, stream=True)

    # mem_file = BytesIO()
    # with ZipFile(mem_file, 'w') as destination:
    #     for chunk in request.iter_content(chunk_size=1024):
    #             destination.write(chunk)

            
    print(f'Simulation results requested for context {context_name} event {event_id}')
    response = FileResponse(BytesIO(request.content))
    response['Content-Disposition'] = f'attachment; filename="{context_name}_{event_id}_simulation_results.zip"'
    return response

def handle_simulation_results(request, event_id): #function to handle simulation results
    sim_url = os.environ['SIMULATOR_ADDRESS']

    event = e_ContextEvent.objects.get(pk=event_id)
    context_name = event.context.Name
    url = f'{sim_url}/simulation/results/?event_id={event_id}&context_name={context_name}'

    try:
        req = requests.get(url)
    except Exception as e:
        print(f'Simulation event handling failed: {e}')
        return HttpResponse(status=404)

    with ZipFile(BytesIO(req.content)) as simulation_results_zip:
        simulation_results_zip.extractall(f'{settings.MEDIA_ROOT}/rasters/')

    try:
        results = event.context_event_results
        results.time = timezone.now()
    except ObjectDoesNotExist:
        results = e_ContextEventResult()
        results.context_event = event
        results.time = timezone.now()

    try:
        results.max_depth = define_raster('Max Depth', f'rasters/results/{context_name}_event_{event_id}-Max_Depth.tif')
        results.max_level = define_raster('Max Level', f'rasters/results/{context_name}_event_{event_id}-Max_Level.tif')
        results.max_q = define_raster('Max Q', f'rasters/results/{context_name}_event_{event_id}-Max_Q.tif')
        results.max_vel = define_raster('Max Vel', f'rasters/results/{context_name}_event_{event_id}-Max_Vel.tif')

        results.save()
    except Exception as e:
        print(f'Simulation results upload failed\nException: {e}')
        return HttpResponse(status=404)

    return HttpResponse(status=200)

def define_raster(name, file): # fucntion to create and return a raster layer
    raster = RasterLayer()
    raster.datatype='co'
    raster.name = name
    raster.srid = 3763
    raster.rasterfile = file
    raster.save()

    return raster

# TODO: check for permissions
@login_required
def view_events_results(request, event_id): #function to view the results of an event simulation
    event = e_ContextEvent.objects.get(pk=event_id)
    web_host = os.environ['CONTEXT_API']
    
    context = {
        'api': f'http://{web_host}/contexts/api/context/',
        'context': event.context,
        'sensors': e_Sensor.objects.all(),
        'event': event,
        'max_depth': event.context_event_results.max_depth.id,
        'max_level': event.context_event_results.max_level.id,
        'max_q': event.context_event_results.max_q.id,
        'max_vel': event.context_event_results.max_vel.id
    }

    return render(request, 'context/event_results.html', context)  


@login_required
def mesh_progress(request, context_code):
    e_context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, e_context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    context = {
        'context': e_context
    }
    
    return render(request, 'context/mesh_progress.html', context)

@login_required
def regenerate_mesh_confirm(request, context_code):
    e_context = get_object_or_404(e_Context, code=context_code)
    if not context_organization_edit_permission_check(request.user, e_context.organization): #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    context = {
        'context': e_context
    }
    
    return render(request, 'context/regenerate_mesh_confirm.html', context)