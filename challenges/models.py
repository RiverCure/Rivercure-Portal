# from django.db import models
from django.core.validators import MinValueValidator

from django.contrib.gis.db import models
from django.contrib.auth.models import User

from django_fsm import FSMField, transition



## Choices
class ChallengeState(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    DELETED = "DELETED", "Deleted"
    PUBLISHED = "PUBLISHED", "Published"
    ARCHIVED = "ARCHIVED", "Archived"


# TODO: Turn this into a TextChoice
DIFFICULTY_LEVEL = (('easy', 'Easy'), ('intermediate', 'Intermediate'), ('hard', 'Hard'))


class Question_Type(models.TextChoices):
    SHORT_TEXT = "SHORT_TEXT", "Short Text"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE", "Multiple Choice"
    TRUE_FALSE = "TRUE_FALSE", "True or False"



## Models
class e_Challenge(models.Model):
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey('context.e_ContextEvent', on_delete=models.SET_NULL, null=True)
    nr_questions = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    state = FSMField(choices=ChallengeState.choices, default=ChallengeState.DRAFT, protected=True) # When first created, the Challenge is in Draft state
    publish_datetime = models.DateTimeField(null=True, blank=True)

    # Information
    title = models.CharField(max_length=100)
    difficulty_level = models.CharField(choices=DIFFICULTY_LEVEL)
    is_public = models.BooleanField(default=False) # If false, only members of Org can see. If True, every logged-in user can see
    # TODO: Add score concept


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
    
    def can_manage_questions(self):
        """
        Returns whether Challenge can have its Questions managed
        
        Conditions: Challenge is a DRAFT
        """
        return self.state == ChallengeState.DRAFT
    
    # State transitions
    @transition(field=state, source=ChallengeState.DRAFT, target=ChallengeState.DELETED) # TODO: Add condition
    def to_delete(self):
        """Change state of Challenge from DRAFT to DELETED"""
    
    @transition(field=state, source=ChallengeState.DRAFT, target=ChallengeState.PUBLISHED, conditions=[can_publish])
    def to_publish(self):
        """Change state of Challenge from DRAFT to PUBLISHED"""
    
    @transition(field=state, source=ChallengeState.PUBLISHED, target=ChallengeState.ARCHIVED) # TODO: Add condition
    def to_archive(self):
        """Change state of Challenge from PUBLISHED to ARCHIVED"""


# We are not using neither of Django's options for inheritance (Abstract model or Multi-table)
# This is the Question model
# The other objects that follow act as complementary information to this object
class e_Question(models.Model):
    # Meta-data
    challenge = models.ForeignKey(e_Challenge, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_by')
    creation_datetime = models.DateTimeField(auto_now_add=True)
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='last_edited_by', blank=True)
    last_edit_datetime = models.DateTimeField(null=True, blank=True)
    type = models.CharField(choices=Question_Type.choices)

    # Question
    content = models.CharField(max_length=500) # Question itself
    # explanation = models.CharField(max_length=500) # Explanation of correct answer

    # Model methods
    def is_short_text(self):
        return self.type == Question_Type.SHORT_TEXT
    
    def is_multiple_choice(self):
        return self.type == Question_Type.MULTIPLE_CHOICE
    
    def is_true_false(self):
        return self.type == Question_Type.TRUE_FALSE

    # Meta
    # class Meta:
    #     abstract = True

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['creation_datetime']
    
    def __str__(self):
        return "Question " + str(self.id) + ' (Challenge ' + str(self.challenge.id) + ")"


class e_ShortText_Question(models.Model):
    question = models.OneToOneField(e_Question, on_delete=models.CASCADE, related_name='short_text_question')
    correct_text = models.CharField(max_length=1000)

    # Meta
    class Meta:
        verbose_name = 'Question - Short Text'
        verbose_name_plural = 'Questions - Short Text'
    
    def __str__(self):
        return "Short Text " + str(self.id) + ' (Question ' + str(self.question.id) + " - Challenge " + str(self.question.challenge.id) + ")"


class e_MultipleChoiceOption_Question(models.Model):
    question = models.ForeignKey(e_Question, on_delete=models.CASCADE, related_name='multiple_choice_option_question')
    content = models.CharField(max_length=500) # Option content
    is_correct = models.BooleanField()
    
    # Meta
    class Meta:
        verbose_name = 'Question - Multiple Choice Option'
        verbose_name_plural = 'Questions - Multiple Choice Options'
    
    def __str__(self):
        return "Multiple Choice Option " + str(self.id) + ' (Question ' + str(self.question.id) + " - Challenge " + str(self.question.challenge.id) + ")"


class e_TrueFalse_Question(models.Model):
    question = models.ForeignKey(e_Question, on_delete=models.CASCADE, related_name='true_false_question')
    content = models.CharField(max_length=500) # Option content
    value = models.BooleanField() # If is True or False

    # Meta
    class Meta:
        verbose_name = 'Question - True or False Option'
        verbose_name_plural = 'Questions - True or False Options'
    
    def __str__(self):
        return "True or False Option " + str(self.id) + ' (Question ' + str(self.question.id) + " - Challenge " + str(self.question.challenge.id) + ")"





# class e_ShortText_Question(e_Question):
#     expected_answer = models.CharField(max_length=1000)

#     def get_type(self):
#         return Question_Type.SHORT_TEXT

#     # Meta
#     class Meta:
#         verbose_name = 'Question - Short Text'
#         verbose_name_plural = 'Questions - Short Text'
    
#     def __str__(self):
#         return "Short Text " + str(self.id) + ' (Challenge ' + str(self.challenge.id) + ")"