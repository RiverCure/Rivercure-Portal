from django.urls import path, include
from rest_framework import routers
from .views import (
    ContextUpdateView,
    ContextEventListView, 
    manage_context, download_context, preprocessing_results, request_pre_processing, download_preprocessing_results,
    ContextViewSet, 
    UploadContext, 
    EventCreateView, EventUpdateView, EventDetailView, 
    ContextSensorListView, 
    ContextListView, ContextDetailView, ContextCreateView, ContextDeleteView, OtherContextListView, 
    mesh_status_change, download_simulation_results, handle_simulation_results, view_events_results, runsimulationview, inform_mesh_status
) 
from context.views import mesh_progress, mesh_status_progress, regenerate_mesh_confirm
from context.views.event import event_progress, event_status_change, event_status_progress, inform_event_status, regenerate_event_confirm

router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', ContextListView.as_view(), name='context-list'),
    path('new/', ContextCreateView.as_view(), name='context-create'),
    path('others/', OtherContextListView.as_view(), name='other-contexts'),
    path('<str:contextCode>', ContextDetailView.as_view(), name='context-detail'),
    path('<str:contextCode>/update/', ContextUpdateView.as_view(), name='context-update'),
    path('<str:contextCode>/delete/', ContextDeleteView.as_view(), name='context-delete'),
    path('manage/<str:contextCode>', manage_context, name='context_manage'),
    path('upload/<str:pk>', UploadContext.as_view(), name='context_upload'),
    path('download/<str:context_code>', download_context, name='download_context'),
    path('request_preprocessing/<str:contextCode>', request_pre_processing, name='context-preprocessing-request'),
    path('preprocessing_results/', preprocessing_results, name='context-preprocessing-results'),
    path('preprocessing_results/download/<str:context_code>', download_preprocessing_results, name='context-preprocessing-results-download'),
    # Mesh progress
    path('mesh-status/progress/<str:context_name>', mesh_status_progress, name='mesh-status-progress'),
    path('mesh-status/<str:context_name>', mesh_status_change, name='mesh-status-change'),
    path('<str:context_code>/regenerate-mesh-confirm/', regenerate_mesh_confirm, name='mesh-regenerate-confirm'),
    path('mesh-status/request/<str:context_code>', inform_mesh_status, name='mesh-status-request'),
    path('<str:context_code>/mesh-progress/', mesh_progress, name='mesh-progress'),

    path('simulation/results/<int:event_id>', view_events_results, name='view-simulation-results'),
    path('simulation/results/download/<int:event_id>', download_simulation_results, name='simulation-results-download'),
    path('simulation/results/handle/<int:event_id>', handle_simulation_results, name='handle-simulation-results'),
    path('api/', include(router.urls)),
    path('<str:contextCode>/sensors/', ContextSensorListView.as_view(), name='context-sensor-list'),
    path('<str:pk>/events/<int:event_id>', EventDetailView.as_view(), name='event-detail'),
    path('<str:pk>/events/<int:event_id>/run/', runsimulationview, name='event-run'),
    path('<str:contextCode>/events/', ContextEventListView.as_view(), name='context-event-list'),
    path('<str:pk>/events/new/', EventCreateView.as_view(), name='event-create'),
    path('<str:pk>/event/<int:event_id>/update/', EventUpdateView.as_view(), name='event-update'),
    # Event progress
    path('event-status/progress/<str:event_id>', event_status_progress, name='event-status-progress'),
    path('event-status/<str:event_id>', event_status_change, name='event-status-change'),
    path('<str:event_id>/regenerate-event-confirm/', regenerate_event_confirm, name='event-regenerate-confirm'),
    path('event-status/request/<str:event_id>', inform_event_status, name='event-status-request'),
    path('<str:event_id>/event-progress/', event_progress, name='event-progress'),
]
