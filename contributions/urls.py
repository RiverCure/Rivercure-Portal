from django.urls import path

from .views import *

urlpatterns = [
    path('', ContributionListView.as_view(), name='contribution-list'),
    path('new/', ContributionCreateView.as_view(), name='contribution-create')
]