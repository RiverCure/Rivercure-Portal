from django.contrib import admin
from django.contrib.gis import admin		
from leaflet.admin import LeafletGeoAdmin
from .models import e_Context, e_ContextBoundaryLine

admin.site.register(e_Context, LeafletGeoAdmin)
admin.site.register(e_ContextBoundaryLine, LeafletGeoAdmin)