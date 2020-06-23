from django.contrib.gis.db import models
from datetime import datetime
from rivercureportal.models import e_HydroFeature
from django.contrib.auth.models import User

EVENTKIND_CHOICES = (  ('flood','Flood'),  ('heavyPrecipitation','HeavyPrecipitation'),  ('hydrologicalDrought','HydrologicalDrought'),  ('meteorologicalDrought','MeteorologicalDrought'),  ('hurricane','Hurricane'),  ('tsunami','Tsunami'),  ('storm','Storm'),  ('landSlide','LandSlide'),  )

EVENTSTATE_CHOICES = (  ('announced','Announced'),  ('occurring','Occurring'),  ('concluded','Concluded'),  )

CONTEXTBOUNDARY_CHOICES = ( ('Input', 'input'), ('Output', 'output'), ('InputOutput', 'inputOutput'), )

CONTEXTBOUNDARYLINEDATAKIND_CHOICES =  ( ('H', 'h'), ('Q', 'q'), )

class e_Context(models.Model):
	code = models.CharField(max_length=100, unique=True)

	Name = models.CharField(max_length=100, unique=True)

	hydroFeature = models.ForeignKey('rivercureportal.e_HydroFeature', on_delete=models.CASCADE, null=True, blank=False )

	#GEOPOLYGON
	geom = models.MultiPolygonField(null=True)

	#NEW BOUNDARY ATTRIBUTES TO BE DEFINED

	def __str__(self):
		return self.Name

class e_ContextUser(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)
	
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	def __str__(self):
		return self.user.username


class e_ContextBoundaryCondition(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)

	geom = models.MultiLineStringField(null=True) #TEMPORARY CHOICE
	
	type = models.CharField(max_length=30, choices=CONTEXTBOUNDARY_CHOICES)
	
class e_ContextEvent(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)

	Name = models.CharField(max_length=100, unique=True)

	type = models.CharField(max_length=30, choices=EVENTKIND_CHOICES)

	state = models.CharField(max_length=30, choices=EVENTSTATE_CHOICES)
	
	startDatetime = models.DateTimeField() 
	endDatetime = models.DateTimeField()    #always bigger than starttime

	description = models.TextField()


#DataEntity e_ContextBoundaryLine : Master 
	
#DataEntity e_ContextBoundaryPoint : Master 
	
#DataEntity e_ContextBoundaryPointSensor : Master 
	
#DataEntity e_ContextSensor "ContextSensor" : Master 

#DataEntity e_ContextOrganization "ContextOrganization" : Parameter [

#DataEntity e_ContextOrganizationUser "ContextOrganizationUser" : Parameter [