from django.urls import path, include
from rest_framework import routers
from .views import (
    ContextUpdateView,
    ContextAccessRequestCreate, ContextRequestDecisionView, ContextRequestListView, 
    GrantAccess, DenyAccess, 
    ContextEventListView, 
    manage_context, download_context, preprocessing_results, request_pre_processing, download_preprocessing_results,
    ContextViewSet, 
    UploadContext, 
    EventCreateView, EventUpdateView, EventDetailView, 
    ContextSensorListView, 
    ContextListView, ContextDetailView, ContextCreateView, ContextDeleteView, OtherContextListView, 
    mesh_status_change, download_simulation_results, handle_simulation_results, view_events_results, runsimulationview, inform_mesh_status
) 

router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', ContextListView, name='context-list'),
    path('new/', ContextCreateView.as_view(), name='context-create'),
    path('others/', OtherContextListView, name='other-contexts'),
    path('<str:pk>', ContextDetailView.as_view(), name='context-detail'),
    path('<str:pk>/update/', ContextUpdateView.as_view(), name='context-update'),
    path('<str:pk>/delete/', ContextDeleteView.as_view(), name='context-delete'),
    path('manage/<str:context_code>', manage_context, name='context_manage'),
    path('upload/<str:pk>', UploadContext.as_view(), name='context_upload'),
    path('download/<str:context_code>', download_context, name='download_context'),
    path('request_preprocessing/<str:context_code>', request_pre_processing, name='context-preprocessing-request'),
    path('preprocessing_results/', preprocessing_results, name='context-preprocessing-results'),
    path('preprocessing_results/download/<str:context_code>', download_preprocessing_results, name='context-preprocessing-results-download'),
    path('mesh-status/<str:context_name>', mesh_status_change, name='mesh-status-change'),
    path('mesh-status/request/<str:context_code>', inform_mesh_status, name='mesh-status-request'),
    path('simulation/results/<int:event_id>', view_events_results, name='view-simulation-results'),
    path('simulation/results/download/<int:event_id>', download_simulation_results, name='simulation-results-download'),
    path('simulation/results/handle/<int:event_id>', handle_simulation_results, name='handle-simulation-results'),
    path('api/', include(router.urls)),
    path('context-sensors/', ContextSensorListView, name='context-sensor-list'),
    path('events/<int:pk>', EventDetailView.as_view(), name='event-detail'),
    path('events/run/<int:event_id>', runsimulationview, name='event-run'),
    path('context_requests/', ContextRequestListView.as_view(), name='context-requests-list'), 
    path('context_request/<int:pk>', ContextRequestDecisionView, name='context-request-decision'),
    path('events/list/<str:context_code>', ContextEventListView, name='context-event-list'),
    path('events/new/', EventCreateView.as_view(), name='event-create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event-update'),
    path('access_granted/<int:pk>', GrantAccess, name='access-granted'),
    path('access_denied/<int:pk>', DenyAccess, name='access-denied'),
    path('context_request_create/<str:context_code>', ContextAccessRequestCreate, name='context-request-create'),
]
