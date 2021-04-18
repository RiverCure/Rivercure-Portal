from django.db import models
from django.contrib.auth.models import User

# Create your models here.

OrganizationKind_Choices = ( ('waterAuthority','Water Authority'), ('municipality','Municipality'), ('researchLab','Research Lab'), ('partner','Partner'), ('other','Other'),)
Country_Choices = ( ('pt', 'Portugal'), ('br', 'Brasil'))
City_Choices = ( ('coimbra', 'Coimbra'), ('lisboa', 'Lisboa'))
Permissions = (('org_manager', 'Manager'), ('org_contextManager', 'Context Manager'), ('org_sensorManager', 'Sensor Manager'), ('org_member', 'Member'))

class Organization(models.Model):
    name     = models.CharField(max_length=50, null=True)
    type     = models.CharField(max_length=50, choices=OrganizationKind_Choices)
    # sector  = models.CharField(max_length=50, null=True)
    # address = models.CharField(max_length=80, null=True)
    country  = models.CharField(max_length=80, choices=Country_Choices)
    city     = models.CharField(max_length=80, choices=City_Choices)
    # email   = models.EmailField(max_length=254)
    # phone   = models.CharField(max_length=15)
    members  = models.ManyToManyField(User, through='Membership')
    isPublic = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user')
    create_date = models.DateTimeField()

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    access_granted = models.BooleanField(default=False)
    access_grant_date = models.DateTimeField(null=True)
    permission = models.CharField(max_length=80, choices=Permissions, null=True)

    def __str__(self):
        return f"{self.user} - {self.organization}"