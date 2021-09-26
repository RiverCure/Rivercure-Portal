from django.urls import path, include
from .views import *

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('new/', OrganizationCreateView.as_view(), name='organization-create'),
    path('<int:organizationId>', OrganizationDetailView.as_view(), name='organization-detail'),
    path('<int:organizationId>/update/', OrganizationUpdateView.as_view(), name='organization-update'), 
    path('<int:organizationId>/manage/', OrganizationManageView.as_view(), name='organization-manage'),
    path('<int:organizationId>/manage/managers/', OrganizationManageManagersView.as_view(), name='organization-manage-managers'),
    path('<int:membershipId>/update/member/', MemberRoleUpdateView.as_view(), name='organization-member-role-update'),
    path('<int:organizationId>/request/', organizationAccessRequest, name='organization-access-request'),
    path('<int:organizationId>/request/cancel/', organizationAccessRequestCancel, name='organization-access-request-cancel'),
    path('<int:organizationId>/manage/<int:userId>/deny/', organizationAccessRequestDeny, name='organization-access-request-deny'),
    path('<int:organizationId>/manage/<int:userId>/remove/', organizationAccessRemove, name='organization-access-remove'),
    path('<int:organizationId>/manage/<int:userId>/allow/', organizationAccessAllow, name='organization-access-allow'),
    path('<int:organizationId>/reactivate/', organizationReactivate, name='organization-reactivate'),
    path('<int:organizationId>/suspend/', organizationSuspend, name='organization-suspend'),
    path('<int:organizationId>/set-current', organizationSetCurrent, name='organization-set-current')
]