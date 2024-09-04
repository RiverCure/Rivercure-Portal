# <app>/templatetags/my_tags.py
from django import template

register = template.Library()

@register.simple_tag
def is_active(url, tab):
    if (tab  == 'map'):
        if (url[3:]  == '/contexts/public/'):
            return 'active'
        else:
            return ''
    else:
        if (url[3:]  == '/contexts/public/'):
            return ''
        else:
            return 'active'


@register.simple_tag
def is_show(url, tab):
    if (tab  == 'map'):
        if (url[3:]  == '/contexts/public/'):
            return 'show'
        return ''
    else:
        if (url[3:]  == '/contexts/public/'):
            return ''
        return 'show'
    

@register.simple_tag
def is_hidden(url):
    if (url[3:]  == '/contexts/public/'):
        return 'hidden'
    return ''
    # if (url == '/pt/contexts/public/' or url == '/en/contexts/public/'):