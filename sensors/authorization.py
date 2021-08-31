from organization.models import Membership
from django.db.models import Q

def sensor_general_create_permission_check(user):
    return Membership.objects.filter(user=user, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager')).exists()
# To view is enough to be in the organization
def sensor_view_permission_check(user, sensor):
    return sensor.isPublic or Membership.objects.filter(user=user, organization=sensor.organization, access_granted=True).exists()

def sensor_edit_permission_check(user, sensor):
    return Membership.objects.filter(user=user, organization=sensor.organization, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager')).exists()