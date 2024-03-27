# Checks if the user is a manager or contextManager on any organization. If so, he can add contexts (from which organization is seen in the create view)
from organization.models import Membership
from django.db.models import Q
from context.models import ContextMembership

def context_general_create_permission_check(user):
    """
    Checks if the user is an org manager or a context manager of any organization?
    """
    try:
        return Membership.objects.filter(user=user, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager')).exists()
    except:
        return False

def context_general_event_create_permission_check(user):
    """
    Checks if the user is an org manager or a context manager or an event manager of any organization?
    """
    try:
        return Membership.objects.filter(user=user, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager') | Q(permission='org_eventManager')).exists()
    except:
        return False

def context_organization_edit_permission_check(user, organization):
    """
    Checks if the user is a manager or contextManager of an organization
    """

    try:
        return Membership.objects.filter(user=user, organization=organization, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager')).exists()
    except:
        return False

def context_organization_event_permission_check(user, organization):
    """
    Checks if the user is a manager or eventManager of an organization
    """

    try:
        return Membership.objects.filter(user=user, organization=organization, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_contextManager') | Q(permission='org_eventManager')).exists()
    except:
        return False

def context_organization_belong_check(user, organization):
    """
    Checks if the user belongs to an organization
    """
    
    try:
        return Membership.objects.filter(user=user, organization=organization).exists()
    except:
        return False

# TODO: Check if this works
def context_event_manager_check(user, context):
    """
    Checks if the user is an event manager of a context
    """
    try:
        return ContextMembership.objects.filter(user=user, context=context, permission='context_eventManager').exists()
    except:
        return False

# TODO: Check if this works
def context_moderator_check(user, context):
    """
    Checks if user is a moderator of a context
    """
    try:
        return ContextMembership.objects.filter(user=user, context=context, permission='context_moderator').exists()
    except:
        return False


def general_moderator_check(user):
    """
    Checks if the user is a moderator
    """
    try:
        return ContextMembership.objects.filter(user=user, permission='context_moderator').exists()
    except:
        return False