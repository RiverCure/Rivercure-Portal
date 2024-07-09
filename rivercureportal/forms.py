from django import forms

from django.contrib.gis.db import models

class Subject_Choices(models.TextChoices):
    REQUEST_CONTEXT = "REQUEST_CONTEXT", "Request Context"
    QUESTIONS = "QUESTIONS", "Questions"
    FEEDBACK = "FEEDBACK", "Feedback"
    OTHER = "OTHER", "Other"

class ContactForm(forms.Form):
    # email = forms.EmailField(widget=forms.TextInput(attrs={"placeholder": "Your e-mail."}))
    subject = forms.ChoiceField(choices=Subject_Choices.choices)
    message = forms.CharField(widget=forms.Textarea(attrs={"placeholder": "Your message."}))