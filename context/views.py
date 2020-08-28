import json, os, geojson, tempfile, datetime
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.db import transaction
from .forms import ContextForm, UploadContextForm
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextEvent, e_ContextSensor, e_ContextAccessRequest
from sensors.models import e_Sensor
from rest_framework import viewsets
from django.core.serializers import serialize
from .serializers import ContextSerializer
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry, Point
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .filters import EventFilter, EventSensorFilter, ContextFilter
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from io import BytesIO, StringIO
from zipfile import ZipFile
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin



def GrantAccess(request):
    context = {
        
    }

    
    return render(request, 'rivercure/home.html', context)




def ContextRequestDecisionView(request, pk):
    pedido = e_ContextAccessRequest.objects.get(id=pk)
    context = pedido.context

    context  = {
        #user
        'context': e_Context.objects.first

    }
    return render(request, 'context/e_ContextRequest_grant_deny.html', context)

class ContextRequestListView(UserPassesTestMixin, ListView):
    model = e_ContextAccessRequest
    context_object_name = 'requests'
    template_name = 'context/e_ContextRequests_list.html'

    def test_func(self):
        if self.request.user.has_perm('can_add_group'):
            return True
        else:
            return False

def ContextListView(request):
    context_list = e_Context.objects.filter(user=request.user)
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
        if self.request.user.has_perm('can_update_contexts') and self.object.user == self.request.user:
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        web_host = os.environ['CONTEXT_API']
        context = super().get_context_data(**kwargs)
        context['api'] = f'http://{web_host}/contexts/api/context/'
        context['sensors'] = e_Sensor.objects.all()
               
        return context
    



def ContextSensorListView(request):
    contextSensor_list = e_ContextSensor.objects.all()
    contextSensor_filter = EventSensorFilter(request.GET, queryset=contextSensor_list)
    return render(request, 'context/e_ContextSensor_list.html', {'filter': contextSensor_filter})


def EventListView(request):
    event_list = e_ContextEvent.objects.all()
    event_filter = EventFilter(request.GET, queryset=event_list)
    return render(request, 'context/e_Event_list.html', {'filter': event_filter})

class EventDetailView(DetailView):
    model = e_ContextEvent
    context_object_name = 'event'
    template_name = 'context/e_Event_detail.html'


def show_context(request):
    web_host = os.environ['CONTEXT_API']
    context = {
        'contexts': e_Context.objects.filter(user__username=request.user).order_by('Name'),
        'sensors': e_Sensor.objects.all(),
        'form': ContextForm(),
        'api': f'http://{web_host}/contexts/api/context/',
        'context': request.GET.get('context_code')
    }
    if request.method == 'POST':
        if not request.user.is_authenticated: # if user is not authenticated
            return render(request, 'context/context.html', context)
        
        form = ContextForm(request.POST)
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

                    messages.success(request,f'Context created with success!') 
            except Exception as e:
                print(f'Error saving context: {e}')
                messages.warning(request,f'Context update failed') 
        else:
            messages.warning(request,f'Context info is not complete') 

    return render(request, 'context/context.html', context)

#aux functions for show_context()
def context_creation(form, user): # function to initialize and save the context given a form and the user that submited the form
    context = e_Context.objects.get(pk=form.cleaned_data['code']) # get the model from the database

    if context.user != user: # if user doesn't own the context
        print('User that doesn\'t own the context tried to change it!')
        return None
                
    context.Name = form.cleaned_data['name']
    context.hydroFeature = form.cleaned_data['hydroFeature']
    context.geomExternalBoundary = MultiPolygon(Polygon(json.loads(form.cleaned_data['domain'])['geometry']['coordinates'][0]))
    context.CLExternalBoundary = json.loads(form.cleaned_data['domain'])['properties']['CL']
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
                    boundary_point_sensor.associateDatetime = datetime.datetime.now()
                    boundary_point_sensor.sensor = e_Sensor.objects.get(code=sensor)
                    boundary_point_sensor.boundary_point = boundary_point
                    boundary_point_sensor.save()
                
