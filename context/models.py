from django.contrib.gis.db import models
from django.utils import timezone
from datetime import datetime, date
from rivercureportal.models import e_HydroFeature
from django.contrib.auth.models import User
from sensors.models import Sensor
from raster.models import RasterLayer
from organization.models import Organization

EVENTKIND_CHOICES = (  ('flood','Flood'),  ('heavyPrecipitation','HeavyPrecipitation'),  
('hydrologicalDrought','Hydrological Drought'),  ('meteorological Drought','Meteorological Drought'),  
('hurricane','Hurricane'),  ('tsunami','Tsunami'),  ('storm','Storm'),  ('landSlide','Land Slide'),  )

EVENTSTATE_CHOICES = (  ('announced','Announced'),  ('occurring','Occurring'),  ('concluded','Concluded'),  )

EVENTSUBKIND_CHOICES = ( ('Forecast', 'forecast'), ('Hindcast','hindcast'), ('Planning','planning'),)

CONTEXTBOUNDARY_CHOICES = ( ('Input', 'input'), ('Output', 'output'), ('InputOutput', 'inputOutput'), )

CONTEXTBOUNDARYLINEDATAKIND_CHOICES =  ( ('H', 'Depth'), ('Q', 'Discharge'), ('Z', 'Elevation'), ('V', 'Velocity'), )

TIME_UNITS = (('hour', 'Hour'), ('minute', 'Minute'), ('second', 'Second'))

class e_Context(models.Model):
	# Information/identification
	code         = models.CharField(primary_key=True, max_length=100, unique=True)
	Name         = models.CharField(max_length=100, unique=True)
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True) # Owner do contexto
	creator      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	create_date  = models.DateTimeField()
	isPublic     = models.BooleanField(default=False)
	
	# Context detail
	hydroFeature         = models.ForeignKey('rivercureportal.e_HydroFeature', on_delete=models.CASCADE, null=True, blank=True )
	geomExternalBoundary = models.MultiPolygonField(null=True, blank=True)  		#aka Domain
	CLExternalBoundary   = models.FloatField(null=True, blank=True)  			    #aka Domain's CL, characteristic lenght 
	hasMesh              = models.BooleanField(default=False)
	
	# For the pre-processing task
	task_id   = models.CharField(max_length=200, null=True)
	# Requester of a mesh generation request
	requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requester')

	class Meta:
		verbose_name = 'Context'
		verbose_name_plural = 'Contexts'

	def __str__(self):
		return self.Name

class e_ContextDTM(models.Model):
	context    = models.OneToOneField('e_Context', on_delete=models.CASCADE, related_name='context_dtm')
	contextDTM = models.OneToOneField('raster.RasterLayer', on_delete=models.CASCADE, related_name='dtm_endpoint') #This field corresponds to the context DTM (.tiff file)

	class Meta:
		verbose_name = 'Context DTM'
		verbose_name_plural = 'Context\'s DTMs'

	def __str__(self):
		return f"{self.context} context dtm"

class e_ContextDTMFile(models.Model):
	context = models.OneToOneField('e_Context', on_delete=models.CASCADE, related_name='context_dtm_file')
	raster  = models.FileField(null=True, blank=True) #This field corresponds to the context DTM (.tiff file)

	class Meta:
		verbose_name = 'Context DTM file'
		verbose_name_plural = 'Context\'s DTM files'

	def __str__(self):
		return f"{self.context} context dtm"

class e_ContextFrictionCoeff(models.Model):
	context = models.OneToOneField('e_Context', on_delete=models.CASCADE, related_name='context_contour_lines')
	raster  = models.FileField(null=True, blank=True)  		#aka contour lines

	class Meta:
		verbose_name = 'Context friction coefficient'
		verbose_name_plural = 'Context\'s friciton coefficients'

	def __str__(self):
		return f"{self.context} context friction coeffiecient"


class e_ContextRefinement(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE, related_name='context_refinement')
	geom    = models.PolygonField(null=True, blank=True) 			# aka Refinement
	CL      = models.FloatField(null=True, blank=True)  			#aka Refinement's CL

	class Meta:
		verbose_name = 'Context refinement'
		verbose_name_plural = 'Context\'s refinements'

	def __str__(self):
		return f"{self.context} context refinement"

class e_ContextAlignment(models.Model):
	context = models.ForeignKey('e_Context', on_delete=models.CASCADE, related_name='context_alignment')
	geom    = models.LineStringField(null=True, blank=True)   # aka Alignment
	CL      = models.FloatField(null=True, blank=True)   	  # Alignment's CL

	class Meta:
		verbose_name = 'Context alignment'
		verbose_name_plural = 'Context\'s alignments'

	def __str__(self):
		return f"{self.context} context alignment"

