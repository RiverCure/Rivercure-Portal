from django.shortcuts import render
from django.http import HttpResponse
from .forms import ContextForm
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextSensor
from sensors.models import e_Sensor
from rest_framework import viewsets
from django.core.serializers import serialize
from .serializers import ContextSerializer
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry, Point
from io import BytesIO, StringIO
from zipfile import ZipFile
import json, os, geojson, tempfile, datetime

def show_context(request):
    web_host = os.environ['CONTEXT_API']
    context = {
        'contexts': e_Context.objects.filter(user__username=request.user).order_by('Name'),
        'sensors': e_Sensor.objects.all(),
        'form': ContextForm(),
        'api': f'http://{web_host}/context/api/context/'
    }
    if request.method == 'POST':
        if not request.user.is_authenticated: # if user is not authenticated
            return render(request, 'context/context.html', context)
        
        form = ContextForm(request.POST)
        if form.is_valid():
            try:
                e_context = context_creation(form, request.user)
                e_context.save()

                # initialize and save refinement
                refinement_creation(form, e_context)
                # initialize and save alignment
                alignment_creation(form, e_context)

                # initialize and save boundaries & boundary points
                boundaryline_creation(form, e_context)

                messages.success(request,f'Context created with success!') 
                return render(request, 'context/context.html', context)
            except Exception as e:
                print(f'Error saving context: {e}')
                messages.warning(request,f'Context update failed') 
                return render(request, 'context/context.html', context)

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
    for feature in json.loads(form.cleaned_data['boundaries'])['features']:
        boundary = e_ContextBoundaryLine()
        boundary.context = context   
        boundary.geom = LineString(feature['geometry']['coordinates'])
        boundary.type = feature['properties']['type']
        boundary.dataType = feature['properties']['dataType']
        boundary.save()
        
        # Save the points on the boundary line
        for point in json.loads(form.cleaned_data['boundary_points'])['features']:
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


def download_context(request, context_code): #function that allows the download of an context
    if not request.user.is_authenticated: #verify that the user is logged in
        return HttpResponse('Unauthorized', status=401)


    message = None  #Message to send to user in case of failure

    #prepare geojson for download

    #Need to check if context code exists

    #------------------ Domain --------------------------------
    context = e_Context.objects.get(code=context_code)

    context_main = geojson.Feature(geometry= geojson.MultiPolygon(context.geomExternalBoundary.coords),
                        properties = {"Geometry type": 'Domain',
                                    "Code": context.code,
                                    "Name": str.title(context.Name),
                                    "CL": context.CLExternalBoundary})

    features = []
    features.append(context_main)
    domain_file = geojson.FeatureCollection(features)

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