import os
import subprocess

from django_fsm import FSMField, transition
from datetime import datetime
from uuid import uuid4
from mimetypes import guess_type
from PIL import Image

from django.utils.translation import gettext_lazy as _

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User

from context.models import EVENTKIND_CHOICES
from rivercureproject.settings import MEDIA_ROOT

# States for a Contribution
class ContributionStatus(models.TextChoices):
    PENDING = _("PENDING"), _("Pending")
    ACCEPTED = _("ACCEPTED"), _("Accepted")
    REJECTED = _("REJECTED"), _("Rejected")
    REPORTED = _("REPORTED"), _("Reported")

class SituationChoices(models.TextChoices):
    FLOOD = _("FLOOD"), _("Flood")
    HEAVY_PRECIPITATION = _("HEAVY_PRECIPITATION"), _("Heavy Precipitation")
    DROUGHT = _("DROUGHT"), _("Drought")
    STORM = _("STORM"), _("Storm")
    TSUNAMI = _("TSUNAMI"), _("Tsunami")
    TORNADO = _("TORNADO"), _("Tornado")
    LANDSLIDE = _("LANDSLIDE"), _("Landslide")
    RIVER_POLLUTION = _("RIVER_POLLUTION"), _("River Pollution")

# TODO: Repeated code in here!
def create_contribution_thumbnail_name(instance, filename):
    """
    Callable that saves the file with the path and name: contributions/uploaded_files/organization_name/context_code/year/month/day/thumb_uuid4.ext
    """

    organization = instance.context.organization
    _context = instance.context.code
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    day = datetime.now().strftime('%d')
    # Path is: contributions/uploaded_files/organization_name/context_code/year/month/day
    path = "contributions/uploaded_files/{}/{}/{}/{}/{}".format(organization, _context, year, month, day)
    extension = "." + filename.split('.')[-1]
    
    # Filename is: thumb-uuid4.ext
    format = "thumb-" + str(uuid4()) + extension

    return os.path.join(path, format)


# Contribution
class e_ContextContribution(models.Model):
    # Metadata
    #id = models.CharField(primary_key=True, max_length=100, unique=True)
    createdBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creationDateTime = models.DateTimeField(auto_now_add=True) # Date and time of creation of contribution
    context = models.ForeignKey('context.e_Context', on_delete=models.SET_NULL, null=True)
    contextEvent = models.ForeignKey('context.e_ContextEvent', on_delete=models.SET_NULL, null=True, blank=True)
    total_file_size = models.FloatField(default=0.000)
    thumbnail = models.ImageField(upload_to=create_contribution_thumbnail_name, blank=True, null=True)

    # Moderation
    state = FSMField(default=ContributionStatus.PENDING, choices=ContributionStatus.choices , protected=True) # protected=True prevents changing the state directly
    last_validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="last_validated_by")
    last_validation_datetime =  models.DateTimeField(null=True, blank=True)
    last_rejection_reason = models.TextField(blank=True)

    # Information provided by the user
    observationDate = models.DateField()
    observationPlace = models.PointField()
    observationAddress = models.CharField(max_length=300, blank=True)
    observationDescription = models.TextField()
    situationObserved = models.CharField(max_length=30, choices=SituationChoices.choices)

    # TODO: Add extra information asked depending on SituationObserved

    class Meta:
        verbose_name = 'Contribution'
        verbose_name_plural = 'Contributions'
        ordering = ['creationDateTime']
    
    def save(self, *args, **kwargs):
        # Save runs first
        super().save()

        # Re-size thumbnail (if it exists)
        if self.thumbnail:
            file_path = self.thumbnail.path

            output_size = (300,300)
            img = Image.open(file_path)

            if img.height > 300 or img.width > 300:
                img.thumbnail(output_size)
                img.save(file_path)
            
    
    def __str__(self):
        return str(self.id)
    
    @transition(field=state, source=[ContributionStatus.PENDING, ContributionStatus.REJECTED, ContributionStatus.REPORTED], target=ContributionStatus.ACCEPTED)
    def accept(self):
        """
        Change the state of the Contribution from PENDING/REJECTED to ACCEPTED
        """

    @transition(field=state, source=[ContributionStatus.PENDING, ContributionStatus.ACCEPTED], target=ContributionStatus.REJECTED)
    def reject(self):
        """
        Change the state of the Contribution from PENDING/ACCEPTED to REJECTED
        """
    
    @transition(field=state, source=ContributionStatus.ACCEPTED, target=ContributionStatus.REPORTED)
    def report(self):
        """
        Report Contribution. This changes the state of the Contribution from ACCEPTED to PENDING
        """
    
    def is_pending(self):
        """
        Returns whether Contribution is in state Pending
        """
        return self.state == ContributionStatus.PENDING
    
    def can_accept(self):
        """
        Returns whether Contribution can be accepted (aka if it's in state PENDING or REJECTED or REPORTED)
        """
        return (self.state == ContributionStatus.PENDING) or (self.state == ContributionStatus.REJECTED) or (self.state == ContributionStatus.REPORTED)
    
    def can_reject(self):
        """
        Returns whether Contribution can be rejected (aka if it's in state PENDING or ACCEPTED)
        """
        return (self.state == ContributionStatus.PENDING) or (self.state == ContributionStatus.ACCEPTED)
    
    def get_long(self):
        """
        Returns the longitude for this contribution's location
        """
        return self.observationPlace.x
    
    def get_lat(self):
        """
        Returns the latitude for this contribution's location
        """
        return self.observationPlace.y


