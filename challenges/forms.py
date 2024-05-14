from django import forms

from django.forms import modelformset_factory

from .models import e_Challenge, e_Question, DIFFICULTY_LEVEL, e_MultipleChoiceOption_Question, e_TrueFalse_Question

class ChallengeForm(forms.ModelForm):
    title = forms.CharField(max_length=100,
                            widget=forms.Textarea(attrs={
                                            'placeholder': 'Enter a title for the Challenge. Maximum of 100 characters.',
                                            'class': 'form-control',
                                        }),
                            label='Title')
    
    difficulty_level = forms.ChoiceField(choices=DIFFICULTY_LEVEL,
                                         help_text='This serves as information to participants.',
                                         label='Difficulty Level')
    is_public = forms.BooleanField(label='Is Public',
                                   help_text='If Challenge is Public, every logged-in user can participate in it. If it isn\'t, only members of the Organization can.',
                                   required=False)

    class Meta:
        model = e_Challenge
        fields = ['id', 'title', 'difficulty_level', 'is_public']



class QuestionForm(forms.ModelForm):
    content = forms.CharField(max_length=100,
                            widget=forms.Textarea(attrs={
                                            'placeholder': 'Enter the question. Maximum of 500 characters.',
                                            'class': 'form-control',
                                        }),
                            label='Question Content')
    
    class Meta:
        model = e_Question
        fields = ['id', 'content', 'type']



class QuestionUpdateForm(forms.ModelForm):
    content = forms.CharField(max_length=100,
                            widget=forms.Textarea(attrs={
                                            'placeholder': 'Enter the question. Maximum of 500 characters.',
                                            'class': 'form-control',
                                        }),
                            label='Question Content')
    
    class Meta:
        model = e_Question
        fields = ['id', 'content']


class QuestionShortTextForm(forms.Form):
    correct_text = forms.CharField(max_length=1000,
                            widget=forms.Textarea(attrs={
                                            'placeholder': 'Enter the correct answer for this Question. Maximum of 1000 characters.',
                                            'class': 'form-control',
                                        }),
                            label='Correct Answer')


class QuestionMultipleChoiceForm(forms.ModelForm):
    content = forms.CharField(max_length=500,
                            widget=forms.TextInput(attrs={
                                            'placeholder': 'Enter the content for this Option. Maximum of 500 characters.',
                                            'class': 'form-control',
                                        }),
                            label='Option Content')
    is_correct = forms.BooleanField(label='Is Correct',
                                   required=False)
    
    class Meta:
        model = e_MultipleChoiceOption_Question
        exclude = ('question',)

QuestionMultipleChoiceFormSet = modelformset_factory(e_MultipleChoiceOption_Question, form=QuestionMultipleChoiceForm)


class QuestionTrueFalseForm(forms.ModelForm):
    content = forms.CharField(max_length=500,
                            widget=forms.TextInput(attrs={
                                            'placeholder': 'Enter the content for this Option. Maximum of 500 characters.',
                                            'class': 'form-control',
                                        }),
                            label='Option Content')
    value = forms.BooleanField(label='True?',
                                required=False)
    
    class Meta:
        model = e_TrueFalse_Question
        exclude = ('question',)

QuestionTrueFalseFormSet = modelformset_factory(e_TrueFalse_Question, form=QuestionTrueFalseForm)