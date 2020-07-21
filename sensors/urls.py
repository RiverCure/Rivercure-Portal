
from .views import SensorListView
from django.urls import path, include

urlpatterns = [

    path('', SensorListView.as_view(), name='sensor-list'),
   
]