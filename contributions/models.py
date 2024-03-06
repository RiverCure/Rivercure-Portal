from django.db import models
from django.contrib.auth.models import User
from context.models import EVENTKIND_CHOICES
from django_fsm import FSMField, transition

# States for a Contribution
class ContributionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"

class e_ContextContribution(models.Model):
    # Metadata
    #id = models.CharField(primary_key=True, max_length=100, unique=True)
    createdBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creationDateTime = models.DateTimeField(auto_now_add=True) # Date of creation of contribution
    context = models.ForeignKey('context.e_Context', on_delete=models.SET_NULL, null=True)
    contextEvent = models.ForeignKey('context.e_ContextEvent', on_delete=models.SET_NULL, null=True, blank=True)
    state = FSMField(default=ContributionStatus.PENDING, choices=ContributionStatus.choices , protected=True) # protected=True prevents changing the state directly
    validatedBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="validatedBy")
    validationDateTime =  models.DateTimeField(null=True, blank=True)

    # Information provided by the user
    observationDate = models.DateField()
    # TODO: observationPlace ; SEE what the best way to do this is (depends on how we'll be collecting the geolocation)
    observationDescription = models.TextField() # TODO: Set max length?
    situationObserved = models.CharField(max_length=30, choices=EVENTKIND_CHOICES)

    # TODO: Add extra information asked depending on SituationObserved

    class Meta:
        verbose_name = 'Contribution'
        verbose_name_plural = 'Contributions'
    
    def __str__(self):
        return str(self.id)
    
    @transition(field=state, source=ContributionStatus.PENDING, target=ContributionStatus.ACCEPTED)
    def accept(self):
        return
    
    @transition(field=state, source=ContributionStatus.PENDING, target=ContributionStatus.REJECTED)
    def reject(self):
        return

class e_ContributionAttachment(models.Model):
    file = models.FileField('Attachment', upload_to="contributions")
    contribution = models.ForeignKey(e_ContextContribution, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Contribution\'s Attachment'
        verbose_name_plural = 'Contribution\'s Attachments'