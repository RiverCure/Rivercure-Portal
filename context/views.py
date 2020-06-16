from django.shortcuts import render
from .forms import ContextForm
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context

def show_context(request):
    if request.method == 'POST':
        form = ContextForm(request.POST)
        if form.is_valid():
            form.save()
            # new_context = e_Context()
            # new_context.code = form.cleaned_data.get('code')
            # new_context.Name = form.cleaned_data.get('Name')
            # new_context.hydroFeature = form.cleaned_data.get('hydroFeature')
            # new_context.geom = Polygon(form.cleaned_data.get('form-polygon'))
            # new_context.save()
            messages.success(request,f'Context created with success!') 
            return render(request, 'context/context.html', {'form': form})


    else:
        form = ContextForm()
    return render(request, 'context/context.html', {'form': form})
