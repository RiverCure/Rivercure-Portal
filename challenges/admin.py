from django.contrib import admin
from .models import e_Challenge, e_Question, e_ShortText_Question

# Register your models here.
admin.site.register(e_Challenge)
admin.site.register(e_Question)
admin.site.register(e_ShortText_Question)