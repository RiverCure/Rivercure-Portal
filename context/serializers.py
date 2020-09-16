from rest_framework import serializers
from .models import e_Context, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextSensor

# Serializers for API calls

class ContextSensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextSensor
        fields = ['sensor']

class ContextPointSerializer(serializers.ModelSerializer):
    sensor_boundary_point = ContextSensorSerializer(many=True, read_only=True)

    class Meta:
        model = e_ContextBoundaryPoint
        fields = ['geom', 'sensor_boundary_point']

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
        fields = ['code', 'Name', 'hydroFeature', 'geomExternalBoundary', 'CLExternalBoundary',
                    'context_refinement', 'context_alignment', 'context_boundaries']

