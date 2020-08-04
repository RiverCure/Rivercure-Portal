from django.shortcuts import render
from .forms import ContextForm
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextEvent, e_ContextSensor
from sensors.models import e_Sensor
from rest_framework import viewsets
from .serializers import ContextSerializer
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry, Point
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
import json, os
from .filters import EventFilter, EventSensorFilter


#NEW URL + FILTER  + TEMPLATE 
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



