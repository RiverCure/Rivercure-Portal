from django.shortcuts import render
from .models import e_District, e_HydroFeature
from context.models import e_Context


def home(request):
    context = {
        'districts': e_District.objects.all(),
        'contexts': e_Context.objects.all(),
    }
    return render(request, 'rivercureportal/home.html', context)

def about(request):
    return render(request, 'rivercureportal/about.html')

def hydrofeatures(request):
    context = {
        'hydrofeatures': e_HydroFeature.objects.all(), 
    }

    return render(request, 'rivercureportal/hydrofeatures.html', context)