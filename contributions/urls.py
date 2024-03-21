from django.urls import path

from .views import *

urlpatterns = [
    path('', AllContributionsListView.as_view(), name='all-contributions-list'),
    path('new/<str:contextCode>', ContributionCreateView.as_view(), name='contribution-create'),
    path('<str:contributionId>/detail', ContributionDetailView.as_view(), name='contribution-detail'),
    path('<str:contributionId>/delete', ContributionDeleteView.as_view(), name='contribution-delete'),
    path('context/<str:contextCode>', ContributionListView.as_view(), name='contribution-list'), # TODO: URL good like this?
    path('mine', MyContributionsListView.as_view(), name='my-contributions'),
]