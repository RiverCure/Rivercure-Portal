from datetime import datetime

from django import forms

from django.forms import modelformset_factory

from django.utils.translation import gettext_lazy as _

from .models import e_Challenge, e_Question, DIFFICULTY_LEVEL, e_ShortText_Question, e_MultipleChoiceOption_Question, e_TrueFalse_Question

class ChallengeForm(forms.ModelForm):
    title = forms.CharField(max_length=100,
                            widget=forms.Textarea(attrs={
                                            'placeholder': _('Enter a title for the Quiz. Maximum of 100 characters.'),
                                            'class': 'form-control',
                                        }),
                            label=_('Title'))
    
    difficulty_level = forms.ChoiceField(choices=DIFFICULTY_LEVEL,
                                         help_text=_('This serves as information to participants.'),
                                         label=_('Difficulty Level'))
    is_public = forms.BooleanField(label=_('Is Public'),
                                   help_text=_('If Quiz is Public, every logged-in user can participate in it. If it isn\'t, only members of the Organization can.'),
                                   required=False)
    # automatic_close_datetime = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date','min': datetime.now().date()}),
    #                                           help_text=_('If specified, the Quiz will be automatically closed on this date.'),
    #                                           label=_('Automatic Closing Date'),
    #                                           required=False)
    when_close_show_correct_answers = forms.BooleanField(help_text=_('If yes, correct answers will only be shown to participating users when the Quiz is closed.'),
                                                         label=_('Only show correct answers when closed?'),
                                                         required=False)
    max_participations = forms.IntegerField(help_text=_('Number of times a user can participate.'),
                                            label=_('Max Number of Participations (per user)'))

    class Meta:
        model = e_Challenge
        fields = ['id', 'title', 'difficulty_level', 'is_public', 'when_close_show_correct_answers', 'max_participations']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['max_participations'].initial = 1



class QuestionForm(forms.ModelForm):
    content = forms.CharField(max_length=500,
                            widget=forms.Textarea(attrs={
                                            'placeholder': _('Enter the question. Maximum of 500 characters.'),
                                            'class': 'form-control',
                                        }),
                            label=_('Question Content'))
    
    class Meta:
        model = e_Question
        fields = ['id', 'content', 'type', 'score']


class QuestionUpdateForm(forms.ModelForm):
    content = forms.CharField(max_length=100,
                            widget=forms.Textarea(attrs={
                                            'placeholder': _('Enter the question. Maximum of 500 characters.'),
                                            'class': 'form-control',
                                        }),
                            label='Question Content')
    
    class Meta:
        model = e_Question
        fields = ['id', 'content', 'score']


class QuestionShortTextForm(forms.ModelForm):
    correct_text = forms.CharField(max_length=500,
                            widget=forms.Textarea(attrs={
                                            'placeholder': _('Enter the correct answer for this Question. Maximum of 500 characters.'),
                                            'class': 'form-control',
                                        }),
                            label=_('Correct Answer'))
    
    class Meta:
        model = e_ShortText_Question
        exclude = ('question',)


class QuestionMultipleChoiceForm(forms.ModelForm):
    content = forms.CharField(max_length=500,
                            widget=forms.TextInput(attrs={
                                            'placeholder': _('Enter the content for this Option. Maximum of 500 characters.'),
                                            'class': 'form-control',
                                        }),
                            label=_('Option Content'))
    is_correct = forms.BooleanField(label=_('Is Correct'),
                                   required=False)
    
    class Meta:
        model = e_MultipleChoiceOption_Question
        exclude = ('question',)

QuestionMultipleChoiceFormSet = modelformset_factory(e_MultipleChoiceOption_Question, form=QuestionMultipleChoiceForm)


class QuestionTrueFalseForm(forms.ModelForm):
    content = forms.CharField(max_length=500,
                            widget=forms.TextInput(attrs={
                                            'placeholder': _('Enter the content for this Option. Maximum of 500 characters.'),
                                            'class': 'form-control',
                                        }),
                            label=_('Option Content'))
    value = forms.BooleanField(label=_('True?'),
                                required=False)
    
    class Meta:
        model = e_TrueFalse_Question
        exclude = ('question',)

QuestionTrueFalseFormSet = modelformset_factory(e_TrueFalse_Question, form=QuestionTrueFalseForm)