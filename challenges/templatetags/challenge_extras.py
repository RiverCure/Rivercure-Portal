from django import template

from challenges.models import ChallengeState, ChallengePublishState

register = template.Library()

@register.filter(name="bootstrap_badge_state")
def bootstrap_badge_state(state):
    """
    Returns Bootstrap CSS badge class according to the given state
    """
    if state == ChallengeState.DRAFT:
        return 'badge-secondary'
    elif state == ChallengeState.PUBLISHED:
        return 'badge-info'
    elif state == ChallengeState.ARCHIVED:
        return 'badge-warning'
    else:
        return 'badge-secondary'
    
@register.filter(name="bootstrap_badge_publish_state")
def bootstrap_badge_publish_state(state):
    """
    Returns Bootstrap CSS badge class according to the given PUBLISH sub-state
    """
    if state == ChallengePublishState.OPEN:
        return 'badge-info'
    else:
        return 'badge-warning'