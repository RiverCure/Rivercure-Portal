# <app>/templatetags/my_tags.py
from django import template

register = template.Library()

# TODO: make these 3 functions prettier
@register.simple_tag
def is_active(url, tab):
    if (tab  == 'map'):
        if (url == '/pt/contexts/public/'):
            return 'active'
        else:
            return ''
    else:
        if (url == '/pt/contexts/public/'):
            return ''
        else:
            return 'active'

@register.simple_tag
def is_show(url, tab):
    if (tab  == 'map'):
        if (url == '/pt/contexts/public/'):
            return 'show'
        else:
            return ''
    else:
        if (url == '/pt/contexts/public/'):
            return ''
        else:
            return 'show'

@register.simple_tag
def is_hidden(url):
    if (url == '/pt/contexts/public/'):
        return 'hidden'
    return ''