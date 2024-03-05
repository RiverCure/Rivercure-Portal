from django.urls import path

from .views import *

urlpatterns = [
    path('', AllContributionsListView.as_view(), name='all-contributions-list'),
    path('new/', ContributionCreateView.as_view(), name='contribution-create'),
    path('<str:contextCode>', ContributionListView.as_view(), name='contribution-list'),
    path('detail/<str:contributionId>', ContributionDetailView.as_view(), name='contribution-detail'),
]