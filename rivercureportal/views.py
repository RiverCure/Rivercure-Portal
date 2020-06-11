from django.shortcuts import render


def home(request):
    return render(request, 'rivercureportal/home.html')

def about(request):
    return render(request, 'rivercureportal/about.html')