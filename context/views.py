from django.shortcuts import render

# Create your views here.

def show_context(request):
    
    return render(request, 'context/context.html')
