from django.urls import path, include
from .views import (
    OrganizationListView,
    OrganizationCreateView,
    OrganizationDetailView,
    OrganizationUpdateView,
    OrganizationDeleteView,
    OrganizationManageView,
    MemberRoleUpdateView,
    organizationAccessRequest,
    organizationAccessRequestCancel,
    organizationAccessRequestDeny,
    organizationAccessRemove,
    organizationAccessAllow
)

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('new/', OrganizationCreateView.as_view(), name='organization-create'),
    path('<int:pk>', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<int:pk>/update/', OrganizationUpdateView.as_view(), name='organization-update'),
    path('<int:pk>/delete/', OrganizationDeleteView.as_view(), name='organization-delete'),
    path('<int:pk>/manage/', OrganizationManageView.as_view(), name='organization-manage'),
    path('<int:pk>/update/member/', MemberRoleUpdateView.as_view(), name='organization-member-role-update'),
    path('<int:pk>/request/', organizationAccessRequest, name='organization-access-request'),
    path('<int:pk>/request/cancel/', organizationAccessRequestCancel, name='organization-access-request-cancel'),
    path('<int:pk1>/manage/<int:pk2>/deny/', organizationAccessRequestDeny, name='organization-access-request-deny'),
    path('<int:pk1>/manage/<int:pk2>/remove/', organizationAccessRemove, name='organization-access-remove'),
    path('<int:pk1>/manage/<int:pk2>/allow/', organizationAccessAllow, name='organization-access-allow')
]