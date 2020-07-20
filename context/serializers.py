from rest_framework import serializers
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment

# Serializers for API calls

class ContextPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextBoundaryPoint
        fields = ['geom',]

class ContextBoundarySerializer(serializers.ModelSerializer):
    context_boundary_points = ContextPointSerializer(many=True, read_only=True)

    class Meta:
        model = e_ContextBoundaryLine
        fields = ['geom', 'type', 'dataType', 'context_boundary_points']

class ContextRefinementSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextRefinement
        fields = ['geom', 'CL']

class ContextAlignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextAlignment
        fields = ['geom', 'CL']

class ContextSerializer(serializers.ModelSerializer): # main serializer
    context_boundaries = ContextBoundarySerializer(many=True, read_only=True)
    context_refinement = ContextRefinementSerializer(many=True, read_only=True)
    context_alignment = ContextAlignmentSerializer(many=True, read_only=True)
    hydroFeature = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = e_Context
        fields = ['code', 'Name', 'hydroFeature', 'geomExternalBoundary', 
                    'geomInternalBoundary', 'geomAlignment', 'context_refinement',
                    'context_alignment', 'context_boundaries']
