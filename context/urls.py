from django.urls import path, include
from .views import GrantAccess, ContextRequestDecisionView, ContextEventListView, show_context, download_context, preprocessing_results, request_pre_processing, ContextViewSet, UploadContext, EventCreateView, EventUpdateView, EventListView,EventDetailView, ContextSensorListView, ContextAccessCreateView, ContextListView, ContextDetailView, OtherContextListView, ContextRequestListView, mesh_status_change, download_simulation_results
from rest_framework import routers
 
router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', ContextListView, name='context-list'),
    path('others/', OtherContextListView, name='other-contexts'),
    path('<str:pk>', ContextDetailView.as_view(), name='context-detail'),
    path('manage/<str:context_code>', show_context, name='context_manage'),
    path('upload/<str:pk>', UploadContext.as_view(), name='context_upload'),
    path('download/<str:context_code>', download_context, name='download_context'),
    path('request_preprocessing/<str:context_code>', request_pre_processing, name='context-preprocessing-request'),
    path('preprocessing_results/', preprocessing_results, name='context-preprocessing-results'),
    path('mesh-status/<str:context_name>', mesh_status_change, name='mesh-status-change'),
    path('simulation/results/download/<int:event_id>', download_simulation_results, name='simulation-results-download'),
    path('api/', include(router.urls)),
    path('context-sensors/', ContextSensorListView, name='context-sensor-list'),
    path('events/<int:pk>', EventDetailView.as_view(), name='event-detail'),
    path('context_requests/', ContextRequestListView.as_view(), name='context-requests-list'), 
    path('context_request/<int:pk>', ContextRequestDecisionView, name='context-request-decision'),
    path('events/', EventListView, name='event-list'),
    path('events/list/<str:context_code>', ContextEventListView, name='context-event-list'),
    path('events/new/', EventCreateView.as_view(), name='event-create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event-update'),
    path('access_granted/<int:pk>', GrantAccess, name='access-granted'),
    path('context_request_create/', ContextAccessCreateView.as_view(), name='context-requests-create'),
]
