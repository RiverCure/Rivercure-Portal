from rest_framework import serializers
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint

class ContextPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextBoundaryPoint
        fields = ['geom',]

class ContextBoundarySerializer(serializers.ModelSerializer):
    context_boundary_points = ContextPointSerializer(many=True, read_only=True)

    class Meta:
        model = e_ContextBoundaryLine
        fields = ['geom', 'type', 'dataType', 'context_boundary_points']

class ContextSerializer(serializers.ModelSerializer):
    context_boundaries = ContextBoundarySerializer(many=True, read_only=True)
    hydroFeature = serializers.StringRelatedField()
    class Meta:
        model = e_Context
        fields = ['code', 'Name', 'hydroFeature', 'geomExternalBoundary', 'CLExternalBoundary', 
                    'geomInternalBoundary', 'CLInternalBoundary',
                    'geomAlignment', 'CLAlignment', 'context_boundaries']

