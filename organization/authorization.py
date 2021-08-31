from organization.models import Membership, Organization
from django.contrib.auth.models import User


def is_org_manager(obj):
    try:
        organization_id = obj.kwargs.get('pk')
        return Membership.objects.filter(organization_id=organization_id, user=obj.request.user, permission='org_manager').exists()
    except:
        return False

def is_sensor_manager(obj):
    try:
        organization_id = obj.kwargs.get('pk')
        return Membership.objects.filter(organization_id=organization_id, user=obj.request.user, permission='org_sensorManager').exists()
    except:
        return False

def is_org_manager_check(user, organization_id):
    try:
        return Membership.objects.filter(organization_id=organization_id, user=user, permission='org_manager').exists()
    except:
        return False

def is_org_or_sensor_manager(user: User, organization: Organization) -> bool:
    try:
        return Membership.objects.filter(organization_id=organization.id, user=user, permission='org_manager').exists() or Membership.objects.filter(organization_id=organization.id, user=user, permission='org_sensorManager').exists()
    except:
        return False