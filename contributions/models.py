from django.db import models
from django.contrib.auth.models import User
from context.models import EVENTKIND_CHOICES

# Create your models here.
class e_ContextContribution(models.Model):
    # Metadata
    id = models.CharField(primary_key=True, max_length=100, unique=True)
    creationAuthor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    context = models.ForeignKey('context.e_Context', on_delete=models.SET_NULL, null=True)
    contextEvent = models.ForeignKey('context.e_ContextEvent', on_delete=models.SET_NULL, null=True, blank=True)
    creationDateTime = models.DateTimeField(auto_now_add=True) # Date of creation of contribution in DB/submission by user
    # TODO: state ; use django-fsm
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="moderator")
    validationDateTime =  models.DateTimeField(null=True, blank=True) # TODO: Add null or blank? How to allow this field to be empty on creation of the row?

    # Information provided by the user
    observationDateTime = models.DateTimeField()
    # TODO: observationPlace ; SEE what the best way to do this is (depends on how we'll be collecting the geolocation)
    observationDescription = models.TextField()
    # TODO: Images
    # TODO: Videos
    situationObserved = models.CharField(max_length=30, choices=EVENTKIND_CHOICES)

    # TODO: Add extra information asked depending on SituationObserved

    class Meta:
        verbose_name = 'Contribution'
        verbose_name_plural = 'Contributions'
    
    def __str__(self):
        return self.id