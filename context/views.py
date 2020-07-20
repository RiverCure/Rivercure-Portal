from django.shortcuts import render
from .forms import ContextForm
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment
from sensors.models import e_Sensor
from rest_framework import viewsets
from .serializers import ContextSerializer
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry, Point
import json, os

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

    return render(request, 'context/context.html', context)

def context_creation(form, user): # function to initialize and save the context given a form and the user that submited the form
    context = e_Context.objects.get(pk=form.cleaned_data['code']) # get the model from the database
    context.Name = form.cleaned_data['name']
    context.hydroFeature = form.cleaned_data['hydroFeature']
    context.geomExternalBoundary = MultiPolygon(Polygon(json.loads(form.cleaned_data['domain'])['geometry']['coordinates'][0]))
    return context

def refinement_creation(form, context):
    e_ContextRefinement.objects.filter(context=context).delete()
    for feature in json.loads(form.cleaned_data['refinement'])['features']:
        refinement = e_ContextRefinement()
        refinement.context = context
        refinement.CL = 0; #temporary solution
        print('\n\n\n\n')
        print(feature['geometry']['coordinates'])
        refinement.geom = Polygon(feature['geometry']['coordinates'][0])
        refinement.save()

def alignment_creation(form, context):
    e_ContextAlignment.objects.filter(context=context).delete()
    for feature in json.loads(form.cleaned_data['alignment'])['features']:
        alignment = e_ContextAlignment()
        alignment.context = context
        alignment.CL = 0; #temporary solution
        alignment.geom = LineString(feature['geometry']['coordinates'])
        alignment.save()


def boundaryline_creation(form, context): # function to create the several lines
    e_ContextBoundaryLine.objects.filter(context=context).delete()
    e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context=context).delete()
    for feature in json.loads(form.cleaned_data['boundaries'])['features']:
        boundary = e_ContextBoundaryLine()
        boundary.context = context   
        boundary.geom = LineString(feature['geometry']['coordinates'])
        boundary.type = 'Input' #temporary solution
        boundary.dataType = 'H'
        boundary.save()
        # Save the points on the boundary line
        for point in feature['geometry']['coordinates']:
            boundary_point = e_ContextBoundaryPoint()
            boundary_point.contextBoundaryLine = boundary
            boundary_point.geom = Point(point)
            boundary_point.sensor = None #Needs to be changed
            boundary_point.save()

class ContextViewSet(viewsets.ModelViewSet):
    queryset = e_Context.objects.all()
    lookup_field = 'code'
    serializer_class = ContextSerializer