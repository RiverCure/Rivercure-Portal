from organization.models import Membership, Organization
from django.contrib.auth.models import User


def belongs_to_organization(user, organization):
    """
    Checks whether user belongs to a specific organization
    """
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


def is_org_manager_check(user: User, organization_id: int) -> bool:
    try:
        return Membership.objects.filter(organization=organization_id, user=user, permission='org_manager').exists()
    except:
        return False


def is_org_manager_or_sensor_manager(user: User, organization: Organization) -> bool:
    try:
        return Membership.objects.filter(organization_id=organization.id, user=user, permission='org_manager').exists() or Membership.objects.filter(organization_id=organization.id, user=user, permission='org_sensorManager').exists()
    except:
        return False
