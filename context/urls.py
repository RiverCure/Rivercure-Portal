from django.urls import path, include
from .views import GrantAccess, ContextRequestDecisionView, show_context, download_context, ContextViewSet, UploadContext, EventListView,EventDetailView, ContextSensorListView, ContextListView, ContextDetailView, OtherContextListView, ContextRequestListView
from rest_framework import routers
 
router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', ContextListView, name='context-list'),
    path('others/', OtherContextListView, name='other-contexts'),
    path('<str:pk>', ContextDetailView.as_view(), name='context-detail'),
    path('manage/', show_context, name='context_manage'),
    path('upload/', UploadContext.as_view(), name='context_upload'),
    path('download/<str:context_code>', download_context, name='download_context'),
    path('api/', include(router.urls)),
    path('events/', EventListView, name='event-list'),
    path('context-sensors/', ContextSensorListView, name='context-sensor-list'),
    path('events/<int:pk>', EventDetailView.as_view(), name='event-detail'),
    path('context_requests/', ContextRequestListView.as_view(), name='context-requests-list'), 
    path('context_request/<int:pk>', ContextRequestDecisionView, name='context-request-decision'),
    path('events/', EventListView, name='event-list'),
    path('context_requests/', GrantAccess, name='access-granted'),
]