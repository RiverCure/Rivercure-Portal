from django.contrib import admin
from .models import e_Challenge, e_Question, e_ShortText_Question, e_MultipleChoiceOption_Question, e_TrueFalse_Question, e_ChallengeAnswer, e_QuestionAnswer

# Register your models here.
admin.site.register(e_Challenge)
admin.site.register(e_Question)
admin.site.register(e_ShortText_Question)
admin.site.register(e_MultipleChoiceOption_Question)
admin.site.register(e_TrueFalse_Question)
admin.site.register(e_ChallengeAnswer)
admin.site.register(e_QuestionAnswer)