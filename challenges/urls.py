from django.urls import path

from .views import *

urlpatterns = [
    path('<int:event_id>', EventChallengesListView.as_view(), name='event-challenge-list'), # TODO: Add event/...
    path('new/<int:event_id>', ChallengeCreateView.as_view(), name='challenge-create'),
    path('detail/<int:challenge_id>', ChallengeDetailView.as_view(), name='challenge-detail'),
    path('delete/<int:challenge_id>', ChallengeDeleteView.as_view(), name='challenge-delete'), # TODO: /detail/.../delete ?
    # path('update/<int:pk>', ChallengeUpdateView.as_view(), name='challenge-update'),
]
