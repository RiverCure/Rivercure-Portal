# from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from context.models import EVENTKIND_CHOICES
from django_fsm import FSMField, transition

import os
import subprocess
from datetime import datetime
from uuid import uuid4
from mimetypes import guess_type
from PIL import Image

from rivercureproject.settings import MEDIA_ROOT

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

    # Moderation
    state = FSMField(default=ContributionStatus.PENDING, choices=ContributionStatus.choices , protected=True) # protected=True prevents changing the state directly
    # TODO: Change these according to Domain Model
    last_validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="last_validated_by")
    last_validation_datetime =  models.DateTimeField(null=True, blank=True)
    last_rejection_reason = models.TextField(blank=True)

    # Information provided by the user
    observationDate = models.DateField()
    observationPlace = models.PointField()
    observationDescription = models.TextField()
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
        """
        Change the state of the Contribution from PENDING to ACCEPTED
        """

    @transition(field=state, source=ContributionStatus.PENDING, target=ContributionStatus.REJECTED)
    def reject(self):
        """
        Change the state of the Contribution from PENDING to REJECTED
        """
    
    @transition(field=state, source=ContributionStatus.ACCEPTED, target=ContributionStatus.PENDING)
    def report(self):
        """
        Report Contribution. This changes the state of the Contribution from ACCEPTED to PENDING
        """
    
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

    As indicated in: https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.FileField.upload_to
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
    
    def save(self, *args, **kwargs):
        super().save()

        file_path = self.file.path
        output_size = (300,300) # TODO: Is this a good size? Should it be higher?

        # If it's an image
        if self.is_video_or_image() == 'image':
            # We must resize it
            img = Image.open(file_path)

            if img.height > 300 or img.width > 300:
                img.thumbnail(output_size)
                img.save(file_path)
        
        # Video thumbnail
        # # Else, since it's a video, we must save a thumbnail (with the same output size as image)
        # else:
        #     video_path = file_path.split('.')[0]
        #     video_extension = file_path.split('.')[-1]
        #     img_output_path = video_path + "_thumb"


        #     # TODO: Do as subprocess instead?
        #     # TODO: RESIZE IMG HERE OR IN ANOTHER FOLLOWING SUPROCESS USING PILLOW?
        #     # subprocess.call(['ffmpeg', '-i', file_path, '-ss', '00:00:00.000', '-vframes', '1', img_output_path])

        #     try:
        #         (
        #             ffmpeg
        #             .input(in_filename, ss=time)
        #             .filter('scale', width, -1)
        #             .output(out_filename, vframes=1)
        #             .overwrite_output()
        #             .run(capture_stdout=True, capture_stderr=True)
        #         )
        #     except ffmpeg.Error as e:
        #         # Do nothing
        #         error = e.stderr.decode()

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


# class e_ContributionValidationHistory(models.Model):
#     contribution = models.ForeignKey(e_ContextContribution, on_delete=models.CASCADE, null=True) # Delete validation from DB if parent contribution is deleted TODO: Delete null=true right ?
#     state = models.CharField(max_length=30, choices=ContributionStatus.choices)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="contribution_validated_by")
#     creation_datetime =  models.DateTimeField(auto_now_add=True)
#     # Validation
#     rejection_reason = models.TextField(blank=True)
#     # Report
#     report_reason = models.TextField()

#     class Meta:
#         verbose_name = 'Contribution\'s Validation'
#         verbose_name_plural = 'Contribution\'s Validation History'
    
#     def __str__(self):
#         return "Contribution " + str(self.contribution.id) + " - " + self.state