from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin, LeafletGeoAdminMixin
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint

class ContextBoundaryPointInLine(LeafletGeoAdminMixin, admin.StackedInline):
    model = e_ContextBoundaryPoint
    # classes = ['collapse']
    fields = ['geom', 'sensor']
    # readonly_fields = ['geom']
    extra = 0

class ContextBoundaryLineInLine(LeafletGeoAdminMixin, admin.StackedInline):
    model = e_ContextBoundaryLine
    # classes = ['collapse']
    fields = ['type', 'dataType', 'geom']
    # readonly_fields = ['geom']
    extra = 0

class ContextBoundaryPointDetail(LeafletGeoAdmin):
    search_fields = ['contextBoundaryLine',]
    list_display = ['__str__', 'contextBoundaryLine', 'context']

    def context(self, obj):
        return obj.contextBoundaryLine.context.Name
    context.short_description = 'Context'
    

class ContextBoundaryDetail(LeafletGeoAdmin):
    inlines = [
        ContextBoundaryPointInLine,
    ]
    search_fields = ['context',]
    list_display = ['__str__', 'context']

class ContextDetail(LeafletGeoAdmin):
    inlines = [
        ContextBoundaryLineInLine,
    ]
    search_fields = ['code', 'Name']
    # readonly_fields = ['geomExternalBoundary', 'geomInternalBoundary', 'geomAlignment']


#Admin data registration
admin.site.register(e_Context, ContextDetail)
admin.site.register(e_ContextBoundaryLine, ContextBoundaryDetail)
# admin.site.register(e_ContextBoundaryPoint, ContextBoundaryPointDetail)