# For upload_to
def create_media_file_name(instance, filename):
    """
    Callable that saves the file with the path and name: contributions/uploaded_files/organization_name/context_code/year/month/day/uuid4.ext

    As indicated in: https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.FileField.upload_to
    """

    organization = instance.contribution.context.organization
    _context = instance.contribution.context.code
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    day = datetime.now().strftime('%d')
    # Path is: contributions/uploaded_files/organization_name/context_code/year/month/day
    path = "contributions/uploaded_files/{}/{}/{}/{}/{}".format(organization, _context, year, month, day)
    extension = "." + filename.split('.')[-1]
    
    # Filename is: uuid4.ext
    format = str(uuid4()) + extension

    return os.path.join(path, format)

# Attachment
class e_ContributionAttachment(models.Model):
    file = models.FileField('Attachment', upload_to=create_media_file_name)
    contribution = models.ForeignKey(e_ContextContribution, on_delete=models.CASCADE, null=True) # Delete attachment from DB if parent contribution is deleted
    file_size = models.FloatField(null=True, blank=True)
    # video_thumbnail = models.ImageField(null=True, blank=True) # Only if attachment is a video

    class Meta:
        verbose_name = 'Contribution\'s Attachment'
        verbose_name_plural = 'Contribution\'s Attachments'
    
    def is_video_or_image(self):
        """
        Returns whether attachment is a video or an image
        """
        type_tuple = guess_type(self.file.url, strict=True)
        if (type_tuple[0]).__contains__("image"):
            return "image"
        elif (type_tuple[0]).__contains__("video"):
            return "video"

    def get_type(self):
        """
        Returns type of attachment
        """
        type_tuple = guess_type(self.file.url, strict=True)
        return type_tuple[0]
    
    #SAVE ALWAYS RUNS BUT WE'RE ADDING THE RESIZE FUNCTION
    def save(self, *args, **kwargs):
        # Save
        super().save()

        # Resize image
        file_path = self.file.path
        output_size = (800,800)

        # If it's an image
        if self.is_video_or_image() == 'image':
            # We must resize it
            img = Image.open(file_path)

            if img.height > 800 or img.width > 800:
                img.thumbnail(output_size)
                img.save(file_path)



# For Validation History
# Keep a record of every validation state the Contribution has been in
class e_ContributionValidation(models.Model):
    contribution = models.ForeignKey(e_ContextContribution, on_delete=models.CASCADE, null=True) # Delete validation from DB if parent contribution is deleted TODO: Delete null=true right ?
    state = models.CharField(max_length=30, choices=ContributionStatus.choices)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="validated_by")
    validation_datetime =  models.DateTimeField(auto_now_add=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Contribution\'s Validation'
        verbose_name_plural = 'Contribution\'s Validations'
    
    def __str__(self):
        return "Contribution " + str(self.contribution.id) + " - " + self.state

# Keep a record of every report made to a Contribution
class e_ContributionReport(models.Model):
    contribution = models.ForeignKey(e_ContextContribution, on_delete=models.CASCADE, null=True) # Delete report from DB if parent contribution is deleted TODO: Delete null=true right ?
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    report_datetime = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()

    class Meta:
        verbose_name = 'Contribution\'s Report'
        verbose_name_plural = 'Contribution\'s Reports'
    
    def __str__(self):
        return "Contribution " + str(self.contribution.id)
