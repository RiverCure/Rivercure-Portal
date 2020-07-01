from django.contrib.gis.db import models
from datetime import datetime
from rivercureportal.models import e_HydroFeature
from django.contrib.auth.models import User
from sensors.models import e_Sensor

EVENTKIND_CHOICES = (  ('flood','Flood'),  ('heavyPrecipitation','HeavyPrecipitation'),  ('hydrologicalDrought','HydrologicalDrought'),  ('meteorologicalDrought','MeteorologicalDrought'),  ('hurricane','Hurricane'),  ('tsunami','Tsunami'),  ('storm','Storm'),  ('landSlide','LandSlide'),  )

EVENTSTATE_CHOICES = (  ('announced','Announced'),  ('occurring','Occurring'),  ('concluded','Concluded'),  )

CONTEXTBOUNDARY_CHOICES = ( ('Input', 'input'), ('Output', 'output'), ('InputOutput', 'inputOutput'), )

CONTEXTBOUNDARYLINEDATAKIND_CHOICES =  ( ('H', 'h'), ('Q', 'q'), )

class e_Context(models.Model):
	code = models.CharField(max_length=100, unique=True)

	Name = models.CharField(max_length=100, unique=True)

	hydroFeature = models.ForeignKey('rivercureportal.e_HydroFeature', on_delete=models.CASCADE, null=True, blank=False )

	geomExternalBoundary = models.MultiPolygonField(null=True)  		#aka Domain
	CLExternalBoundary  = models.BigIntegerField(null=True)  			#aka Domain's CL, characteristic lenght 
	
	geomInternalBoundary = models.MultiPolygonField(null=True) 					# aka Refinement
	CLInternalBoundary  = models.BigIntegerField(null=True)  			#aka Refinement's CL

	geomAlignment = models.MultiLineStringField(null=True)   		# aka Alignment
	CLAlignment = models.BigIntegerField(null=True)   					# Alignment's CL

	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

	def __str__(self):
		return self.Name


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


class  e_ContextBoundaryLine(models.Model):

	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)

	type = models.CharField(max_length=30, choices=CONTEXTBOUNDARY_CHOICES)
	datakind = models.CharField(max_length=30, choices=CONTEXTBOUNDARYLINEDATAKIND_CHOICES)
	geom = models.MultiLineStringField(null=True) #superimposed "must be a line superimposed on context.geomExternalBoundary"))] 
	

class  e_ContextBoundaryPoint(models.Model):

	contextBoundaryLine = models.ForeignKey('e_ContextBoundaryLine', on_delete=models.CASCADE, null=True, blank=False )

	geom = models.PointField() #superimposed "must be a point superimposed on e_ContextBoundaryLine.geom"))]  


class  e_ContextBoundaryPointSensor(models.Model):

	point = models.IntegerField()

	sensor = models.ForeignKey('sensors.e_Sensor', on_delete=models.CASCADE, null=True, blank=False )
	

class e_ContextSensor(models.Model):

	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)
	sensor = models.ForeignKey('sensors.e_Sensor', on_delete=models.CASCADE, null=True, blank=False )
	description = models.TextField()
	#attribute associateDatetime "Associate Datetime" : Datetime [constraints(NotNull)]
	#attribute associateUser "Associate User" : String [constraints(NotNull ForeignKey (e_User))]



