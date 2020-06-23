from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import e_Sensor, e_SensorAlarm, e_SensorObservation

admin.site.register(e_Sensor)
admin.site.register(e_SensorAlarm)
admin.site.register(e_SensorObservation)


