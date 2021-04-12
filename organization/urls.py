from django.urls import path, include
from .views import (
    OrganizationListView,
    OrganizationCreateView,
    OrganizationDetailView,
    OrganizationUpdateView,
    OrganizationDeleteView,
    OrganizationManageView,
    organizationAccessRequest,
    organizationAccessRequestCancel,
    organizationAccessRequestDeny,
    organizationAccessRemove,
    organizationAccessAllow
)

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('new/', OrganizationCreateView.as_view(), name='organization-create'),
    path('<str:pk>', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<str:pk>/update/', OrganizationUpdateView.as_view(), name='organization-update'),
    path('<str:pk>/delete/', OrganizationDeleteView.as_view(), name='organization-delete'),
    path('<str:pk>/manage/', OrganizationManageView.as_view(), name='organization-manage'),
    path('<str:pk>/request/', organizationAccessRequest, name='organization-access-request'),
    path('<str:pk>/request/cancel/', organizationAccessRequestCancel, name='organization-access-request-cancel'),
    path('<str:pk1>/manage/<str:pk2>/deny/', organizationAccessRequestDeny, name='organization-access-request-deny'),
    path('<str:pk1>/manage/<str:pk2>/remove/', organizationAccessRemove, name='organization-access-remove'),
    path('<str:pk1>/manage/<str:pk2>/allow/', organizationAccessAllow, name='organization-access-allow')
]