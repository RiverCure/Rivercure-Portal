import json, os, geojson, tempfile, datetime, requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction, connection
from django.utils import timezone
from .forms import ContextForm, UploadContextForm, EventForm
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context, e_ContextDTM, e_ContextContourLine, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextEvent, e_ContextSensor, e_ContextAccessRequest
from raster.models import RasterLayer
from sensors.models import e_Sensor, e_SensorObservation
from rest_framework import viewsets
from django.core.serializers import serialize
from .serializers import ContextSerializer
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry, Point, fromfile
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .filters import EventFilter, EventSensorFilter, ContextFilter, ContextSensorFilter
from django.contrib.gis.gdal import SpatialReference, CoordTransform, GDALRaster
from io import BytesIO, StringIO
from zipfile import ZipFile
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from pprint import pprint

class ContextAccessCreateView(UserPassesTestMixin, CreateView):
    model = e_ContextAccessRequest
    fields = ['type', 'context']
    template_name = "context/e_ContextAccessRequest_create.html"
    #success_url =  "/contexts/"
    
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.requestuser = self.request.user
        obj.save() 
        return HttpResponseRedirect("/contexts")
        
    def test_func(self, *args , **kwargs):
        if self.request.user.groups.filter(name='ContextManager').exists() or self.request.user.groups.filter(name='ContextAdmin').exists() :
            return True 

def ContextRequestDecisionView(request, pk):
    pedido = e_ContextAccessRequest.objects.get(id=pk)
    requester = pedido.requestuser
    context = {
        'sensors': e_Sensor.objects.all(),
        'user': requester,
        'context': e_Context.objects.first(),
        'request': pedido,
    }
    return render(request, 'context/e_ContextRequest_grant_deny.html', context)

def GrantAccess(request, pk):
    pedido = e_ContextAccessRequest.objects.get(id=pk)
    requester = pedido.requestuser
    pedido.access_granted = True
    pedido.state = "Finished"
    pedido.save()   

    context = {
        'user': requester,   
    }
    return render(request, 'context/access_granted.html', context)

class ContextRequestListView(UserPassesTestMixin, ListView):
    model = e_ContextAccessRequest
    context_object_name = 'requests'
    template_name = 'context/e_ContextRequests_list.html'

    def test_func(self):
        if self.request.user.groups.filter(name='ContextAdmin').exists() :
            return True
        else:
            return False

def ContextListView(request):
    context_list = e_Context.objects.filter(user=request.user)

    granted_list = e_ContextAccessRequest.objects.filter(state='Finished', access_granted='True', requestuser=request.user)

    context_filter = ContextFilter(request.GET, queryset=context_list)
    return render(request, 'context/e_Context_list.html', {'filter': context_filter})

def OtherContextListView(request):
    other_context_list = e_Context.objects.exclude(user=request.user)
    other_context_filter = ContextFilter(request.GET, queryset=other_context_list)
    return render(request, 'context/e_OtherContext_list.html', {'filter': other_context_filter})

    #def get_context_data(self, **kwargs):
        #web_host = os.environ['CONTEXT_API']
        #context = super().get_context_data(**kwargs)
        #context['owned_contexts'] = e_Context.objects.filter(user=self.request.user)
        #context['other_contexts'] = e_Context.objects.exclude(user=self.request.user)
        #return context

class ContextDetailView(UserPassesTestMixin, DetailView):
    model = e_Context
    context_object_name = 'context'
    template_name = 'context/e_Context_detail.html'

    def test_func(self, *args , **kwargs):
        self.object = self.get_object()
        if self.object.isPublic and self.request.user.is_authenticated:
            if self.request.user.groups.filter(name='ContextManager').exists() or self.request.user.groups.filter(name='ContextAdmin').exists():
                return True
            else:
                return False
        else:
            if self.request.user.groups.filter(name='ContextManager').exists() or self.request.user.groups.filter(name='ContextAdmin').exists():
                if e_ContextAccessRequest.objects.filter(requestuser=self.request.user, access_granted=True).exists() or self.object.user == self.request.user:  #para ver, falta a permissao igual mas de manager na outra view
                    return True
                else:
                    return False
                return False

    def get_context_data(self, **kwargs):
        web_host = os.environ['CONTEXT_API']
        context = super().get_context_data(**kwargs)
        context['api'] = f'http://{web_host}/contexts/api/context/'
        context['sensors'] = e_Sensor.objects.all()
        context['form'] = UploadContextForm()
               
        return context
    
