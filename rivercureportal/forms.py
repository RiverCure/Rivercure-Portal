from django import forms

from django.utils.translation import gettext_lazy as _

from django.contrib.gis.db import models

class Subject_Choices(models.TextChoices):
    REQUEST_CONTEXT = "REQUEST_CONTEXT", _("Request Context")
    QUESTIONS = "QUESTIONS", _("Questions")
    FEEDBACK = "FEEDBACK", "Feedback"
    OTHER = "OTHER", _("Other")

class ContactForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={"placeholder": _("Your email address"),
                                                           "class": "form-control",
                                                           "id": "inputEmail",
                                                           "aria-describedby":"emailHelp"}))
    subject = forms.ChoiceField(choices=Subject_Choices.choices,
                                widget=forms.Select(attrs={'class':'form-control',
                                                           'id':'selectSubject'}))
    message = forms.CharField(widget=forms.Textarea(attrs={"placeholder": _("Your message"),
                                                           'class':'form-control'}))