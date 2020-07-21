from django.urls import path
from . import views 
from .views import (
    SensorListView
)

urlpatterns = [
    path('sensors/', SensorListView.as_view(), name='sensor-list')
]