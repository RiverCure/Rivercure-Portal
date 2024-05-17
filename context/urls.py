from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'context', ContextViewSet)

urlpatterns = [
    path('', ContextListView.as_view(), name='context-list'),
    path('new/', ContextCreateView.as_view(), name='context-create'),
    path('public/', PublicContextListView.as_view(), name='public-contexts'),
    path('public/<str:contextCode>', PublicContextDetailView.as_view(), name='public-context-detail'),
    path('<str:contextCode>', ContextDetailView.as_view(), name='context-detail'),
    path('<str:contextCode>/update/', ContextUpdateView.as_view(), name='context-update'),
    path('<str:contextCode>/delete/', ContextDeleteView.as_view(), name='context-delete'),
    path('<str:contextCode>/manage/', manage_context, name='context_manage'),
    path('<str:contextCode>/upload/', UploadContext.as_view(), name='context_upload'),
    path('<str:contextCode>/download/', download_context, name='download_context'),
    path('<str:contextCode>/request_preprocessing/', request_pre_processing, name='context-preprocessing-request'),
    path('<str:contextCode>/preprocessing_results/download/',
         download_preprocessing_results, name='context-preprocessing-results-download'),
    path('preprocessing_results/', preprocessing_results, name='context-preprocessing-results'),
    # Moderator
    path('moderators/my-contexts/', ModeratorContextsListView.as_view(), name='moderator-context-list'),
    path('<str:contextCode>/moderators', ModeratorListView.as_view(), name='moderator-list'),
    path('<str:contextCode>/moderators/contributions', ModeratorContextContributionListView.as_view(), name='moderator-context-contribution-list'), # TODO: Should I just reuse the already existing page with contribution list of a context? aka contribution-list
    path('<str:contextCode>/moderators/add/', ModeratorAddListView.as_view(), name='moderator-list-add'),
    path('<str:contextCode>/moderators/<int:userId>/add/', contextModeratorAdd, name='moderator-user-add'),
    path('<str:contextCode>/moderators/<int:userId>/remove/', contextModeratorRemove, name='moderator-remove'),
    path('<str:contextCode>/moderators/batch-handle/', batchHandle, name='contribution-batch-handle'),
    # Mesh progress
    path('mesh-status/<str:contextCode>', mesh_status, name='mesh-status'),
    path('mesh-status/<str:contextCode>/progress', mesh_status_progress, name='mesh-status-progress'),
    path('mesh-status/<str:contextCode>/regenerate-confirm', regenerate_mesh_confirm, name='mesh-regenerate-confirm'),
    path('mesh-status/<str:contextCode>/cancel-confirm', cancel_mesh_confirm, name='mesh-cancel-confirm'),
    path('mesh-status/<str:contextCode>/request', inform_mesh_status, name='mesh-status-request'),
    path('<str:contextCode>/cancel', cancel_mesh, name='mesh-cancel'),
    # Event simulation
    path('simulation/results/<int:event_id>', view_events_results, name='view-simulation-results'),
    path('simulation/results/download/<int:event_id>', download_simulation_results, name='simulation-results-download'),
    path('simulation/results/handle/<int:event_id>', handle_simulation_results, name='handle-simulation-results'),
    path('api/', include(router.urls)),
    path('<str:contextCode>/sensors/', ContextSensorListView.as_view(), name='context-sensor-list'),
    # Events
    path('<str:pk>/events/<int:event_id>', EventDetailView.as_view(), name='event-detail'),
    path('<str:pk>/events/<int:event_id>/challenges/', EventChallengesFilterView.as_view(), name='event-challenge-list'),
    path('<str:pk>/events/<int:event_id>/run/', request_simulation, name='event-run'),
    path('<str:contextCode>/events/', ContextEventListView.as_view(), name='event-list'),
    path('<str:contextCode>/events/managers/', ContextEventManagersListView.as_view(), name='event-manager-list'),
    path('<str:contextCode>/events/managers/add/', ContextEventManagerAddListView.as_view(), name='event-manager-list-add'),
    path('<str:contextCode>/events/managers/add/<int:userId>/', contextEventManagerAdd, name='event-manager-add'),
    path('<str:contextCode>/events/managers/remove/<int:userId>/', contextEventManagerRemove, name='event-manager-remove'),
    path('<str:pk>/events/new/', EventCreateView.as_view(), name='event-create'),
    path('<str:pk>/event/<int:event_id>/update/', EventUpdateView.as_view(), name='event-update'),
    path('<str:pk>/event/<int:event_id>/cancel/', cancel_simulation, name='event-cancel'),
    # Event progress
    path('event-status/<str:event_id>', event_progress, name='event-progress'),
    path('event-status/<str:event_id>/progress', event_status_progress, name='event-status-progress'),
    path('event-status/<str:event_id>/regenerate-confirm', regenerate_event_confirm, name='event-regenerate-confirm'),
    path('event-status/<str:event_id>/cancel-confirm', cancel_event_confirm, name='event-cancel-confirm'),
    path('event-status/<str:event_id>/request', inform_event_status, name='event-status-request'),
    # Event Managers
    path('event-managers/my-contexts/', EventManagerContextsListView.as_view(), name='event-manager-context-list'),
    path('event-managers/my-challenges/', MyContextsChallengesFilterView.as_view(), name='my-contexts-challenges-list'), # TODO: MOVE THIS TO CONTEXT APP!
]
