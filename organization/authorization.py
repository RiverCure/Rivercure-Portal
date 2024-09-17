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
    """
    Checks whether user is Manager in specific organization
    """
    try:
        return Membership.objects.filter(organization=organization, user=user, permission='org_manager').exists()
    except:
        return False


def is_sensor_manager(user: User, organization: Organization) -> bool:
    """
    Checks whether user is Sensor Manager in specific organization
    """
    try:
        return Membership.objects.filter(organization=organization, user=user, permission='org_sensorManager').exists()
    except:
        return False


def is_org_manager_or_sensor_manager(user: User, organization: Organization) -> bool:
    """
    Checks whether user is Manager or Sensor Manager in specific organization
    """
    try:
        return Membership.objects.filter(organization_id=organization.id, user=user, permission='org_manager').exists() or Membership.objects.filter(organization_id=organization.id, user=user, permission='org_sensorManager').exists()
    except:
        return False


def is_org_quiz_manager(user: User, organization: Organization) -> bool:
    """
    Checks whether user is Quiz Manager in specific organization
    """
    try:
        return  Membership.objects.filter(organization=organization, user=user, permission='org_quizManager').exists()
    except:
        return False