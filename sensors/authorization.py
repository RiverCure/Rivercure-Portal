from organization.models import Membership
from django.db.models import Q

def sensor_general_create_permission_check(user):
    try:
        return Membership.objects.filter(user=user, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager')).exists()
    except:
        return False
# To view is enough to be in the organization
def sensor_view_permission_check(user, sensor):
    try:
        return sensor.isPublic or Membership.objects.filter(user=user, organization=sensor.sensorClass.organization, access_granted=True).exists()
    except:
        return False

def sensor_edit_permission_check(user, sensor):
    try:
        return Membership.objects.filter(user=user, organization=sensor.sensorClass.organization, organization__is_active=True).filter(Q(permission='org_manager') | Q(permission='org_sensorManager') | Q(permission='org_contextManager')).exists()
    except:
        return False