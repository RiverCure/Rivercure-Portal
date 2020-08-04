
from .views import SensorListView
from django.urls import path, include

urlpatterns = [

    path('', SensorListView, name='sensor-list'),
    #path('hydrofeature/<int:pk>', HydroFeatureDetailView.as_view(), name='hydrofeature-detail'),
   
]