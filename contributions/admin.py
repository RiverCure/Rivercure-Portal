from django.contrib import admin
from .models import e_ContextContribution, e_ContributionAttachment, e_ContributionReport

# Register your models here.
admin.site.register(e_ContextContribution)
admin.site.register(e_ContributionAttachment)
admin.site.register(e_ContributionReport)