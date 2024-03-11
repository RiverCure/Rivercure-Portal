# from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from context.models import EVENTKIND_CHOICES
from django_fsm import FSMField, transition
import os
from datetime import datetime
from uuid import uuid4

# States for a Contribution
class ContributionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"

# Contribution
class e_ContextContribution(models.Model):
    # Metadata
    #id = models.CharField(primary_key=True, max_length=100, unique=True)
    createdBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creationDateTime = models.DateTimeField(auto_now_add=True) # Date and time of creation of contribution
    context = models.ForeignKey('context.e_Context', on_delete=models.SET_NULL, null=True)
    contextEvent = models.ForeignKey('context.e_ContextEvent', on_delete=models.SET_NULL, null=True, blank=True)
    state = FSMField(default=ContributionStatus.PENDING, choices=ContributionStatus.choices , protected=True) # protected=True prevents changing the state directly
    validatedBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="validatedBy")
    validationDateTime =  models.DateTimeField(null=True, blank=True)

    # Information provided by the user
    observationDate = models.DateField()
    observationPlace = models.PointField()
    observationDescription = models.TextField() # TODO: Set max length?
    situationObserved = models.CharField(max_length=30, choices=EVENTKIND_CHOICES)

    # TODO: Add extra information asked depending on SituationObserved

    class Meta:
        verbose_name = 'Contribution'
        verbose_name_plural = 'Contributions'
        ordering = ['creationDateTime']
    
    def __str__(self):
        return str(self.id)
    
    @transition(field=state, source=ContributionStatus.PENDING, target=ContributionStatus.ACCEPTED)
    def accept(self):
        return
    
    @transition(field=state, source=ContributionStatus.PENDING, target=ContributionStatus.REJECTED)
    def reject(self):
        return


# For upload_to=
def create_media_file_name(instance, filename):
    """
    Callable that saves the upload path as: contributions/uploaded_files/%Y-%m-%d-%H%M%S-uuid4

    As indicated in: https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.FileField.upload_to
    """

    path = "contributions/uploaded_files/"
    extension = "." + filename.split('.')[-1]
    format = datetime.now().strftime('%Y-%m-%d-%H%M%S-') + str(uuid4()) + extension
    # format = instance.pk + '_' + instance + instance.file_extension
    return os.path.join(path, format)

# Attachment
class e_ContributionAttachment(models.Model):
    file = models.FileField('Attachment', upload_to=create_media_file_name)
    contribution = models.ForeignKey(e_ContextContribution, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Contribution\'s Attachment'
        verbose_name_plural = 'Contribution\'s Attachments'