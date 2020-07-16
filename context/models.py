from django.contrib.gis.db import models
from datetime import datetime
from rivercureportal.models import e_HydroFeature
from django.contrib.auth.models import User
from sensors.models import e_Sensor

EVENTKIND_CHOICES = (  ('flood','Flood'),  ('heavyPrecipitation','HeavyPrecipitation'),  ('hydrologicalDrought','HydrologicalDrought'),  ('meteorologicalDrought','MeteorologicalDrought'),  ('hurricane','Hurricane'),  ('tsunami','Tsunami'),  ('storm','Storm'),  ('landSlide','LandSlide'),  )

EVENTSTATE_CHOICES = (  ('announced','Announced'),  ('occurring','Occurring'),  ('concluded','Concluded'),  )

EVENTSUBKIND_CHOICES = (  ('Real','real'),  ('simulation','Simulation'),  )

EVENTSIMULATIONKIND_CHOICES = ( ('Forecast', 'forecast'), ('Hindcast','hindcast'), ('Planning','planning'),)

CONTEXTBOUNDARY_CHOICES = ( ('Input', 'input'), ('Output', 'output'), ('InputOutput', 'inputOutput'), )

CONTEXTBOUNDARYLINEDATAKIND_CHOICES =  ( ('Depth', 'H'), ('Discharge','Q'), ('Elevation', 'Z'), ('Velocity', 'V'), )

class e_Context(models.Model):
	code = models.CharField(primary_key=True, max_length=100, unique=True)

	Name = models.CharField(max_length=100, unique=True)

	hydroFeature = models.ForeignKey('rivercureportal.e_HydroFeature', on_delete=models.CASCADE, null=True, blank=False )

	geomExternalBoundary = models.MultiPolygonField(null=True, blank=True)  		#aka Domain
	CLExternalBoundary  = models.BigIntegerField(null=True, blank=True)  			#aka Domain's CL, characteristic lenght 
	
	geomInternalBoundary = models.MultiPolygonField(null=True, blank=True) 					# aka Refinement
	CLInternalBoundary  = models.BigIntegerField(null=True, blank=True)  			#aka Refinement's CL

	geomAlignment = models.MultiLineStringField(null=True, blank=True)   		# aka Alignment
	CLAlignment = models.BigIntegerField(null=True, blank=True)   					# Alignment's CL

	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True) # Owner do contexto

	def __str__(self):
		return self.Name

class  e_ContextBoundaryLine(models.Model):

	context = models.ForeignKey('e_Context', on_delete=models.CASCADE, related_name='context_boundaries')

	geom = models.MultiLineStringField(null=True) #superimposed "must be a line superimposed on context.geomExternalBoundary"))] 

	type = models.CharField(max_length=30, choices=CONTEXTBOUNDARY_CHOICES)
	dataType = models.CharField(max_length=30, choices=CONTEXTBOUNDARYLINEDATAKIND_CHOICES, null=True)

	def __str__(self):
		return f"{self.context} context boundary"
		
	
class  e_ContextBoundaryPoint(models.Model):

	contextBoundaryLine = models.ForeignKey('e_ContextBoundaryLine', on_delete=models.CASCADE, null=True, blank=False, related_name='context_boundary_points')

	geom = models.PointField() #superimposed "must be a point superimposed on e_ContextBoundaryLine.geom"))]  

	sensor = models.ForeignKey('e_ContextSensor', on_delete=models.CASCADE, null=True)

class e_ContextSensor(models.Model):

	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)
	sensor = models.ForeignKey('sensors.e_Sensor', on_delete=models.CASCADE, null=True, blank=False )
	description = models.TextField()
	
	associateDatetime = models.DateTimeField(default=datetime.now)
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

class e_ContextEvent(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)

	Name = models.CharField(max_length=100, unique=True)

	type = models.CharField(max_length=30, choices=EVENTKIND_CHOICES)

	state = models.CharField(max_length=30, choices=EVENTSTATE_CHOICES)
	
	startDatetime = models.DateTimeField() 
	endDatetime = models.DateTimeField()    #always bigger than starttime

	description = models.TextField()

	#Attributes for "Flood Simulation" event, with iStav

	returnPeriod = models.IntegerField(default=1)

	warmUp = models.BooleanField(default=False)
	
	simulationType = models.CharField(max_length=30, choices=EVENTSIMULATIONKIND_CHOICES, null=True)


	



#CONTEXT BOUNDARY POINT SENSOR?

#class  e_ContextBoundaryPointSensor(models.Model):

	#point = models.IntegerField()

	#sensor = models.ForeignKey('sensors.e_Sensor', on_delete=models.CASCADE, null=True, blank=False )

#CONTEXT BOUNDARY CONDITION?

# class e_ContextBoundaryCondition(models.Model):
# 	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)
# 	geom = models.MultiLineStringField(null=True) #TEMPORARY CHOICE
# 	type = models.CharField(max_length=30, choices=CONTEXTBOUNDARY_CHOICES)

#CONTEXT SIMULATION?

#CONTEXT USER?

#CONTEXT ORGANIZATION?