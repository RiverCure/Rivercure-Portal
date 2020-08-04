from django.urls import path, include
from .views import show_context, download_context, ContextViewSet, UploadContext, EventListView,EventDetailView, ContextSensorListView, ContextListView, ContextDetailView
from rest_framework import routers
 
router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', ContextListView.as_view(), name='context-list'),
    path('<str:pk>', ContextDetailView.as_view(), name='context-detail'),
    path('manage/', show_context, name='context_manage'),
    path('upload/', UploadContext.as_view(), name='context_upload'),
    path('download/<str:context_code>', download_context, name='download_context'),
    path('api/', include(router.urls)),
    path('events/', EventListView, name='event-list'),
    path('context-sensors/', ContextSensorListView, name='context-sensor-list'),
    path('events/<int:pk>', EventDetailView.as_view(), name='event-detail'),
]