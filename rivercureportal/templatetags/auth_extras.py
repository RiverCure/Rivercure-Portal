from django import template
from django.contrib.auth.models import Group 

from organization.models import Membership
from context.models import ContextMembership

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name): 
    group = Group.objects.get(name=group_name) 
    return True if group in user.groups.all() else False

# Check if user belongs to any organization
@register.filter(name="has_org")
def has_org(user):
    return Membership.objects.filter(user=user).exists()

# Check if user is a moderator (in whatever context)
@register.filter(name='is_mod')
def is_mod(user):
    return ContextMembership.objects.filter(user=user, permission='context_moderator').exists()