from django.urls import path, include
from . import views 
from rest_framework import routers
from .views import (
    EventListView,
    EventDetailView,
    ContextSensorListView
) 

router = routers.DefaultRouter()
router.register(r'context', views.ContextViewSet)

urlpatterns = [
    path('', views.show_context, name='context'),
    path('api/', include(router.urls)),
    path('events/', views.EventListView, name='event-list'),
    path('context-sensors/', ContextSensorListView, name='context-sensor-list'),
    path('events/<int:pk>', EventDetailView.as_view(), name='event-detail'),
]