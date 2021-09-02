
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
    SensorClassListView
)
from sensors.views.sensorClass import SensorClassCreateView, SensorClassDeleteView, SensorClassDetailView, SensorClassUpdateView
from sensors.views.sensorClassProperty import SensorClassPropertyCreateView, SensorClassPropertyDeleteView, SensorClassPropertyDetailView, SensorClassPropertyListView, SensorClassPropertyUpdateView

urlpatterns = [
    # Sensors
    path('', SensorListView.as_view(), name='sensor-list'),
    path('new/', SensorCreateView.as_view(), name='sensor-create'),
    path('<str:pk>', SensorDetailView.as_view(), name='sensor-detail'),
    path('<str:pk>/update/', SensorUpdateView.as_view(), name='sensor-update'),
    path('<str:pk>/geo-update/', SensorGeoUpdateView.as_view(), name='sensor-geo-update'),
    path('<str:pk>/delete/', SensorDeleteView.as_view(), name='sensor-delete'),
    # Observations
    path('<str:pk>/observation/new/' , SensorObservationCreateView.as_view(), name='sensor-observation-create'),
    path('<str:pk>/observations/' , SensorObservationListView, name='sensor-observation-list'),
    path('<str:pk1>/observation/<int:pk>', SensorObservationDetailView.as_view(), name='sensor-observation-detail'),
    path('<str:pk1>/observation/<int:pk>/update/', SensorObservationUpdateView.as_view(), name='sensor-observation-update'),
    path('<str:pk1>/observation/<int:pk>/delete/', SensorObservationDeleteView.as_view(), name='sensor-observation-delete'),
    # Upload
    path('<str:pk>/observation/upload/', sensor_observations_upload, name='sensor-observations-upload'),
    path('upload/', sensor_upload, name='sensor-upload'),
    # SensorClass
    path('sensor-class/<int:organizationId>', SensorClassListView.as_view(), name='sensor-class-list'),
    path('sensor-class/<int:organizationId>/new', SensorClassCreateView.as_view(), name='sensor-class-create'),
    path('sensor-class/<str:sensorClassId>/detail', SensorClassDetailView.as_view(), name='sensor-class-detail'),
    path('sensor-class/<str:sensorClassId>/update', SensorClassUpdateView.as_view(), name='sensor-class-update'),
    path('sensor-class/<str:sensorClassId>/delete', SensorClassDeleteView.as_view(), name='sensor-class-delete'),
    # SensorClass Property
    path('sensor-class/<int:sensorClassId>/property/list', SensorClassPropertyListView.as_view(), name='sensor-class-property-list'),
    path('sensor-class/<int:sensorClassId>/property/new', SensorClassPropertyCreateView.as_view(), name='sensor-class-property-create'),
    path('sensor-class/<int:sensorClassId>/property/<int:sensorClassPropertyId>/detail', SensorClassPropertyDetailView.as_view(), name='sensor-class-property-detail'),
    path('sensor-class/<str:sensorClassId>/property/<int:sensorClassPropertyId>/update', SensorClassPropertyUpdateView.as_view(), name='sensor-class-property-update'),
    path('sensor-class/<str:sensorClassId>/property/<int:sensorClassPropertyId>/delete', SensorClassPropertyDeleteView.as_view(), name='sensor-class-property-delete'),
]