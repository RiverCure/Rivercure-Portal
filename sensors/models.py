from django.contrib.gis.db import models
from organization.models import Organization
from datetime import date

SENSOR_CLASS_STATE = ( ('active', 'Active'), ('inactive', 'Inactive') )

SENSOR_MODALITY_KIND = ( ('PhysicalFixed', 'Physical Fixed'), ('PhysicalMobile', 'Physical Mobile'), ('Digital','Digital'), ('Human','Human') )

SENSOR_STATE = ( ('active', 'Active'), ('inactive', 'Inactive'), ('deleted', 'Deleted') )

SENSOR_VISIBILITY_KIND = ( ('public', 'Public'), ('private', 'Private') )

SEVERITY_KIND = ( ('ok', 'Ok'), ('attention', 'Attention'), ('critical', 'Critical') )

SENSOR_OBSERVATION_VALUE_TYPE = ( ('number', 'Number'), ('string', 'String'), ('image', 'Image') )

class SensorCategory(models.Model):
    name = models.TextField(unique=True)

    def __str__(self):
        return self.name

class QuantityKind(models.Model):
    fullName     = models.TextField(unique=True) # E.g.: Length
    abbreviation = models.TextField() # E.g.: len

    def __str__(self):
        return self.fullName

class Unit(models.Model):
    fullName     = models.TextField(unique=True) # E.g.: Meter
    abbreviation = models.TextField() # E.g.: m
    quantity     = models.ForeignKey(to=QuantityKind, on_delete=models.CASCADE)

    def __str__(self):
        return self.fullName

class SensorClass(models.Model):
    code         = models.TextField(unique=True)
    name         = models.TextField()
    state        = models.TextField(choices=SENSOR_CLASS_STATE)
    vendor       = models.TextField(blank=True)
    version      = models.TextField(blank=True)
    modality     = models.TextField(choices=SENSOR_MODALITY_KIND)
    kind         = models.ForeignKey(to=SensorCategory, on_delete=models.CASCADE)
    organization = models.ForeignKey(to=Organization, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Sensor(models.Model):
    code         = models.TextField(unique=True)
    name         = models.TextField()
    description  = models.TextField()
    state        = models.TextField(choices=SENSOR_STATE)
    # visibility   = models.TextField(choices=SENSOR_VISIBILITY_KIND) -> not needed (yet). Replaced by isPublic
    isPublic     = models.BooleanField(default=True)
    local        = models.PointField(null=True) # being null=True allows 0..1 relationship
    sensorClass  = models.ForeignKey(to=SensorClass, on_delete=models.CASCADE)
    organization = models.ForeignKey(to=Organization, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class SensorClassProperty(models.Model):
    code                      = models.TextField(unique=True)
    name                      = models.TextField()
    type                      = models.TextField(choices=SENSOR_OBSERVATION_VALUE_TYPE)
    isOptional                = models.BooleanField(default=False)
    thresholdLowerCritical    = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    thresholdLowerNoncritical = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    thresholdUpperCritical    = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    thresholdUpperNoncritical = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    sensorClass               = models.ForeignKey(to=SensorClass, on_delete=models.CASCADE)
    unit                      = models.ForeignKey(to=Unit, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

class SensorObservation(models.Model):
    # dateTime would be better, but preivously it used dateTime and it has many dependencies to change. Perhaps change in the future?
    date     = models.DateField(default=date.today)
    time     = models.TimeField()
    value    = models.TextField()
    severity = models.TextField(choices=SEVERITY_KIND)
    property = models.ForeignKey(to=SensorClassProperty, on_delete=models.CASCADE)
    sensor   = models.ForeignKey(to=Sensor, on_delete=models.CASCADE)