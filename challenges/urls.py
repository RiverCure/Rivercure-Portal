from django.urls import path

from .views import *

urlpatterns = [
    path('<int:event_id>', ChallengesListView.as_view(), name='challenge-list'),
]
