from django.contrib.auth.models import Group

# Creates the two groups
def run():
    aU_Admin_group = Group(name='Admin')
    aU_Admin_group.save()

    aU_Manager_group = Group(name='Manager')
    aU_Manager_group.save()