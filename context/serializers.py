from rest_framework import serializers
from rivercureproject import settings
from .models import e_Context, e_ContextFrictionCoeff, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextRefinement, e_ContextAlignment, e_ContextSensor, e_ContextDTM

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
        fields = ['geom', 'type', 'criteria', 'dataType', 'context_boundary_points']


class ContextRefinementSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextRefinement
        fields = ['geom', 'CL']


class ContextAlignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextAlignment
        fields = ['geom', 'CL']


class ContextDTMSerializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextDTM
        fields = ['contextDTM']


class ContexteFrictionCoeffserializer(serializers.ModelSerializer):
    class Meta:
        model = e_ContextFrictionCoeff
        fields = ['raster']


class ContextSerializer(serializers.ModelSerializer):  # main serializer
    context_boundaries = ContextBoundarySerializer(many=True, read_only=True)
    context_refinement = ContextRefinementSerializer(many=True, read_only=True)
    context_alignment = ContextAlignmentSerializer(many=True, read_only=True)
    hydroFeature = serializers.PrimaryKeyRelatedField(read_only=True)
    context_dtm = serializers.SerializerMethodField()
    # context_contour_lines = ContextContourLineSerializer(read_only=True)

    def get_context_dtm(self, obj):
        if obj.dtm_file_name:
            dtm_file_name = obj.Name + '_dtm_optimized.tif'
            return settings.MEDIA_URL + dtm_file_name
        return None

    class Meta:
        model = e_Context
        fields = ['code', 'Name', 'hydroFeature', 'geomExternalBoundary', 'CLExternalBoundary',
                  'context_refinement', 'context_alignment', 'context_boundaries', 'context_dtm']
