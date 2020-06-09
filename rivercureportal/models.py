#GENERATED ENTITIES
from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.gis.db import models


SENSORKIND_CHOICES = (  ('hydrometricSensor','HydrometricSensor'),  ('weatherSensor','WeatherSensor'),  ('socialNetworkScanner','SocialNetworkScanner'),  ('humanSensor','HumanSensor'),  ('tBD Sensor','TBD Sensor'),  )

SENSORMODALITYKIND_CHOICES = (  ('physicalFixed ','PhysicalFixed '),  ('physicalMobile','PhysicalMobile'),  ('digitalSocialNetworkScanner','DigitalSocialNetworkScanner'),  ('digitalHumanUpload','DigitalHumanUpload'),  )

TIMESERIETYPE_CHOICES = (  ('continuous','Continuous'),  ('discontinuous','Discontinuous'),  ('statistical','Statistical'),  )

EVENTKIND_CHOICES = (  ('flood','Flood'),  ('heavyPrecipitation','HeavyPrecipitation'),  ('hydrologicalDrought','HydrologicalDrought'),  ('meteorologicalDrought','MeteorologicalDrought'),  ('hurricane','Hurricane'),  ('tsunami','Tsunami'),  ('storm','Storm'),  ('landSlide','LandSlide'),  )

EVENTSTATE_CHOICES = (  ('announced','Announced'),  ('occurring','Occurring'),  ('concluded','Concluded'),  )

HYDROFEATUREKIND_CHOICES = (  ('river','River'),  ('estuary','Estuary'),  ('lake','Lake'),  ('riverBasin','RiverBasin'),  ('drainageBasin','DrainageBasin'),  ('dam','Dam'),  )

GEOMETRYKIND_CHOICES = (  ('point','Point'),  ('polyline','Polyline'),  ('polygon','Polygon'),  )

SIMULATIONKIND_CHOICES = (  ('simulation','Simulation'),  ('scenario','Scenario'),  )

INFORMATIONKIND_CHOICES = (  ('simulation','Simulation'),  ('event','Event'),  ('sensor','Sensor'),  ('alarm','Alarm'),  )

CITYKIND_CHOICES = (  ('city','City'),  ('town','Town'),  ('village','Village'),  ('other','Other'),  )

ORGANIZATIONKIND_CHOICES = (  ('waterAuthority','WaterAuthority'),  ('municipality','Municipality'),  ('researchLab','ResearchLab'),  ('partner','Partner'),  ('other','Other'),  )

USERKIND_CHOICES = (  ('sysAdmin','SysAdmin'),  ('contextAdmin','ContextAdmin'),  ('contextManager','ContextManager'),  ('contextSimulationManager','ContextSimulationManager'),  ('contextTechnician','ContextTechnician'),  ('citizen','Citizen'),  )

USERSTATE_CHOICES = (  ('suspended','Suspended'),  ('active','Active'),  ('inactive','Inactive'),  ('deleted','Deleted'),  )

ALARMPERMISSION_CHOICES = (  ('yes','Yes'),  ('yes (only authorities alarms)','Yes (only authorities alarms)'),  ('no','No'),  ('depend on secondary role','Depend on secondary role'),  )

METRICKIND_CHOICES = (  ('sec','Sec'),  ('min','Min'),  ('hour','Hour'),  ('day','Day'),  ('week','Week'),  ('month','Month'),  ('year','Year'),  )

COLOURKIND_CHOICES = (  ('red','Red'),  ('yellow','Yellow'),  ('green','Green'),  )

class e_Country(models.Model):

	
	code_regex = RegexValidator(
		regex=r'^[a-zA-Z0-9]*$',  #temporarly this expression by default
		message="",
		code="invalid_field")#true
	code = models.CharField(max_length=20,validators=[code_regex])


	Name = models.CharField(max_length=20)

	capital = models.ForeignKey('e_City', on_delete=models.CASCADE, related_name='e_Country_capital')

#TYPE GEOGRAFICO
	geom = models.MultiPolygonField()

class e_District(models.Model):

	
	code_regex = RegexValidator(
		regex=r'^[a-zA-Z0-9]*$',  #temporarly this expression by default
		message="",
		code="invalid_field")#true
	code = models.CharField(max_length=20,validators=[code_regex])


	Name = models.CharField(max_length=20)

	capital = models.ForeignKey('e_City', on_delete=models.CASCADE, related_name='e_District_capital')

	country = models.ForeignKey('e_Country', on_delete=models.CASCADE, related_name='e_District_country')

#TYPE GEOGRAFICO
	geom = models.MultiPolygonField()

class e_Municipality(models.Model):

	

	code = models.CharField(max_length=20)


	Name = models.CharField(max_length=20)

	district = models.ForeignKey('e_District', on_delete=models.CASCADE, related_name='e_Municipality_district')

	capital = models.ForeignKey('e_City', on_delete=models.CASCADE, related_name='e_Municipality_capital')

#TYPE GEOGRAFICO
	geom = models.MultiPolygonField()

class e_Parish(models.Model):

	

	code = models.CharField(max_length=20)


	Name = models.CharField(max_length=20)

	municipality = models.ForeignKey('e_Municipality', on_delete=models.CASCADE, related_name='e_Parish_municipality')

#TYPE GEOGRAFICO
	geom = models.MultiPolygonField()

class e_City(models.Model):

	

	code = models.CharField(max_length=20)


	Name = models.CharField(max_length=20)

	type = models.CharField(max_length=15, choices=CITYKIND_CHOICES)

	municipality = models.ForeignKey('e_Municipality', on_delete=models.CASCADE, related_name='e_City_municipality')

#TYPE GEOGRAFICO
	geom = models.PointField()

class e_HydroFeature(models.Model):

	

	code = models.CharField(max_length=20)


	Name = models.CharField(max_length=20)

	type = models.CharField(max_length=15, choices=HYDROFEATUREKIND_CHOICES)


	area = models.DecimalField(max_digits=5, decimal_places=2)


	length = models.DecimalField(max_digits=5, decimal_places=2)

	PartOf = models.ForeignKey('e_HydroFeature', on_delete=models.CASCADE, related_name='e_HydroFeature_PartOf')

	flowsInto = models.ForeignKey('e_HydroFeature', on_delete=models.CASCADE, related_name='e_HydroFeature_flowsInto')

#TYPE GEOGRAFICO
	geom = models.MultiPolygonField()

class e_Organization(models.Model):


	Name = models.CharField(max_length=20)

	type = models.CharField(max_length=15, choices=ORGANIZATIONKIND_CHOICES)


	sector = models.CharField(max_length=20)


	address = models.CharField(max_length=20)

	city = models.ForeignKey('e_City', on_delete=models.CASCADE, related_name='e_Organization_city')

	country = models.ForeignKey('e_Country', on_delete=models.CASCADE, related_name='e_Organization_country')


	email = models.EmailField(max_length=254)


	phone = models.CharField(max_length=20)

#TYPE GEOGRAFICO
	geom = models.PointField()

class e_User(models.Model):

	user = models.OneToOneField(User, on_delete=models.CASCADE)
	password = models.CharField(max_length=20)
	Name = models.TextField()
	email = models.EmailField(max_length=254)
	emails = models.EmailField(max_length=254)
	phoneNumbers = models.CharField(max_length=20)

