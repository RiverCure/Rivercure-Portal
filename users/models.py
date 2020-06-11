from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=20, default="default")
    last_name = models.CharField(max_length=20, default="default")
    institution = models.CharField(max_length=50, default="default")

    def __str__(self):
        return f'{ self.user.username } profile'
