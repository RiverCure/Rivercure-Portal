from django.urls import path

from .views import *

urlpatterns = [
    # TODO: Add / to end of URLs
    path('', AllContributionsListView.as_view(), name='all-contributions-list'),
    path('new/<str:contextCode>', ContributionCreateView.as_view(), name='contribution-create'),
    path('<str:contributionId>/detail', ContributionDetailView.as_view(), name='contribution-detail'),
    path('<str:contributionId>/detail/accept', contributionAccept, name='moderator-contribution-accept'), # TODO: Remove /detail/
    path('<str:contributionId>/detail/reject', contributionReject, name='moderator-contribution-reject'), # TODO: Remove /detail/
    path('<str:contributionId>/delete', ContributionDeleteView.as_view(), name='contribution-delete'),
    path('<str:contributionId>/report', contributionReport, name='contribution-report'),
    path('context/<str:contextCode>', ContributionListView.as_view(), name='contribution-list'), # TODO: /context/<str:contextCode>/contributions/
    path('mine', MyContributionsListView.as_view(), name='my-contributions'),
]