class  e_ContextBoundaryLine(models.Model):
	context  = models.ForeignKey('e_Context', on_delete=models.CASCADE, related_name='context_boundaries')
	geom     = models.LineStringField(null=True, blank=True) #superimposed "must be a line superimposed on context.geomExternalBoundary"))] 
	type     = models.CharField(max_length=30, choices=CONTEXTBOUNDARY_CHOICES)
	dataType = models.CharField(max_length=30, choices=CONTEXTBOUNDARYLINEDATAKIND_CHOICES, null=True)

	class Meta:
		verbose_name = 'Context boundary line'
		verbose_name_plural = 'Context\'s boundary lines'

	def __str__(self):
		return f"{self.context} context boundary line"

class  e_ContextBoundaryPoint(models.Model):
	contextBoundaryLine = models.ForeignKey('e_ContextBoundaryLine', on_delete=models.CASCADE, null=True, blank=False, related_name='context_boundary_points')
	geom                = models.PointField(null=True, blank=True) #superimposed "must be a point superimposed on e_ContextBoundaryLine.geom"))]  

	class Meta:
		verbose_name = 'Context boundary point'
		verbose_name_plural = 'Context\'s boundary points'

	def __str__(self):
		return f"{self.contextBoundaryLine} point"

class e_ContextSensor(models.Model):
	boundary_point    = models.ForeignKey('e_ContextBoundaryPoint', on_delete=models.CASCADE, null=True, related_name='sensor_boundary_point')
	sensor            = models.ForeignKey(to=Sensor, on_delete=models.CASCADE, related_name='context_sensor' )
	description       = models.TextField()
	associateDatetime = models.DateTimeField(default=timezone.now)

	class Meta:
		verbose_name = 'Context sensor'
		verbose_name_plural = 'Context\'s sensors'

	def __str__(self):
		return f"{self.boundary_point} sensor"

# A sensor has to be associated to Context before being associated with a point. Check ASL specification

class e_ContextEvent(models.Model):
	context     = models.ForeignKey('e_Context', on_delete=models.CASCADE)
	Name        = models.CharField(max_length=100, unique=True)
	type        = models.CharField(max_length=30, choices=EVENTKIND_CHOICES)
	subtype     = models.CharField(max_length=30, choices=EVENTSUBKIND_CHOICES, null=True, blank=True)
	state       = models.CharField(max_length=30, choices=EVENTSTATE_CHOICES)
	startDate   = models.DateField(verbose_name='Start date', default=date.today)
	startTime   = models.TimeField(verbose_name='Start time')
	endDate     = models.DateField(verbose_name='End date', default=date.today)
	endTime     = models.TimeField(verbose_name='End time')
	description = models.TextField()
	
	#Attributes for "Flood Simulation" event, with HiSTAV
	returnPeriod           = models.IntegerField(verbose_name='Return period', default=1)
	warmUp                 = models.BooleanField(verbose_name='Warm-up', default=False)
	WritingPeriodicity     = models.FloatField(verbose_name='Writing periodicity', default=1.0, null=True, blank=True)
	WritingPeriodicityUnit = models.CharField(verbose_name='Writing periodicity unit', max_length=20, choices= TIME_UNITS, null=True, blank=True) 
	UpdateMaximumValue     = models.FloatField(verbose_name='Update maximum value', default=1.0, null=True, blank=True)
	UpdateMaximumValueUnit = models.CharField(verbose_name='Update maximum value unit', max_length=20, choices= TIME_UNITS, null=True, blank=True) 
	hasSimulation          = models.BooleanField(default=False)

	# Celery simulation task
	task_id   = models.TextField(null=True)
	requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

	class Meta:
		verbose_name = 'Context event'
		verbose_name_plural = 'Context\'s events'

	def __str__(self):
		return f'{self.context} event {self.id}'

class e_ContextEventResult(models.Model):
	context_event = models.OneToOneField('e_ContextEvent', on_delete=models.CASCADE, related_name='context_event_results', null=True, blank=True, default=None)
	max_depth     = models.OneToOneField('raster.RasterLayer', on_delete=models.CASCADE, related_name='event_max_depth_result')
	max_level     = models.OneToOneField('raster.RasterLayer', on_delete=models.CASCADE, related_name='event_max_level_result')
	max_q         = models.OneToOneField('raster.RasterLayer', on_delete=models.CASCADE, related_name='event_max_q_result') 
	max_vel       = models.OneToOneField('raster.RasterLayer', on_delete=models.CASCADE, related_name='event_max_vel_result') 
	time          = models.DateTimeField(default=timezone.now)

	class Meta:
		verbose_name = 'Context event result'
		verbose_name_plural = 'Context\'s events results'

	def __str__(self):
		return f'{self.context_event} results'