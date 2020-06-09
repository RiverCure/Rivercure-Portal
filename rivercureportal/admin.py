from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.gis import admin		
from leaflet.admin import LeafletGeoAdmin
from .models import e_User, e_City, e_District, e_Municipality, e_Parish, e_HydroFeature, e_Organization


admin.site.register(e_City, LeafletGeoAdmin)
admin.site.register(e_District, LeafletGeoAdmin)
admin.site.register(e_Municipality, LeafletGeoAdmin)
admin.site.register(e_Parish, LeafletGeoAdmin)
admin.site.register(e_HydroFeature, LeafletGeoAdmin)

admin.site.register(e_Organization)


class UserInline(admin.StackedInline):
	model = e_User
	can_delete = False
	verbose_name_plural = 'e_User'

class UserAdmin(BaseUserAdmin):
    inlines = (UserInline,)
    
admin.site.unregister(User)
admin.site.register(User, UserAdmin)			


