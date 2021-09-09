
from django.urls import path, include
from sensors import views

urlpatterns = [
    # Sensors
    path('', views.SensorListView.as_view(), name='sensor-list'),
    path('new/', views.SensorCreateView.as_view(), name='sensor-create'),
    path('<str:pk>', views.SensorDetailView.as_view(), name='sensor-detail'),
    path('<str:pk>/update/', views.SensorUpdateView.as_view(), name='sensor-update'),
    path('<str:pk>/geo-update/', views.SensorGeoUpdateView.as_view(), name='sensor-geo-update'),
    path('<str:pk>/delete/', views.SensorDeleteView.as_view(), name='sensor-delete'),
    # Observations
    path('<int:sensorId>/observation/new/' , views.SensorObservationCreateView.as_view(), name='sensor-observation-create'),
    path('<int:sensorId>/observations/' , views.SensorObservationListView.as_view(), name='sensor-observation-list'),
    path('<int:sensorId>/observation/<int:observationId>', views.SensorObservationDetailView.as_view(), name='sensor-observation-detail'),
    path('<int:sensorId>/observation/<int:observationId>/update/', views.SensorObservationUpdateView.as_view(), name='sensor-observation-update'),
    path('<int:sensorId>/observation/<int:observationId>/delete/', views.SensorObservationDeleteView.as_view(), name='sensor-observation-delete'),
    # Upload
    path('<str:pk>/observation/upload/', views.sensor_observations_upload, name='sensor-observations-upload'),
    path('upload/', views.sensor_upload, name='sensor-upload'),
    # SensorClass
    path('sensor-class/<int:organizationId>', views.SensorClassListView.as_view(), name='sensor-class-list'),
    path('sensor-class/<int:organizationId>/new', views.SensorClassCreateView.as_view(), name='sensor-class-create'),
    path('sensor-class/<str:sensorClassId>/detail', views.SensorClassDetailView.as_view(), name='sensor-class-detail'),
    path('sensor-class/<str:sensorClassId>/update', views.SensorClassUpdateView.as_view(), name='sensor-class-update'),
    path('sensor-class/<str:sensorClassId>/delete', views.SensorClassDeleteView.as_view(), name='sensor-class-delete'),
    # SensorClass Property
    path('sensor-class/<int:sensorClassId>/property/list', views.SensorClassPropertyListView.as_view(), name='sensor-class-property-list'),
    path('sensor-class/<int:sensorClassId>/property/new', views.SensorClassPropertyCreateView.as_view(), name='sensor-class-property-create'),
    path('sensor-class/<int:sensorClassId>/property/<int:sensorClassPropertyId>/detail', views.SensorClassPropertyDetailView.as_view(), name='sensor-class-property-detail'),
    path('sensor-class/<str:sensorClassId>/property/<int:sensorClassPropertyId>/update', views.SensorClassPropertyUpdateView.as_view(), name='sensor-class-property-update'),
    path('sensor-class/<str:sensorClassId>/property/<int:sensorClassPropertyId>/delete', views.SensorClassPropertyDeleteView.as_view(), name='sensor-class-property-delete'),
]