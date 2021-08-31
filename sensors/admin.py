from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import Sensor, SensorObservation

admin.site.register(Sensor, LeafletGeoAdmin)
admin.site.register(SensorObservation, LeafletGeoAdmin)


