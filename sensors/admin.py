from django.contrib import admin
from sensors.models import SensorCategory, QuantityKind, Unit
from django.db import models
from django.forms.widgets import TextInput

# Just turns TextFields (which are converted into TextAreas), into TextInputs
class MyModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': TextInput},
    }

admin.site.register(SensorCategory, MyModelAdmin)
admin.site.register(QuantityKind, MyModelAdmin)
admin.site.register(Unit, MyModelAdmin)