from django.shortcuts import render
from .forms import ContextForm
from django.contrib import messages
from django.contrib.gis.geos import Polygon
from .models import e_Context

def show_context(request):
    context = {
        'contexts': e_Context.objects.all(),
        'form': ContextForm()
    }

    if request.method == 'POST':
        form = ContextForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,f'Context created with success!') 
            return render(request, 'context/context.html', context)

    return render(request, 'context/context.html', context)
