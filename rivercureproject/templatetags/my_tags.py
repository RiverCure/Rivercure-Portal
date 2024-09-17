# <app>/templatetags/my_tags.py
from django import template

from contributions.models import e_ContextContribution, ContributionStatus

register = template.Library()

# Based on: https://cheat.readthedocs.io/en/latest/django/filter.html
@register.simple_tag
def url_replace (request, field, value):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    dict_ = request.GET.copy()
    dict_[field] = value

    return dict_.urlencode()  


# Get number of pending contributions
@register.filter(name='get_pending')
def get_pending(contributions):
    pending = contributions.filter(state=ContributionStatus.PENDING).count()
    return str(pending)

# Get number of accepted contributions
@register.filter(name='get_accepted')
def get_accepted(contributions):
    accepted = contributions.filter(state=ContributionStatus.ACCEPTED).count()
    return accepted


@register.filter(name='get_state_color')
def get_state_color(state):
    """
    Returns Bootstrap class for color depending on Contribution state
    """
    if state == ContributionStatus.PENDING:
        return 'warning'
    elif state == ContributionStatus.ACCEPTED:
        return 'success'
    else:
        return 'danger'

@register.filter(name='is_active')
def is_active(isFirst):
    """
    Returns class 'active' if element is first in Bootstrap Carousel.

    isFirst: bool that says whether this element is the first in a list
    """
    if isFirst:
        return 'active'

@register.filter(name='get_state_icon')
def get_state_icon(state):
    """
    Returns Bootstrap class for icon depending on Contribution state
    """
    if state == ContributionStatus.PENDING:
        return 'hourglass-split'
    elif state == ContributionStatus.ACCEPTED:
        return 'check-circle'
    else:
        return 'x-circle'