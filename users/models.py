from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from rivercureportal.models import e_Country, e_City

OrganizationKind_Choices = ( ('waterAuthority','WaterAuthority'), ('municipality','Municipality'), ('researchLab','ResearchLab'), ('partner','Partner'), ('other','Other'),)



class Organization(models.Model):
    name =  models.CharField(max_length=50, null=True)
    type =  models.CharField(max_length=50, choices= OrganizationKind_Choices)
    sector =  models.CharField(max_length=50, null=True)
    address =  models.CharField(max_length=80, null=True)
    city = models.ForeignKey('rivercureportal.e_City', on_delete=models.CASCADE)
    country = models.ForeignKey('rivercureportal.e_Country', on_delete=models.CASCADE)
    email =  models.EmailField(max_length=254)
    phone =  models.CharField(max_length=15)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=20, null=True)
    last_name = models.CharField(max_length=20, null=True)
    institution = models.CharField(max_length=50, null=True)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True)
    image = models.ImageField(default='default.jpg', upload_to="profile_pics")

    def __str__(self):
        return f'{self.user.username} profile'

    #SAVE ALWAYS RUNS BUT WE'RE ADDING THE RESIZE FUNCTION
    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300,300)
            img.thumbnail(output_size)
            img.save(self.image.path)