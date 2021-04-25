from django.contrib.gis.db import models
from datetime import datetime, date
from django.contrib.auth.models import User
from organization.models import Organization

SENSORKIND_CHOICES = (  ('HydrometricSensor','Hydrometric Sensor'),  ('WeatherSensor','Weather Sensor'),  ('SocialNetworkScanner','Social Network Scanner'),  ('HumanSensor','Human Sensor'),  ('TBDSensor','TBD Sensor'),  )

SENSORMODALITYKIND_CHOICES = (  ('PhysicalFixed', 'Physical Fixed'),  ('PhysicalMobile', 'Physical Mobile'),  ('DigitalSocialNetworkScanner','Digital Social Network Scanner'),  ('DigitalHumanUpload','Digital Human Upload'),  )

COLOURKIND_CHOICES = (  ('red','Red'),  ('yellow','Yellow'),  ('green','Green'),  )

METRICKIND_CHOICES = (  ('sec','Sec'),  ('min','Min'),  ('hour','Hour'),  ('day','Day'), ('week','Week'), ('month','Month'), ('year','Year'),)


class e_Sensor(models.Model):
    code = models.CharField(primary_key=True, max_length=100, unique=True)

    Name = models.CharField(max_length=100)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)

    isPublic = models.BooleanField(default=True)

    modalityType = models.CharField(max_length=50, choices=SENSORMODALITYKIND_CHOICES)

    type = models.CharField(max_length=50, choices= SENSORKIND_CHOICES )
    
    description = models.TextField()

    version = models.CharField(max_length=20, blank=True, null=True)

    timeZoneAbbreviation = models.CharField(null=True, blank=True, max_length=20)

    timeZoneOffset = models.IntegerField(null=True, blank=True)

    geom = models.PointField()
   
    # FixedInSituSensor
    recRhythmValue = models.IntegerField(null=True, blank=True)                                           # Recording rhythm value
    recRhythmMetric = models.CharField(max_length=20, choices=METRICKIND_CHOICES, null=True)              # Recording rhythm metric                                                                  


#  HydrometricSensor
    zeroLevelScale = models.DecimalField(null=True, max_digits=3, decimal_places=2)


#  WeatherSensor
    maxRange = models.IntegerField(null=True, blank=True)   
    PRF = models.IntegerField(null=True, blank=True)   

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

    date = models.DateField(default=date.today)

    time = models.TimeField(null=True)

    #HYDROMETRIC SENSORS
    depth = models.FloatField(blank=True, null=True)        #profundidade (m)
    discharge = models.FloatField(blank=True, null=True)    #caudal (m3/seg)
    volume  = models.FloatField(blank=True, null=True)      #volume (m3)
    velocity  = models.FloatField(blank=True, null=True)   #velocidade (m/seg)
    elevation  = models.FloatField(blank=True, null=True)   #cota (m)

    test  = models.IntegerField(blank=True, null=True)   #cota (m)

    #WeatherSensorObservation
    WeatherSensorRainFall = models.FloatField(blank=True, null=True)  #precipitação (m)
    soilWaterContent = models.FloatField(blank=True, null=True)    # teor em água do solo (%)

    #RadarSensorObservation
    RadarSensorRainfall = models.FloatField(blank=True, null=True)  #precipitação (m)
    
    class Meta:
	    unique_together = ['sensor', 'date', 'time',]

    #HumanSensorObservation
	#photo : Image
	#geom  : GeoPoint 
	#elevation : Double                              #"ML techniques from Photo" 	// cota (m3)
	#attribute velocity : Double	                 #"ML techniques from Photo"	// velocidade (m/seg)

	#isCummulative "is Cummulative" : Boolean [defaultValue "False"]
	#nValueTotal "Total number of values" : Integer [constraints (NotNull)]

    ##e_PhotoSensorObservation
	#attribute url "URL" : URL
	#attribute fileName "File name" : String 
	#attribute height "Height" : Integer
	#attribute horizontalRes "Horizontal resolution" : Integer
	#attribute verticalRes "Vertical resolution" : Integer
	#attribute nBits "Number of bits" : Integer
	#attribute width "Width" : Integer
	#attribute fileFormat "File format" : String



    def __str__(self):
        return f"{self.sensor} observation {self.id}"