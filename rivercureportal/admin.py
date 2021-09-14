
from django.contrib.auth.models import User
from django.contrib.gis import admin		
from leaflet.admin import LeafletGeoAdmin
from .models import e_HydroFeature

admin.site.register(e_HydroFeature, LeafletGeoAdmin)

from notifications.models import Notification
admin.site.unregister(Notification)

from raster.models import LegendSemantics, LegendEntry, Legend, RasterLayer, RasterLayerMetadata, RasterTile
admin.site.unregister(LegendSemantics)
admin.site.unregister(LegendEntry)
admin.site.unregister(Legend)
admin.site.unregister(RasterLayer)
admin.site.unregister(RasterLayerMetadata)
admin.site.unregister(RasterTile)