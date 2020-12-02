
from django.urls import path, include
from .views import (
    SensorCreateView, 
    SensorListView, 
    SensorDetailView, 
    SensorDeleteView, 
    SensorUpdateView , 
    SensorUploadView,
    SensorObservationListView, 
    SensorObservationDetailView,
    SensorObservationDeleteView,
    SensorObservationUpdateView,
    sensor_observations_upload,
)

urlpatterns = [
    path('', SensorListView, name='sensor-list'),
    path('new/', SensorCreateView.as_view(), name='sensor-create'),
    path('upload/', SensorUploadView, name='sensor-upload'),
    path('<str:pk>', SensorDetailView.as_view(), name='sensor-detail'),
    path('<str:pk>/update/', SensorUpdateView.as_view(), name='sensor-update'),
    path('<str:pk>/delete/', SensorDeleteView.as_view(), name='sensor-delete'),
    path('observations/' , SensorObservationListView, name='sensor-observations'),
    path('observation/<int:pk>', SensorObservationDetailView.as_view(), name='sensor-observation-detail'),
    path('observation/<int:pk>/update/', SensorObservationUpdateView.as_view(), name='sensor-observation-update'),
    path('observation/<int:pk>/delete/', SensorObservationDeleteView.as_view(), name='sensor-observation-delete'),
    path('observation/upload/', sensor_observations_upload, name='sensor-observations-upload')
]