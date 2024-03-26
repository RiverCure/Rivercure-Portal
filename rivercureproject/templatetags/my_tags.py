# <app>/templatetags/my_tags.py
from django import template

from contributions.models import e_ContextContribution

register = template.Library()

# Based on: https://cheat.readthedocs.io/en/latest/django/filter.html
@register.simple_tag
def url_replace (request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value

    return dict_.urlencode()  

# Get progress (that is, how many contributions have been validated) in percentage
@register.filter(name='get_progress')
def get_progress(contributions):
    total = contributions.count()
    validated = contributions.exclude(state='PENDING').count()

    if total == 0:
            return '0'
        
    progress = round((validated * 100) / total)

    return str(progress)

# Get number of validated contributions
@register.filter(name='get_validated')
def get_validated(contributions):
    completed = contributions.exclude(state='PENDING').count()
    return str(completed)

# Return Bootstrap class for text color depending on contribution state
@register.filter(name='get_state_color')
def get_state_color(state):
    if state == 'PENDING':
        return 'text-warning'
    elif state == 'ACCEPTED':
        return 'text-success'
    else:
        return 'text-danger'