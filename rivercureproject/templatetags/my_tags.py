# <app>/templatetags/my_tags.py
from django import template

register = template.Library()

# Based on: https://cheat.readthedocs.io/en/latest/django/filter.html
@register.simple_tag
def url_replace (request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value

    return dict_.urlencode()  