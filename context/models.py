from django.contrib.gis.db import models
from datetime import datetime, date
from rivercureportal.models import e_HydroFeature
from django.contrib.auth.models import User
from sensors.models import e_Sensor


EVENTKIND_CHOICES = (  ('flood','Flood'),  ('heavyPrecipitation','HeavyPrecipitation'),  ('hydrologicalDrought','HydrologicalDrought'),  ('meteorologicalDrought','MeteorologicalDrought'),  ('hurricane','Hurricane'),  ('tsunami','Tsunami'),  ('storm','Storm'),  ('landSlide','LandSlide'),  )

EVENTSTATE_CHOICES = (  ('announced','Announced'),  ('occurring','Occurring'),  ('concluded','Concluded'),  )

EVENTSUBKIND_CHOICES = (  ('Real','real'),  ('simulation','Simulation'),  )

EVENTSIMULATIONKIND_CHOICES = ( ('Forecast', 'forecast'), ('Hindcast','hindcast'), ('Planning','planning'),)

CONTEXTBOUNDARY_CHOICES = ( ('Input', 'input'), ('Output', 'output'), ('InputOutput', 'inputOutput'), )

CONTEXTBOUNDARY_CHOICES = ( ('Input', 'input'), ('Output', 'output'), ('InputOutput', 'inputOutput'), )

ContextAccessRequestState_CHOICES =  ( ('Processing', 'processing'), ('Finished', 'finished'), )

CONTEXTBOUNDARYLINEDATAKIND_CHOICES =  ( ('H', 'Depth'), ('Q', 'Discharge'), ('Z', 'Elevation'), ('V', 'Velocity'), )

CONTEXTACCESS_CHOICES = (('admin', 'Admin'), ('manager', 'Manager'), ('viewer', 'Viewer'))

class e_Context(models.Model):
	code = models.CharField(primary_key=True, max_length=100, unique=True)

	Name = models.CharField(max_length=100, unique=True)

	hydroFeature = models.ForeignKey('rivercureportal.e_HydroFeature', on_delete=models.CASCADE, null=True, blank=False )

	geomExternalBoundary = models.MultiPolygonField(null=True, blank=True)  		#aka Domain
	CLExternalBoundary  = models.BigIntegerField(null=True, blank=True)  			#aka Domain's CL, characteristic lenght 

	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True) # Owner do contexto

	isPublic = models.BooleanField(default=False)

	def __str__(self):
		return self.Name

class e_ContextRefinement(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE, related_name='context_refinement')
	geom = models.PolygonField(null=True, blank=True) 					# aka Refinement
	CL  = models.BigIntegerField(null=True, blank=True)  			#aka Refinement's CL

	def __str__(self):
		return f"{self.context} context refinement"

class e_ContextAlignment(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE, related_name='context_alignment')
	geom = models.LineStringField(null=True, blank=True)   		# aka Alignment
	CL = models.BigIntegerField(null=True, blank=True)   					# Alignment's CL

	def __str__(self):
		return f"{self.context} context alignment"

class  e_ContextBoundaryLine(models.Model):

	context = models.ForeignKey('e_Context', on_delete=models.CASCADE, related_name='context_boundaries')

	geom = models.LineStringField(null=True, blank=True) #superimposed "must be a line superimposed on context.geomExternalBoundary"))] 

	type = models.CharField(max_length=30, choices=CONTEXTBOUNDARY_CHOICES)
	dataType = models.CharField(max_length=30, choices=CONTEXTBOUNDARYLINEDATAKIND_CHOICES, null=True)

	def __str__(self):
		return f"{self.context} context boundary line"
		
	
class  e_ContextBoundaryPoint(models.Model):

	contextBoundaryLine = models.ForeignKey('e_ContextBoundaryLine', on_delete=models.CASCADE, null=True, blank=False, related_name='context_boundary_points')

	geom = models.PointField(null=True, blank=True) #superimposed "must be a point superimposed on e_ContextBoundaryLine.geom"))]  

	# sensor = models.ForeignKey('e_ContextSensor', on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		return f"{self.contextBoundaryLine} point"

class e_ContextSensor(models.Model):

	boundary_point = models.ForeignKey('e_ContextBoundaryPoint', on_delete=models.CASCADE, null=True, related_name='sensor_boundary_point')
	sensor = models.ForeignKey('sensors.e_Sensor', on_delete=models.CASCADE, null=True, blank=False, related_name='context_sensor' )
	description = models.TextField()
	
	associateDatetime = models.DateTimeField(default=datetime.now)
	# user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

	def __str__(self):
		return f"{self.boundary_point} sensor"

# A sensor has to be associated to Context before being associated with a point. Check ASL specification

class e_ContextEvent(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)

	Name = models.CharField(max_length=100, unique=True)

	type = models.CharField(max_length=30, choices=EVENTKIND_CHOICES)

	state = models.CharField(max_length=30, choices=EVENTSTATE_CHOICES)
	
	startDate = models.DateField(default=date.today)

	startTime = models.TimeField(null=True)

	endDate = models.DateField(default=date.today)

	endTime = models.TimeField(null=True)
	   									
	description = models.TextField()

	#Attributes for "Flood Simulation" event, with iStav

	returnPeriod = models.IntegerField(default=1)

	warmUp = models.BooleanField(default=False)
	
	simulationType = models.CharField(max_length=30, choices=EVENTSIMULATIONKIND_CHOICES, null=True)


class e_ContextAccessRequest(models.Model):

	context = models.ForeignKey('e_Context', on_delete=models.CASCADE)

	access_granted = models.BooleanField(default=False)

	state = models.CharField(max_length=30, choices=ContextAccessRequestState_CHOICES, null=True, default="processing")

	requestuser = models.ForeignKey(User, on_delete=models.CASCADE, null=True) # REQUESTER

	type = models.CharField(max_length=30, choices=CONTEXTACCESS_CHOICES)