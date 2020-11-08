from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User

def run():
    aU_Admin_group = Group(name='Administration')
    aU_Admin_group.save()
    user=User.objects.create_user('Admin', password='password')
    user.is_staff=True
    user.save()
    aU_Admin_group.user_set.add(user)

    aU_ContextAdmin_group = Group(name='ContextAdmin')
    aU_ContextAdmin_group.save()
    user=User.objects.create_user('ContextAdmin', password='password')
    user.is_staff=True
    user.save()
    aU_ContextAdmin_group.user_set.add(user)

    aU_ContextManager_group = Group(name='ContextManager')
    aU_ContextManager_group.save()
    user=User.objects.create_user('ContextManager', password='password')
    user.is_staff=True
    user.save()
    aU_ContextManager_group.user_set.add(user)

    aU_Manager_group = Group(name='Manager')
    aU_Manager_group.save()
    user=User.objects.create_user('Manager', password='password')
    user.is_staff=True
    user.save()
    aU_Manager_group.user_set.add(user)

    aU_SensorManager_group = Group(name='SensorManager')
    aU_SensorManager_group.save()
    user=User.objects.create_user('SensorManager', password='password')
    user.is_staff=True
    user.save()
    aU_SensorManager_group.user_set.add(user)

    aU_ContextEventManager_group = Group(name='ContextEventManager')
    aU_SensorManager_group.save()
    user=User.objects.create_user('ContextEventManager', password='password')
    user.is_staff=True
    user.save()
    aU_SensorManager_group.user_set.add(user)

    aU_Visitor_group = Group(name='Visitor')
    aU_Visitor_group.save()
    user=User.objects.create_user('Visitor', password='password')
    user.is_staff=False
    user.save()
    aU_Visitor_group.user_set.add(user)

    permission_HydroFeatureCreate = Permission.objects.get(codename='add_e_hydrofeature')
    aU_Manager_group.permissions.add(permission_HydroFeatureCreate)
    permission_HydroFeatureChange = Permission.objects.get(codename='change_e_hydrofeature')
    aU_Manager_group.permissions.add(permission_HydroFeatureChange)
    permission_HydroFeatureDelete = Permission.objects.get(codename='delete_e_hydrofeature')
    aU_Manager_group.permissions.add(permission_HydroFeatureDelete)
    permission_HydroFeatureView = Permission.objects.get(codename='view_e_hydrofeature')
    aU_Manager_group.permissions.add(permission_HydroFeatureView)

    aU_Admin_group.permissions.add(permission_HydroFeatureView)
    aU_Visitor_group.permissions.add(permission_HydroFeatureView)
    aU_ContextEventManager_group.permissions.add(permission_HydroFeatureView)
    aU_ContextAdmin_group.permissions.add(permission_HydroFeatureView)
    aU_ContextManager_group.permissions.add(permission_HydroFeatureView)
    aU_SensorManager_group.permissions.add(permission_HydroFeatureView)
    
    permission_SensorCreate = Permission.objects.get(codename='add_e_sensor')
    aU_SensorManager_group.permissions.add(permission_SensorCreate)
    permission_SensorChange = Permission.objects.get(codename='change_e_sensor')
    aU_SensorManager_group.permissions.add(permission_SensorChange)
    permission_SensorDelete = Permission.objects.get(codename='delete_e_sensor')
    aU_SensorManager_group.permissions.add(permission_SensorDelete)
    permission_SensorView = Permission.objects.get(codename='view_e_sensor')
    aU_SensorManager_group.permissions.add(permission_SensorView)

    permission_SensorObservationCreate = Permission.objects.get(codename='add_e_sensor_observation')
    aU_SensorManager_group.permissions.add(permission_SensorObservationCreate)
    permission_SensorObservationChange = Permission.objects.get(codename='change_e_sensor_observation')
    aU_SensorManager_group.permissions.add(permission_SensorObservationChange)
    permission_SensorObservationDelete = Permission.objects.get(codename='delete_e_sensor_observation')
    aU_SensorManager_group.permissions.add(permission_SensorObservationDelete)
    permission_SensorObservationView = Permission.objects.get(codename='view_e_sensor_observation')
    aU_SensorManager_group.permissions.add(permission_SensorObservationView)

    permission_ContextCreate = Permission.objects.get(codename='add_e_context')
    permission_ContextChange = Permission.objects.get(codename='change_e_context')
    permission_ContextDelete = Permission.objects.get(codename='delete_e_context')
    permission_ContextView = Permission.objects.get(codename='view_e_context')
    
    aU_ContextAdmin_group.permissions.add(permission_ContextCreate)
    aU_ContextAdmin_group.permissions.add(permission_ContextChange)
    aU_ContextAdmin_group.permissions.add(permission_ContextDelete)
    aU_ContextAdmin_group.permissions.add(permission_ContextView)

    aU_ContextManager_group.permissions.add(permission_ContextChange)
    aU_ContextManager_group.permissions.add(permission_ContextView)

    aU_ContextEventManager_group.permissions.add(permission_ContextChange)
    aU_ContextEventManager_group.permissions.add(permission_ContextView)

    permission_ContextEventCreate = Permission.objects.get(codename='add_e_ContextEvent')
    permission_ContextEventChange = Permission.objects.get(codename='change_e_ContextEvent')
    permission_ContextEventDelete = Permission.objects.get(codename='delete_e_ContextEvent')
    permission_ContextEventView = Permission.objects.get(codename='view_e_ContextEvent')
    
    
    aU_ContextEventManager_group.permissions.add(permission_ContextEventCreate)
    aU_ContextEventManager_group.permissions.add(permission_ContextEventChange)
    aU_ContextEventManager_group.permissions.add(permission_ContextEventDelete)
    aU_ContextEventManager_group.permissions.add(permission_ContextEventView)

