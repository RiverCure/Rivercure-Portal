from organization.models import Membership, Organization
from django.contrib.auth.models import User

def belongs_to_organization(user, organization):
    try:
        return Membership.objects.filter(user=user, organization=organization, access_granted=True).exists()
    except:
        return False

def is_org_manager(user: User, organization: Organization) -> bool:
    try:
        return Membership.objects.filter(organization=organization, user=user, permission='org_manager').exists()
    except:
        return False

def is_sensor_manager(user: User, organization: Organization) -> bool:
    try:
        return Membership.objects.filter(organization=organization, user=user, permission='org_sensorManager').exists()
    except:
        return False

def is_org_manager_check(user, organizationCode):
    try:
        return Membership.objects.filter(organization__code=organizationCode, user=user, permission='org_manager').exists()
    except:
        return False

def is_org_manager_or_sensor_manager(user: User, organization: Organization) -> bool:
    try:
        return Membership.objects.filter(organization_id=organization.id, user=user, permission='org_manager').exists() or Membership.objects.filter(organization_id=organization.id, user=user, permission='org_sensorManager').exists()
    except:
        return False