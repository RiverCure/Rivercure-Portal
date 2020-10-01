from django.urls import path, include
from .views import GrantAccess, ContextRequestDecisionView, show_context, download_context, simulation_results, request_pre_processing, ContextViewSet, UploadContext, EventCreateView, EventUpdateView, EventListView,EventDetailView, ContextSensorListView, ContextAccessCreateView, ContextListView, ContextDetailView, OtherContextListView, ContextRequestListView
from rest_framework import routers
 
router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', ContextListView, name='context-list'),
    path('others/', OtherContextListView, name='other-contexts'),
    path('<str:pk>', ContextDetailView.as_view(), name='context-detail'),
    path('manage/', show_context, name='context_manage'),
    path('upload/<str:pk>', UploadContext.as_view(), name='context_upload'),
    path('download/<str:context_code>', download_context, name='download_context'),
    path('request_simulation/<str:context_code>', request_pre_processing, name='context-simulation-request'),
    path('simulation_results/', simulation_results, name='context-simulation-results'),
    path('api/', include(router.urls)),
    path('events/', EventListView, name='event-list'),
    path('context-sensors/', ContextSensorListView, name='context-sensor-list'),
    path('events/<int:pk>', EventDetailView.as_view(), name='event-detail'),
    path('context_requests/', ContextRequestListView.as_view(), name='context-requests-list'), 
    path('context_request/<int:pk>', ContextRequestDecisionView, name='context-request-decision'),
    path('events/', EventListView, name='event-list'),
    path('events/new/', EventCreateView.as_view(), name='event-create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event-update'),
    path('access_granted/<int:pk>', GrantAccess, name='access-granted'),
    path('context_request_create/', ContextAccessCreateView.as_view(), name='context-requests-create'),
]
