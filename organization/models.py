from django.db import models
from django.contrib.auth.models import User

# Create your models here.

OrganizationKind_Choices = ( ('waterAuthority','Water Authority'), ('municipality','Municipality'), ('researchLab','Research Lab'), ('partner','Partner'), ('other','Other'),)
Country_Choices = ( ('pt', 'Portugal'), ('br', 'Brasil'))
City_Choices = ( ('coimbra', 'Coimbra'), ('lisboa', 'Lisboa'))

class Organization(models.Model):
    name     = models.CharField(max_length=50, null=True)
    type     = models.CharField(max_length=50, choices=OrganizationKind_Choices)
    # sector  = models.CharField(max_length=50, null=True)
    # address = models.CharField(max_length=80, null=True)
    country  = models.CharField(max_length=80, choices=Country_Choices)
    city     = models.CharField(max_length=80, choices=City_Choices)
    manager  = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    # email   = models.EmailField(max_length=254)
    # phone   = models.CharField(max_length=15)
    isPublic = models.BooleanField(default=True)


class OrganizationAccessRequest(models.Model):
	requester = models.ForeignKey(User, on_delete=models.CASCADE)
	organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
	access_granted = models.BooleanField(default=False)
	access_grant_date = models.DateTimeField(null=True)

    