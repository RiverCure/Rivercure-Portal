
from .views import SensorListView
from django.urls import path, include

urlpatterns = [

    path('', SensorListView, name='sensor-list'),
   
]