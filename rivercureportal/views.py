from django.shortcuts import render
from .models import e_District
from context.models import e_Context

def home(request):
    context = {
        'districts': e_District.objects.all(),
        'contexts': e_Context.objects.all(),
    }
    return render(request, 'rivercureportal/home.html', context)

def about(request):
    return render(request, 'rivercureportal/about.html')