def ContextSensorListView(request):
    
    context_sensor_list = e_ContextSensor.objects.filter(boundary_point__contextBoundaryLine__context__code=request.GET.get('context_code')).distinct('sensor')

    context_sensor_filter = ContextSensorFilter(request.GET, queryset=context_sensor_list)
    
    context={
        'filter' :  context_sensor_filter,
        'context_code' : request.GET.get('context_code'),
        'context_name' : request.GET.get('context_name'),
        
    }

    return render(request, 'context/e_ContextSensor_list.html', context )

class EventUpdateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_ContextEvent
    success_url = 'event-list'
    template_name = 'context/e_Event_create.html'
    form_class = EventForm

    #def form_valid(self, form):
        #obj = form.save(commit=False)
        #obj.save() 
        #return HttpResponseRedirect(reverse('event-list'))

    def test_func(self):
        if self.request.user.has_perm('can_update_hydrofeatures'):
            return True
        else:
            return False

class EventCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = e_ContextEvent
    success_url = 'event-list'
    template_name = 'context/e_Event_create.html'
    form_class = EventForm

    def form_valid(self, form):
        context = form.cleaned_data['context']
        writing_period = form.cleaned_data['WritingPeriodicity']
        max_update_period = form.cleaned_data['UpdateMaximumValue']
        writing_unit = form.cleaned_data['WritingPeriodicityUnit']
        update_unit = form.cleaned_data['UpdateMaximumValueUnit']
        init_date = form.cleaned_data['startDate']
        end_date = form.cleaned_data['endDate']
        init_time = form.cleaned_data['startTime']
        end_time = form.cleaned_data['endTime']

        obj = form.save(commit=False)
        obj.save() 

        try:
            request_simulation(context, writing_period, max_update_period, writing_unit, update_unit, init_date, end_date, init_time, end_time)
            messages.success(self.request,f'Simulation request successful') 
        except Exception as e:
            print(f'Failed simulation request!\nException: {e}')
            messages.warning(self.request,f'Simulation request failed') 

        return HttpResponseRedirect(reverse('event-list'))

    def test_func(self):
        if self.request.user.has_perm('can_add_hydrofeatures'):
            return True
        else:
            return False

def EventListView(request):
    event_list = e_ContextEvent.objects.all()
    event_filter = EventFilter(request.GET, queryset=event_list)
    return render(request, 'context/e_AllEvents.html', {'filter': event_filter})

def ContextEventListView(request, context_code):
    events_list = e_ContextEvent.objects.filter(context__code=context_code)
    context = {
        'events': events_list,
        'context': events_list.first().context,
    }
    return render(request, 'context/e_Event_list.html', context)

class EventDetailView(DetailView):
    model = e_ContextEvent
    context_object_name = 'event'
    template_name = 'context/e_Event_detail.html'


