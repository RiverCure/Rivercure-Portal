
from django.urls import path, include
from .views import (
    SensorCreateView, 
    SensorListView, 
    SensorDetailView, 
    SensorDeleteView, 
    SensorUpdateView , 
    SensorObservationListView, 
    SensorObservationDetailView,
    SensorObservationDeleteView,
    SensorObservationUpdateView,
    sensor_observations_upload,
    sensor_upload,
    SensorObservationCreateView,
    SensorGeoUpdateView,
)

urlpatterns = [
    path('', SensorListView, name='sensor-list'),
    path('new/', SensorCreateView.as_view(), name='sensor-create'),
    path('<str:pk>', SensorDetailView.as_view(), name='sensor-detail'),
    path('<str:pk>/update/', SensorUpdateView.as_view(), name='sensor-update'),
    path('<str:pk>/geo-update/', SensorGeoUpdateView.as_view(), name='sensor-geo-update'),
    path('<str:pk>/delete/', SensorDeleteView.as_view(), name='sensor-delete'),
    path('<str:pk>/observation/new/' , SensorObservationCreateView.as_view(), name='sensor-observation-create'),
    path('<str:pk>/observations/' , SensorObservationListView, name='sensor-observation-list'),
    path('<str:pk1>/observation/<int:pk>', SensorObservationDetailView.as_view(), name='sensor-observation-detail'),
    path('<str:pk1>/observation/<int:pk>/update/', SensorObservationUpdateView.as_view(), name='sensor-observation-update'),
    path('<str:pk1>/observation/<int:pk>/delete/', SensorObservationDeleteView.as_view(), name='sensor-observation-delete'),
    path('<str:pk>/observation/upload/', sensor_observations_upload, name='sensor-observations-upload'),
    path('upload/', sensor_upload, name='sensor-upload'),
]