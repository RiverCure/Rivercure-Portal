
from django.contrib.auth.models import User
from django.contrib.gis import admin		
from leaflet.admin import LeafletGeoAdmin
from .models import e_City, e_District, e_Municipality, e_Parish, e_HydroFeature, e_Organization


admin.site.register(e_City, LeafletGeoAdmin)
admin.site.register(e_District, LeafletGeoAdmin)
admin.site.register(e_Municipality, LeafletGeoAdmin)
admin.site.register(e_Parish, LeafletGeoAdmin)
admin.site.register(e_HydroFeature, LeafletGeoAdmin)

admin.site.register(e_Organization)
