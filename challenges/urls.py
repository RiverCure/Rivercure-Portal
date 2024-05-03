from django.urls import path

from .views import *

urlpatterns = [
    path('mine/', MyContextsChallengesFilterView.as_view(), name='my-contexts-challenges-list'),
    path('event/<int:event_id>/new/', ChallengeCreateView.as_view(), name='challenge-create'),
    path('detail/<int:challenge_id>/', ChallengeDetailView.as_view(), name='challenge-detail'),
    path('delete/<int:challenge_id>/', ChallengeDeleteView.as_view(), name='challenge-delete'), # TODO: /detail/.../delete ?
    # path('update/<int:pk>', ChallengeUpdateView.as_view(), name='challenge-update'),
]
