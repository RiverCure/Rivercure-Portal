from django.urls import path

from .views import *

urlpatterns = [
    # Challenges
    path('mine/', MyContextsChallengesFilterView.as_view(), name='my-contexts-challenges-list'),
    path('event/<int:event_id>/new/', ChallengeCreateView.as_view(), name='challenge-create'),
    path('detail/<int:challenge_id>/', ChallengeDetailView.as_view(), name='challenge-detail'),
    path('update/<int:challenge_id>/', ChallengeUpdateView.as_view(), name='challenge-update'),
    path('delete/<int:challenge_id>/', ChallengeDeleteView.as_view(), name='challenge-delete'),
    path('manage/<int:challenge_id>/', ChallengeManageView.as_view(), name='challenge-manage'),
    # Questions
    # path('questions/<int:challenge_id>/new/', QuestionCreateView.as_view(), name='question-add'), # TODO: <int:challenge_id>/questions/new/
    path('questions/<int:challenge_id>/new/', question_create, name='question-add'), # TODO: <int:challenge_id>/questions/new/
    path('questions/<int:question_id>/update/', QuestionUpdateView.as_view(), name='question-update'),
    path('questions/<int:question_id>/short-text/new', questionShortTextCreate, name='question-short-text-add'),

    # path('participate/<int:challenge_id>/', ?, name='challenge-participate'),
]
