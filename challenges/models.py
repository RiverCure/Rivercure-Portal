# from django.db import models
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

from django_fsm import FSMField, transition

class ChallengeState(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    DELETED = "DELETED", "Deleted"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"

DIFFICULTY_LEVEL = (('easy', 'Easy'), ('intermediate', 'Intermediate'), ('hard', 'Hard'))

class e_Challenge(models.Model):
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey('context.e_ContextEvent', on_delete=models.SET_NULL, null=True)
    nr_questions = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    # Information
    title = models.CharField(max_length=100)
    difficulty_level = models.CharField(choices=DIFFICULTY_LEVEL)
    # TODO: Add score concept

    # When first created, the Challenge is in Draft state
    state = FSMField(choices=ChallengeState.choices, default=ChallengeState.DRAFT, protected=True) # protected=True prevents changing the state directly

    # Meta
    class Meta:
        verbose_name = 'Challenge'
        verbose_name_plural = 'Challenges'
        ordering = ['creation_datetime']
    
    def __str__(self):
        return "Challenge " + str(self.id)
    
    # Functions
    def can_publish(self):
        """
        Returns whether Challenge can be published

        Conditions: Challenge is a DRAFT and has >0 questions
        """
        return (self.state == ChallengeState.DRAFT) and (self.nr_questions > 0)
    
    def can_delete(self):
        """
        Returns whether Challenge can be deleted

        Conditions: Challenge is a DRAFT
        """
        return self.state == ChallengeState.DRAFT
    
    def can_archive(self):
        """
        Returns whether Challenge can be archived

        Conditions: Challenge is published
        """
        return self.state == ChallengeState.PUBLISHED
    
    # State transitions
    @transition(field=state, source=ChallengeState.DRAFT, target=ChallengeState.DELETED)
    def to_delete(self):
        """Change state of Challenge from DRAFT to DELETED"""
    
    @transition(field=state, source=ChallengeState.DRAFT, target=ChallengeState.PUBLISHED, conditions=[can_publish])
    def to_publish(self):
        """Change state of Challenge from DRAFT to PUBLISHED"""
    
    @transition(field=state, source=ChallengeState.PUBLISHED, target=ChallengeState.ARCHIVED)
    def to_archive(self):
        """Change state of Challenge from PUBLISHED to ARCHIVED"""