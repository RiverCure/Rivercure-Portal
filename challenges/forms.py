from django import forms

from .models import e_Challenge, DIFFICULTY_LEVEL

class ChallengeInitialForm(forms.ModelForm):
    title = forms.CharField(max_length=100,
                            widget=forms.Textarea(attrs={
                                            'placeholder': 'Enter a title for the Challenge. Maximum of 100 characters.',
                                            'class': 'form-control',
                                        }),
                            label='Title')
    
    difficulty_level = forms.ChoiceField(choices=DIFFICULTY_LEVEL,
                                         help_text='This serves as information to participants.',
                                         label='Difficulty Level')

    class Meta:
        model = e_Challenge
        fields = ['id', 'title', 'difficulty_level']