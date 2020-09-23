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

    aU_Visitor_group = Group(name='Visitor')
    aU_Visitor_group.save()
    user=User.objects.create_user('Visitor', password='password')
    user.is_staff=False
    user.save()
    aU_Visitor_group.user_set.add(user)

    permission_Create = Permission.objects.get(codename='add_e_hydrofeature')
    aU_Admin_group.permissions.add(permission_Create)

