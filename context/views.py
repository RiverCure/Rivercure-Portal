from django.shortcuts import render
from .forms import ContextForm
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context
from django.contrib.gis.geos import MultiLineString, MultiPolygon, Polygon, LineString
import json

def show_context(request):
    context = {
        'contexts': e_Context.objects.all(),
        'form': ContextForm()
    }

    if request.method == 'POST':
        form = ContextForm(request.POST)
        if form.is_valid():
            # initialize and save the context
            e_context = e_Context()
            e_context.code = form.cleaned_data['code']
            e_context.Name = form.cleaned_data['name']
            e_context.hydroFeature = form.cleaned_data['hydroFeature']
            e_context.geomExternalBoundary = MultiPolygon(Polygon(json.loads(form.cleaned_data['domain'])['geometry']['coordinates'][0]))
            e_context.geomInternalBoundary = MultiPolygon(Polygon(json.loads(form.cleaned_data['refinement'])['geometry']['coordinates'][0]))
            e_context.geomAlignment = MultiLineString(LineString(json.loads(form.cleaned_data['alignment'])['geometry']['coordinates']))
            e_context.save()

            # initialize and save boundaries

            messages.success(request,f'Context created with success!') 
            return render(request, 'context/context.html', context)

    return render(request, 'context/context.html', context)
