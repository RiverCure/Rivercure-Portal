from django.contrib.gis.db import models
from rivercureportal.models import e_HydroFeature

class e_Context(models.Model):
	code = models.CharField(max_length=100, unique=True)

	Name = models.CharField(max_length=100, unique=True)

	hydroFeature = models.ForeignKey('rivercureportal.e_HydroFeature', on_delete=models.CASCADE, null=True, blank=False )

	#GEOPOLYGON
	geom = models.MultiPolygonField(null=True)

	def __str__(self):
		return self.Name



	