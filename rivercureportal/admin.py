from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.gis import admin		
from .models import e_User, e_City, e_District, e_Municipality, e_Parish, e_HydroFeature, e_Organization


admin.site.register(e_City,admin.GeoModelAdmin)
admin.site.register(e_District,admin.GeoModelAdmin)
admin.site.register(e_Municipality,admin.GeoModelAdmin)
admin.site.register(e_Parish,admin.GeoModelAdmin)
admin.site.register(e_HydroFeature,admin.GeoModelAdmin)

admin.site.register(e_Organization)


class UserInline(admin.StackedInline):
	model = e_User
	can_delete = False
	verbose_name_plural = 'e_User'

class UserAdmin(BaseUserAdmin):
    inlines = (UserInline,)
    
admin.site.unregister(User)
admin.site.register(User, UserAdmin)			