#end of aux functions for show_context()

class ContextViewSet(viewsets.ModelViewSet):
    queryset = e_Context.objects.all()
    lookup_field = 'code'
    serializer_class = ContextSerializer

class UploadContext(FormView):
    template_name = 'context/context_upload.html'
    form_class = UploadContextForm

    def form_valid(self, form):
        try:
            with transaction.atomic():
                context = e_Context()
                context.code = form.cleaned_data['code']
                srid = handle_domain(form.cleaned_data['domain'], context, self.request.user)
                handle_alignment(form.cleaned_data['alignments'], context, srid)
                handle_refinement(form.cleaned_data['refinements'], context, srid)
                handle_boundaries(form.cleaned_data['boundaries'], form.cleaned_data['boundaries_points'], context, srid)
                messages.success(self.request, 'Context Uploaded')
        except Exception as e:
            print(f'Error loading the files:\n{e}')
            messages.warning(self.request, 'Context Upload Failed') 

        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('context_upload')
    
def handle_domain(f, context, user): #handle the loading of domain from a geojson
    domain_features = json.load(f)
    try:
        srid = SpatialReference(domain_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    context.Name = str.title(domain_features['name'].split('_')[0])
    context.hydroFeature = None
    context.CLExternalBoundary = domain_features['features'][0]['properties']['CL']
    domain_geom = MultiPolygon(Polygon(domain_features['features'][0]['geometry']['coordinates'][0][0], srid=srid), srid=srid)
    context.geomExternalBoundary = domain_geom
    # context.geomExternalBoundary.transform(SpatialReference(4326))
    context.user = user
    context.save()
    
    return srid
    
def handle_alignment(f, context, srid): #handle the loading of alignment from a geojson
    for feature in json.load(f)['features']:
        alignment = e_ContextAlignment()
        alignment.context = context
        alignment.CL = feature['properties']['CL']
        alignment.geom = LineString(feature['geometry']['coordinates'][0], srid=srid)
        alignment.save()

def handle_refinement(f, context, srid): #handle the loading of refinement from a geojson
    for feature in json.load(f)['features']:
        refinement = e_ContextRefinement()
        refinement.context = context
        refinement.CL = feature['properties']['CL']
        refinement.geom = Polygon(feature['geometry']['coordinates'][0][0], srid=srid)
        refinement.save()

def handle_boundaries(f, f_points, context, srid): #handle the loading of boundaries from a geojson
    boundary_points = json.load(f_points)['features']

    for feature in json.load(f)['features']:
        boundary = e_ContextBoundaryLine()
        boundary.context = context  
        boundary.geom = LineString(feature['geometry']['coordinates'][0], srid=srid)
        boundary.dataType = feature['properties']['Type']
        # boundary.type = feature['properties']['dataType']
        boundary.save()
        
        # Save the points on the boundary line
        for point in boundary_points:
            if(boundary.geom.intersects(Point(point['geometry']['coordinates'], srid=srid))):
                boundary_point = e_ContextBoundaryPoint()
                boundary_point.contextBoundaryLine = boundary
                boundary_point.geom = Point(point['geometry']['coordinates'], srid=srid)
                boundary_point.save()

                # Handle sensors on point
                # for sensor in point['properties']['sensors']:
                #     boundary_point_sensor = e_ContextSensor()
                #     boundary_point_sensor.associateDatetime = datetime.datetime.now()
                #     boundary_point_sensor.sensor = e_Sensor.objects.get(code=sensor)
                #     boundary_point_sensor.boundary_point = boundary_point
                #     boundary_point_sensor.save()

def download_context(request, context_code): #function that allows the download of an context
    if not request.user.is_authenticated: #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)

    message = None  #Message to send to user in case of failure

    #prepare geojson for download

    #Need to check if context code exists
    try:
        #------------------ Domain --------------------------------
        context = e_Context.objects.get(code=context_code)

        context_main = geojson.Feature(geometry= geojson.MultiPolygon(context.geomExternalBoundary.coords),
                            properties = {"Geometry type": 'Domain',
                                        "Code": context.code,
                                        "CL": context.CLExternalBoundary})

        features = []
        features.append(context_main)
        domain_file = geojson.FeatureCollection(features)
        domain_file['name'] = str.title(context.Name)
        # domain_file['crs'] = { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3763" } }

        #------------------ Alignment --------------------------------

        features = []
        for alignment in e_ContextAlignment.objects.filter(context__code=context_code):
            context_alignment = geojson.Feature(geometry= geojson.LineString(alignment.geom.coords),
                                properties = {"Geometry type": 'Alignment',
                                            "Context code": context.code,
                                            "Context name": str.title(context.Name),
                                            "CL": alignment.CL})

            features.append(context_alignment)

        alignment_file = geojson.FeatureCollection(features)
        alignment_file['name'] = str.title(context.Name).join('_alignments')

        #------------------ Refinement --------------------------------  

        features = []
        for refinement in e_ContextRefinement.objects.filter(context__code=context_code):
            context_refinement = geojson.Feature(geometry= geojson.Polygon(refinement.geom.coords),
                                properties = {"Geometry type": 'Refinement',
                                            "Context code": context.code,
                                            "Context name": str.title(context.Name),
                                            "CL": refinement.CL})

            features.append(context_refinement)

        refinement_file = geojson.FeatureCollection(features)
        refinement_file['name'] = str.title(context.Name).join('_refinements')

        #------------------ Boundary --------------------------------

        features = []
        for boundary in e_ContextBoundaryLine.objects.filter(context__code=context_code):
            context_boundary = geojson.Feature(geometry= geojson.LineString(boundary.geom.coords),
                                properties = {"Geometry type": 'Boundary Line',
                                            "Contextc ode": context.code,
                                            "Context name": str.title(context.Name),
                                            "Type": boundary.type,
                                            "Data type": boundary.dataType})

            features.append(context_boundary)

        boundary_file = geojson.FeatureCollection(features)
        boundary_file['name'] = str.title(context.Name).join('_boundaries')

        #------------------ Boundary Points --------------------------------

        features = []
        for boundary_point in e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context__code=context_code):
            context_boundary_points = geojson.Feature(geometry= geojson.Point(boundary_point.geom.coords),
                                properties = {"Geometry type": 'Boundary Point',
                                            "Context code": context.code,
                                            "Context name": str.title(context.Name),
                                            "Boundary": '0'}) #must be changed

            features.append(context_boundary_points)

        boundary_point_file = geojson.FeatureCollection(features)
        boundary_point_file['name'] = str.title(context.Name).join('_boundary_points')

        #endof json preparation

        mem_file = BytesIO() #memory where the zip file will be created
        with ZipFile(mem_file, 'w') as zipFolder: #create a zipped folder to return to the user
            zipFolder.writestr(f'{context.Name}_domain.geojson', geojson.dumps(domain_file))
            zipFolder.writestr(f'{context.Name}_alignments.geojson', geojson.dumps(alignment_file))
            zipFolder.writestr(f'{context.Name}_refinements.geojson', geojson.dumps(refinement_file))
            zipFolder.writestr(f'{context.Name}_boundaries.geojson', geojson.dumps(boundary_file))
            zipFolder.writestr(f'{context.Name}_boundaries_points.geojson', geojson.dumps(boundary_point_file))

        mem_file.seek(0)
        response = HttpResponse(mem_file.read(), content_type="application/zip")
        response['Content-Disposition'] = 'attachment; filename="%s.zip"'%context.Name
        return response
    except:
        messages.warning(request,f'Context not complete for download') 
        return redirect(request.META['HTTP_REFERER'])

