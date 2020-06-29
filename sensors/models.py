from django.contrib.gis.db import models
from datetime import datetime
from django.contrib.auth.models import User

SENSORKIND_CHOICES = (  ('hydrometricSensor','HydrometricSensor'),  ('weatherSensor','WeatherSensor'),  ('socialNetworkScanner','SocialNetworkScanner'),  ('humanSensor','HumanSensor'),  ('tBD Sensor','TBD Sensor'),  )

SENSORMODALITYKIND_CHOICES = (  ('physicalFixed ','PhysicalFixed '),  ('physicalMobile','PhysicalMobile'),  ('digitalSocialNetworkScanner','DigitalSocialNetworkScanner'),  ('digitalHumanUpload','DigitalHumanUpload'),  )

COLOURKIND_CHOICES = (  ('red','Red'),  ('yellow','Yellow'),  ('green','Green'),  )

class e_Sensor(models.Model):
    code = models.CharField(max_length=100, unique=True)

    Name = models.CharField(max_length=100)

    responsibleUser = models.ForeignKey(User, on_delete=models.CASCADE)

    modalityType = models.CharField(max_length=50, choices=SENSORMODALITYKIND_CHOICES)

    type = models.CharField(max_length=50, choices= SENSORKIND_CHOICES )
    
    description = models.TextField()

    version = models.CharField(max_length=20)

    timeZoneAbbreviation = models.CharField(max_length=20)

    timeZoneOffset = models.IntegerField()

    geom = models.PointField()
   
    # FixedInSituSensor
# 	attribute recRhythmValue "Recording rhythm value" : Integer []
# 	attribute recRhythmMetric "Recording rhythm metric" : DataEnumeration MetricKind

#  HydrometricSensor
# 	attribute zeroLevelScale "Zero level scale" : Decimal  

#  WeatherSensor
# 	attribute maxRange "Max range" : Integer 
# 	attribute PRF "Pulse repetition frequency (PRF)" : Integer 
# 	attribute recRhythm "Recording rhythm" : String  

# 	PhotoSensor
# 	attribute isSocialNetwork "is from a social network" : Boolean [defaultValue "False"]
# 	attribute isUpload "is from an upload" : Boolean [defaultValue "False"]
# 	attribute source "Source" : String 
# 	attribute url "URL" : URL
# 	attribute isAgreeTerms "is agreed with terms and conditions" : Boolean [defaultValue "True"]

    def __str__(self):
        return self.Name


class e_SensorAlarm(models.Model):

    sensor = models.ForeignKey('e_Sensor', on_delete=models.CASCADE, null=True, blank=False)

    Name = models.CharField(max_length=100)

    action = models.CharField(max_length=100)

    description = models.TextField()

    colour = models.CharField(max_length=50, choices=COLOURKIND_CHOICES)
    
    redMinthreshold = models.DecimalField(max_digits=10, decimal_places=2)

    redMaxthreshold = models.DecimalField(max_digits=10, decimal_places=2)

    yellowMinthreshold = models.DecimalField(max_digits=10, decimal_places=2)

    yellowMaxthreshold = models.DecimalField(max_digits=10, decimal_places=2)

    greenMinthreshold = models.DecimalField(max_digits=10, decimal_places=2)

    greenMaxthreshold = models.DecimalField(max_digits=10, decimal_places=2)


class e_SensorObservation(models.Model):

    sensor = models.ForeignKey('e_Sensor', on_delete=models.CASCADE, null=True, blank=False)

    sensorType = models.CharField(max_length=50, choices=SENSORKIND_CHOICES )

    startDatetime = models.DateTimeField()

    endDateTime = models.DateTimeField()
# 	// TBD
# 	attribute data "Data" : String  

# 	// HydrometricSensor
# 	attribute depth : Double  		// profundidade (m)
# 	attribute discharge : Double	// caudal (m3/seg)
# 	attribute volume : Double		// volume (m3)
# 	attribute velocity : Double		// velocidade (m/seg)
# 	attribute elevation : Double	// cota (m3)
	
# 	// WeatherSensorObservation
# 	attribute rainfall : Double  			// precipitação (m)
# 	attribute soilWaterContent : Double  	// teor em água do solo (%)
	
# 	//HumanSensorObservation
# 	attribute photo : Image
# 	attribute geom "Geometry"	: GeoPoint [constraints (NotNull)]
# 	attribute elevation : Double [constraints (Derived ("ML techniques from Photo"))] 	// cota (m3)
# 	attribute velocity : Double	[constraints (Derived ("ML techniques from Photo"))]	// velocidade (m/seg)

# 	//RadarSensorObservation
# 	// Mapa de valores
# 	attribute rainfall : Double  			// precipitação (m)
	
# 	//TBD SensorObservation 
# 	attribute isCummulative "is Cummulative" : Boolean [defaultValue "False"]
# 	attribute nValueTotal "Total number of values" : Integer [constraints (NotNull)]

# 	//e_PhotoSensorObservation
# 	attribute url "URL" : URL
# 	attribute fileName "File name" : String 
# 	attribute height "Height" : Integer
# 	attribute horizontalRes "Horizontal resolution" : Integer
# 	attribute verticalRes "Vertical resolution" : Integer
# 	attribute nBits "Number of bits" : Integer
# 	attribute width "Width" : Integer
# 	attribute fileFormat "File format" : String