def show_context(request, context_code):
    web_host = os.environ['CONTEXT_API']
    context = {
        # 'contexts': e_Context.objects.filter(user__username=request.user).order_by('Name'),
        'sensors': e_Sensor.objects.all(),
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

#aux functions for show_context()
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

def handle_contour_lines_upload(context, contour_lines_file): #function to handle the upload of the contour lines file
    contour_lines = e_ContextContourLine.objects.get_or_create(context=context)
    contour_lines_features = json.load(contour_lines_file)
    try:
        srid = SpatialReference(contour_lines_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    contour_lines_geom = []
    for feature in contour_lines_features['features']:
        line = LineString(feature['geometry']['coordinates'][0], srid=srid)
        contour_lines_geom.append(line)
    
    contour_lines[0].geom = MultiLineString(contour_lines_geom, srid=srid)
    # contour_lines.geom = MultiPolygon(Polygon(contour_lines_features['features'][0]['geometry']['coordinates'][0][0], srid=srid), srid=srid)

    contour_lines[0].save()


def context_creation(form, user): # function to initialize and save the context given a form and the user that submited the form
    context = e_Context.objects.get(pk=form.cleaned_data['code']) # get the model from the database

    if context.user != user: # if user doesn't own the context
        print('User that doesn\'t own the context tried to change it!')
        return None
                
    context.Name = form.cleaned_data['name']
    context.hydroFeature = form.cleaned_data['hydroFeature']
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
                
#end of aux functions for show_context()

class ContextViewSet(viewsets.ModelViewSet):
    queryset = e_Context.objects.all()
    lookup_field = 'code'
    serializer_class = ContextSerializer

class UploadContext(FormView):
    http_method_names = ['post']
    template_name = 'context/context_upload.html'
    form_class = UploadContextForm

    def form_valid(self, form):
        try:
            with transaction.atomic():
                context = e_Context.objects.get(code=form.cleaned_data['code'])
                if form.cleaned_data['domain'] is not None:
                    handle_domain(form.cleaned_data['domain'], context, self.request.user)
                
                #Mark edited context for mesh regeneration need
                context.hasMesh = False
                context.save()

                if form.cleaned_data['alignments'] is not None:
                    handle_alignment(form.cleaned_data['alignments'], context)
                if form.cleaned_data['refinements'] is not None:
                    handle_refinement(form.cleaned_data['refinements'], context)
                if form.cleaned_data['boundaries'] is not None:
                    handle_boundaries(form.cleaned_data['boundaries'], context)

                #Save dtm from raster file field
                dtm = self.request.FILES.get('dtm_file')
                if dtm is not None:
                    handle_upload_raster(context, dtm)

                #Save contour lines from file
                contour_lines = self.request.FILES.get('contour_lines')
                if contour_lines is not None:
                    handle_contour_lines_upload(context, contour_lines)
                
                messages.success(self.request, 'Context Uploaded')
        except Exception as e:
            print(f'Error loading the files:\n{e}')
            messages.warning(self.request, 'Context Upload Failed') 

        
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


def download_context(request, context_code): #function that allows the download of an context
    if not request.user.is_authenticated: #verify that the user is logged in
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
            zipFolder.writestr(f'{context_name}_alignments.geojson', geojson.dumps(alignment_file))
            zipFolder.writestr(f'{context_name}_refinements.geojson', geojson.dumps(refinement_file))
            zipFolder.writestr(f'{context_name}_boundaries.geojson', geojson.dumps(boundary_file))
            zipFolder.writestr(f'{context_name}_boundaries_points.geojson', geojson.dumps(boundary_point_file))

        mem_file.seek(0)
        response = HttpResponse(mem_file.read(), content_type="application/zip")
        response['Content-Disposition'] = 'attachment; filename="%s.zip"'%context_name
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
    domain_file['name'] = str.title(context_name)
    domain_file['code'] = context_code
    domain_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763"} } # str(context.geomExternalBoundary.srid)

    return domain_file

def prepare_alignment(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute('SELECT ST_AsText(ST_Transform("geom", 3763)), "CL" FROM public.context_e_contextalignment WHERE context_id= %s', [context_code])
        rows = cursor.fetchall()
        for alignment in rows:
            alignment_geom = GEOSGeometry(alignment[0])
            context_alignment = geojson.Feature(geometry= geojson.LineString(alignment_geom.coords),
                                properties = {"Geometry type": 'Alignment',
                                            "CL": alignment[1]})

            features.append(context_alignment)

    alignment_file = geojson.FeatureCollection(features)
    alignment_file['name'] = str.title(context_name) + '_alignments'
    alignment_file['Context code'] = context_code
    alignment_file['Context name'] = str.title(context_name)
    alignment_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

    return alignment_file

def prepare_refinement(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute('''SELECT ST_AsText(ST_Transform("geom", 3763)), "CL" 
                        FROM public.context_e_contextrefinement WHERE context_id= %s''', [context_code])
        rows = cursor.fetchall()
        for refinement in rows:
            refinement_geom = GEOSGeometry(refinement[0])
            context_refinement = geojson.Feature(geometry= geojson.Polygon(refinement_geom.coords),
                                properties = {"Geometry type": 'Refinement',
                                            "CL": refinement[1]})

            features.append(context_refinement)

    refinement_file = geojson.FeatureCollection(features)
    refinement_file['name'] = str.title(context_name) + '_refinements'
    refinement_file['Context code'] = context_code
    refinement_file['Context name'] = str.title(context_name)
    refinement_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

    return refinement_file

def prepare_boundaries(context_code, context_name):
    features = []
    
    with connection.cursor() as cursor:
        cursor.execute('SELECT ST_AsText(ST_Transform("geom", 3763)), "type", "dataType" FROM public.context_e_contextboundaryline WHERE context_id= %s', [context_code])
        rows = cursor.fetchall()
        for boundary in rows:
            boundary_geom = GEOSGeometry(boundary[0])
            context_boundary = geojson.Feature(geometry= geojson.LineString(boundary_geom.coords),
                                properties = {"Geometry type": 'Boundary Line',
                                            "Type": boundary[1],
                                            "Data type": boundary[2]})

            features.append(context_boundary)

    boundary_file = geojson.FeatureCollection(features)
    boundary_file['name'] = str.title(context_name) + '_boundaries'
    boundary_file['Context code'] = context_code
    boundary_file['Context name'] = str.title(context_name)
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
        for boundary_point in rows:
            boundary_point_geom = GEOSGeometry(boundary_point[0])
            context_boundary_points = geojson.Feature(geometry= geojson.Point(boundary_point_geom.coords),
                                properties = {"Geometry type": 'Boundary Point',
                                            "Boundary": boundary_point[1],
                                            "Series": f'sensor_{boundary_point[2]}.bnd',
                                            "Type": boundary_point[3]}) 

            features.append(context_boundary_points)

    boundary_point_file = geojson.FeatureCollection(features)
    boundary_point_file['name'] = str.title(context_name) + '_boundary_points'
    boundary_point_file['Context code'] = context_code
    boundary_point_file['Context name'] = str.title(context_name)
    boundary_point_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

    return boundary_point_file


def request_pre_processing(request, context_code): # function to start simulation
    url = os.environ['SIMULATOR_ADDRESS'] + 'process/'

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

        files = {
            'domain.geojson': geojson.dumps(domain_file),
            'alignments.geojson': geojson.dumps(alignment_file),
            'refinements.geojson': geojson.dumps(refinement_file),
            'boundaries.geojson': geojson.dumps(boundary_file),
            'boundaries_points.geojson': geojson.dumps(boundary_point_file)
        }  
        payload = {'context_name': context_name}
        r = requests.post(url, files=files, params=payload)

        if r.text == 'success':
            messages.success(request, 'Mesh generation request successful<br>Simulation is under way')
        else:
            messages.warning(request,f'Pre-processing failed') 
            context = e_Context.objects.get(code=context_code)
            context.hasMesh = False
            context.save()

        return redirect(request.META['HTTP_REFERER'])

    except Exception as e:
        messages.warning(request,f'Context mesh generation request failed') 
        print(f'Error requesting context mesh generation: {e}')
        return redirect(request.META['HTTP_REFERER'])

def simulation_results(request): # function to redirect the user to the paraviewweb visualizer
    paraviewweb_visualizer_url = 'http://localhost:8090'
    return redirect(paraviewweb_visualizer_url)

def request_simulation(context, writing_perio, max_update_perio, writing_unit, update_unit, init_date, end_date, init_time, end_time): # function to request a simulation for a certain context
    url = os.environ['SIMULATOR_ADDRESS'] + 'simulate/'

    payload = {'context_name': context.Name}

    #prepare files

    frequency_file = prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit)

    files = prepare_gauge_file(context, init_date, end_date, init_time, end_time)

    files.append(('frequency', frequency_file))

    r = requests.post(url, files=files, params=payload)


def prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit): # prepare output.cnt file for simulation
    # transform periodicity
    writing_freq = 1/writing_perio
    max_update_freq = 1/max_update_perio

    if(writing_unit == 'hour'):
        writing_freq *= 60 * 60
    elif(writing_unit == 'minute'):
        writing_freq *= 60

    if(update_unit == 'hour'):
        max_update_freq *= 60 * 60
    elif(update_unit == 'minute'):
        max_update_freq *= 60
    
    #end transform

    output_file_data = f'{writing_freq}\r\n{max_update_freq}'

    return output_file_data
    
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

def mesh_status_change(request, context_name): # Function to mark mesh has generated
    context = e_Context.objects.get(Name=context_name)
    if request.GET.get('status'):
        context.hasMesh = True
    else:
        context.hasMesh = False

    context.save()

    return HttpResponse(status=200)