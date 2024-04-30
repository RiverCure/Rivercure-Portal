from django.urls import path

from .views import *

urlpatterns = [
    path('<int:event_id>', EventChallengesListView.as_view(), name='challenge-list'),
    path('new/<int:event_id>', ChallengeCreateView.as_view(), name='challenge-create'),
]
