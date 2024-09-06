from django.urls import path

from .views import *

urlpatterns = [
    path('new/<str:contextCode>/', ContributionCreateView.as_view(), name='contribution-create'),
    path('<str:contributionId>/detail', ContributionDetailView.as_view(), name='contribution-detail'),
    path('<str:contributionId>/accept/', contributionAccept, name='moderator-contribution-accept'),
    path('<str:contributionId>/reject/', contributionReject, name='moderator-contribution-reject'),
    path('<str:contributionId>/delete/', ContributionDeleteView.as_view(), name='contribution-delete'),
    path('<str:contributionId>/report/', contributionReport, name='contribution-report'),
    path('context/<str:contextCode>/', ContributionFilterView.as_view(), name='contribution-list'),
    path('mine/', MyContributionsFilterView.as_view(), name='my-contributions'),
]