
from .views import SensorListView, SensorDetailView, SensorDeleteView, SensorUpdateView
from django.urls import path, include

urlpatterns = [

    path('', SensorListView, name='sensor-list'),
    path('<str:pk>', SensorDetailView.as_view(), name='sensor-detail'),
    path('<str:pk>/update/', SensorUpdateView.as_view(), name='sensor-update'),
    path('<str:pk>/delete/', SensorDeleteView.as_view(), name='sensor-delete'),
   
]