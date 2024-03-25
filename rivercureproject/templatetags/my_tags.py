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

@register.filter(name='get_progress')
def get_progress(contributions):
    total = contributions.count()
    completed = contributions.exclude(state='PENDING').count()

    if total == 0:
            return '0'
        
    progress = round((completed * 100) / total)

    return str(progress)

@register.filter(name='get_completed')
def get_completed(contributions):
    completed = contributions.exclude(state='PENDING').count()
    return str(completed)