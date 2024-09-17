from django.contrib import admin
from .models import e_ContextContribution, e_ContributionAttachment, e_ContributionReport, e_ContributionValidation

# Register your models here.
admin.site.register(e_ContextContribution)
admin.site.register(e_ContributionAttachment)
admin.site.register(e_ContributionReport)
admin.site.register(e_ContributionValidation)