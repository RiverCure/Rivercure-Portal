def is_platform_admin(user):
    try:
        return user.groups.filter(name='Admin').exists()
    except:
        return False

def is_platform_admin_or_manager(user):
    try:
        return user.groups.filter(name='Admin').exists() or user.groups.filter(name='Manager').exists()
    except:
        return False