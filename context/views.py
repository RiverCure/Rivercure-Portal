from django.shortcuts import render
from .forms import ContextForm
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString, GEOSGeometry
import json

def show_context(request):
    context = {
        'contexts': e_Context.objects.all(),
        'form': ContextForm()
    }

    if request.method == 'POST':
        if not request.user.is_authenticated: # if user is not authenticated
            return render(request, 'context/context.html', context)

        form = ContextForm(request.POST)
        if form.is_valid():
            e_context = context_creation(form, request.user)
            e_context.save()

            # initialize and save boundaries
            boundaryline_creation(form, e_context).save()

            # initialize and save boundaries point
            # boundary_point = e_ContextBoundaryPoint()

            messages.success(request,f'Context created with success!') 
            return render(request, 'context/context.html', context)

    return render(request, 'context/context.html', context)

def context_creation(form, user): # function to initialize and save the context given a form and the user that submited the form
    context = e_Context()
    context.code = form.cleaned_data['code']
    context.Name = form.cleaned_data['name']
    context.hydroFeature = form.cleaned_data['hydroFeature']
    context.geomExternalBoundary = MultiPolygon(Polygon(json.loads(form.cleaned_data['domain'])['geometry']['coordinates'][0]))
    context.geomInternalBoundary = MultiPolygon(Polygon(json.loads(form.cleaned_data['refinement'])['geometry']['coordinates'][0]))
    context.geomAlignment = MultiLineString(LineString(json.loads(form.cleaned_data['alignment'])['geometry']['coordinates']))
    context.user = user

    return context

def boundaryline_creation(form, context):
    boundary = e_ContextBoundaryLine()
    boundary.context = context   
    lineStrings = []
    for feature in json.loads(form.cleaned_data['boundaries'])['features']:
        lineStrings.append(LineString(feature['geometry']['coordinates']))

    boundary.geom = MultiLineString(lineStrings)
    boundary.type = 'Input' #temporary solution

    return boundary