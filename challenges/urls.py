from django.urls import path

from .views import *

urlpatterns = [
    # Challenges
    path('event/<int:event_id>/new/', ChallengeCreateView.as_view(), name='challenge-event-create'),
    path('context/<str:context_id>/new/', ChallengeContextCreateView.as_view(), name='challenge-context-create'),
    path('context/<str:context_id>/all/', ChallengeContextFilterView.as_view(), name='challenges-context-list'),
    #path('context/<str:context_id>/all/', context_challenges_list, name='challenge-context-all'),
    path('<int:challenge_id>/detail/', ChallengeDetailView.as_view(), name='challenge-detail'),
    path('<int:challenge_id>/update/', ChallengeUpdateView.as_view(), name='challenge-update'),
    path('<int:challenge_id>/delete/', ChallengeDeleteView.as_view(), name='challenge-delete'),
    path('<int:challenge_id>/manage/', ChallengeManageView.as_view(), name='challenge-manage'),
    path('<int:challenge_id>/publish/', challenge_publish, name='challenge-publish'),
    path('<int:challenge_id>/open/', challenge_open, name='challenge-open'),
    path('<int:challenge_id>/close/', challenge_close, name='challenge-close'),
    path('<int:challenge_id>/archive/', challenge_archive, name='challenge-archive'),
    # Participations
    path('<int:challenge_id>/participate/', challenge_participate, name='challenge-participate'),
    path('<int:challenge_id>/participations/all/', ChallengeParticipationsFilterView.as_view(), name='challenge-all-participations'),
    path('<int:challenge_id>/participations/mine/', MyChallengeParticipationsFilterView.as_view(), name='challenge-my-participations'),
    path('participations/<int:participation_id>/', ParticipationDetailView.as_view(), name='participation-detail'),
    # Questions
    path('<int:challenge_id>/questions/new/', question_create, name='question-add'),
    path('questions/<int:question_id>/delete/', question_delete, name='question-delete'),
    path('questions/<int:question_id>/update/', question_update, name='question-update'),
    path('questions/<int:question_id>/position-up/', question_position_up, name='question-position-up'),
    path('questions/<int:question_id>/position-down/', question_position_down, name='question-position-down'),
    path('questions/<int:option_id>/multiple-choice-option/delete', multiple_choice_option_delete, name='multiple-choice-option-delete'),
    path('questions/<int:option_id>/true-false-option/delete', true_false_option_delete, name='true-false-option-delete'),
]
