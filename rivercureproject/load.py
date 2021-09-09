from django.contrib.auth.models import Group

# Creates the two groups
def run():
    admin_group = Group(name='Admin')
    admin_group.save()

    manager_group = Group(name='Manager')
    manager_group.save()

    visitor_group = Group(name='Visitor')
    visitor_group.save()