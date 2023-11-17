from context.forms import UploadContextForm
from django.shortcuts import get_object_or_404
from .authorization import *
from django.db import transaction
from context.models import e_Context, e_ContextAlignment, e_ContextBoundaryLine, e_ContextBoundaryPoint, e_ContextDTM, e_ContextDTMFile, e_ContextFrictionCoeff, e_ContextRefinement, e_ContextSensor
from organization.models import Organization
from django.contrib.gis.geos import MultiPolygon, Polygon, LineString, Point
import json
from raster.models import RasterLayer
from django.urls import reverse
from django.utils import timezone
from sensors.models import Sensor
from django.contrib import messages
from django.contrib.gis.gdal import SpatialReference
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import FormView


class UploadContext(LoginRequiredMixin, UserPassesTestMixin, FormView):
    http_method_names = ['post']
    template_name = 'context/context/upload.html'
    form_class = UploadContextForm

    def test_func(self):
        return context_organization_edit_permission_check(self.request.user, get_object_or_404(e_Context, pk=self.kwargs['contextCode']).organization)

    def form_valid(self, form):
        message = ''
        context = e_Context.objects.get(code=form.cleaned_data['code'])
        try:
            with transaction.atomic():
                try:
                    if form.cleaned_data['domain'] is not None:
                        handle_domain(form.cleaned_data['domain'], context, self.request.user)
                        context.domain_file_name = form.cleaned_data['domain']

                    # Mark edited context for mesh regeneration need
                    context.hasMesh = False
                    context.save()
                except Exception as e:
                    message = 'Error in Domain definition'
                    raise Exception(e)

                try:
                    if form.cleaned_data['alignments'] is not None:
                        handle_alignment(form.cleaned_data['alignments'], context)
                        context.alignments_file_name = form.cleaned_data['alignments']
                        context.save()
                except Exception as e:
                    message = 'Error in Alignment definition'
                    raise Exception(e)
                try:
                    if form.cleaned_data['refinements'] is not None:
                        handle_refinement(form.cleaned_data['refinements'], context)
                        context.refinements_file_name = form.cleaned_data['refinements']
                        context.save()
                except Exception as e:
                    message = 'Error in Refinement definition'
                    raise Exception(e)
                try:
                    if form.cleaned_data['boundaries'] is not None:
                        handle_boundaries(form.cleaned_data['boundaries'], context)
                        context.boundaries_file_name = form.cleaned_data['boundaries']
                        context.save()
                except Exception as e:
                    message = 'Error in Boundary definition'
                    raise Exception(e)

                # Save dtm from raster file field
                try:
                    dtm = self.request.FILES.get('dtm_file')
                    if dtm is not None:
                        # handle_upload_raster(context, dtm)
                        handle_upload_raster_file(context, dtm)
                        context.dtm_file_name = form.cleaned_data['dtm_file']
                        context.save()
                except Exception as e:
                    message = 'Error in DTM definition'
                    raise Exception(e)
                # Save contour lines from file

                try:
                    friction_coeff = self.request.FILES.get('friction_coefficient_file')
                    if friction_coeff is not None:
                        handle_friction_coeff_upload(context, friction_coeff)
                        context.frictionCoeff_file_name = form.cleaned_data['friction_coefficient_file']
                        context.save()
                except Exception as e:
                    message = 'Error in Friction coefficient definition'
                    raise Exception(e)

                messages.success(self.request, 'Context Uploaded')
        except Exception as e:
            print(f'Error loading the files:\n{e}')
            messages.warning(self.request, f'Context Upload Failed. Detail: {message}')

        return super().form_valid(form)

    def get_success_url(self):
        action = self.request.GET.get('value')
        if action == "finished":
            return reverse('context-detail', args=[self.kwargs['contextCode']])
        elif action == "continue":
            return reverse('context_manage', args=[self.kwargs['contextCode']])
        else:
            return reverse('context-detail', args=[self.kwargs['contextCode']])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['context'] = e_Context.objects.get(code=self.kwargs['contextCode'])
        return context

# aux functions for manage_context()


def handle_upload_raster(context, raster_file):  # function to handle the upload of the raster file
    try:
        dtm = e_ContextDTM.objects.get(context=context)
        dtm.contextDTM.datatype = 'co'
        dtm.contextDTM.name = str(dtm)
        dtm.contextDTM.rasterfile = raster_file
    except e_ContextDTM.DoesNotExist:
        dtm = e_ContextDTM()
        dtm.context = context
        raster = RasterLayer()
        raster.datatype = 'co'
        raster.name = str(dtm)
        raster.rasterfile = raster_file
        raster.save()
        dtm.contextDTM = raster

    dtm.save()


def handle_upload_raster_file(context, raster_file):
    dtm = e_ContextDTMFile.objects.get_or_create(context=context)
    file_name = f'{context.Name}_dtm.tif'
    with open(f'media/{file_name}', 'wb+') as destination:
        for chunk in raster_file.chunks():
            destination.write(chunk)

    dtm[0].raster = file_name
    dtm[0].save()


# function to handle the upload of the contour lines file
def handle_friction_coeff_upload(context, friction_coeff_file):
    friction_coeff = e_ContextFrictionCoeff.objects.get_or_create(context=context)
    file_name = f'{context.Name}_frictionCoef.tif'
    with open(f'media/{file_name}', 'wb+') as destination:
        for chunk in friction_coeff_file.chunks():
            destination.write(chunk)

    friction_coeff[0].raster = friction_coeff_file
    friction_coeff[0].save()


def context_creation(form, user):  # function to initialize and save the context given a form and the user that submited the form
    context = e_Context.objects.get(pk=form.cleaned_data['code'])  # get the model from the database
    organization_members = Organization.objects.get(pk=context.organization.id).members.all()

    if user not in organization_members:  # if user doesn't own the context
        print('User that doesn\'t own the context tried to change it!')
        return None

    context.geomExternalBoundary = MultiPolygon(
        Polygon(json.loads(form.cleaned_data['domain'])['geometry']['coordinates'][0]))
    context.CLExternalBoundary = json.loads(form.cleaned_data['domain'])['properties']['CL']
    context.hasMesh = False
    return context


def refinement_creation(form, context):
    e_ContextRefinement.objects.filter(context=context).delete()
    for feature in json.loads(form.cleaned_data['refinement'])['features']:
        refinement = e_ContextRefinement()
        refinement.context = context
        refinement.CL = feature['properties']['CL']
        refinement.geom = Polygon(feature['geometry']['coordinates'][0])
        refinement.save()


def alignment_creation(form, context):
    e_ContextAlignment.objects.filter(context=context).delete()
    for feature in json.loads(form.cleaned_data['alignment'])['features']:
        alignment = e_ContextAlignment()
        alignment.context = context
        alignment.CL = feature['properties']['CL']
        alignment.geom = LineString(feature['geometry']['coordinates'])
        alignment.save()


def parseHTMLgetTypeCriteriaDataType(html: str):
    _type, criteria, dataType = None, None, None
    # Type
    isInlet = html.find('Inlet') != -1
    isOutlet = html.find('Outlet') != -1
    if isInlet:
        _type = 'Inlet'
    elif isOutlet:
        _type = 'Outlet'

    # Criteria
    isCritical = html.find('Critical') != -1
    isTransmissive = html.find('Transmissive') != -1
    isCharacteristics = html.find('Characteristics') != -1
    if isCritical:
        criteria = 'Critical'
    elif isTransmissive:
        criteria = 'Transmissive'
    elif isCharacteristics:
        criteria = 'Characteristics'

    # Data Type
    isDepth = html.find('Depth') != -1
    isVelocity = html.find('Velocity') != -1
    isDischarge = html.find('Discharge') != -1
    isElevation = html.find('Elevation') != -1

    if isDepth:
        dataType = 'H'
    elif isVelocity:
        dataType = 'V'
    elif isDischarge:
        dataType = 'Q'
    elif isElevation:
        dataType = 'Z'

    return _type, criteria, dataType


def boundaryline_creation(form, context):  # function to create the several lines
    e_ContextBoundaryLine.objects.filter(context=context).delete()
    e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context=context).delete()
    boundary_points = json.loads(form.cleaned_data['boundary_points'])['features']
    for feature in json.loads(form.cleaned_data['boundaries'])['features']:
        boundary = e_ContextBoundaryLine()
        boundary.context = context
        boundary.geom = LineString(feature['geometry']['coordinates'])
        _type, criteria, dataType = parseHTMLgetTypeCriteriaDataType(feature['properties']['type'])
        boundary.type = _type
        boundary.criteria = criteria
        boundary.dataType = dataType
        boundary.save()

        # Save the points on the boundary line
        for point in boundary_points:
            if (point['properties']['boundaryLineId'] == feature['properties']['id']):
                boundary_point = e_ContextBoundaryPoint()
                boundary_point.contextBoundaryLine = boundary
                boundary_point.geom = Point(point['geometry']['coordinates'])
                boundary_point.save()

                # Handle sensors on point
                for sensor in point['properties']['sensors']:
                    boundary_point_sensor = e_ContextSensor()
                    boundary_point_sensor.associateDatetime = timezone.now()
                    boundary_point_sensor.sensor = Sensor.objects.get(code=sensor)
                    boundary_point_sensor.boundary_point = boundary_point
                    boundary_point_sensor.save()

# end of aux functions for manage_context()


def handle_domain(f, context, user):  # handle the loading of domain from a geojson
    domain_features = json.load(f)
    try:
        srid = SpatialReference(domain_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    # context.Name = str.title(domain_features['name'].split('_')[0]) # might cause problems
    # context.hydroFeature = None
    context.CLExternalBoundary = domain_features['features'][0]['properties']['CL']
    try:
        domain_geom = MultiPolygon(Polygon(domain_features['features']
                                   [0]['geometry']['coordinates'][0][0], srid=srid), srid=srid)
    except:
        print('Domain geojson doesn\'t contain a MultiPolygon\nTrying simple Polygon')
        domain_geom = MultiPolygon(Polygon(domain_features['features']
                                   [0]['geometry']['coordinates'][0], srid=srid), srid=srid)
    context.geomExternalBoundary = domain_geom
    # context.geomExternalBoundary.transform(SpatialReference(4326))
    # context.user = user

    context.save()


def handle_alignment(f, context):  # handle the loading of alignment from a geojson
    alignment_features = json.load(f)
    e_ContextAlignment.objects.filter(context=context).delete()
    try:
        srid = SpatialReference(alignment_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    for feature in alignment_features['features']:
        alignment = e_ContextAlignment()
        alignment.context = context
        alignment.CL = feature['properties']['CL']
        try:
            alignment.geom = LineString(feature['geometry']['coordinates'][0], srid=srid)
        except:
            print('Alignment geojson doesn\'t contain a MultiLineString\nTrying simple LineString')
            alignment.geom = LineString(feature['geometry']['coordinates'], srid=srid)
        alignment.save()


def handle_refinement(f, context):  # handle the loading of refinement from a geojson
    e_ContextRefinement.objects.filter(context=context).delete()
    refinement_features = json.load(f)
    try:
        srid = SpatialReference(refinement_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    for feature in refinement_features['features']:
        refinement = e_ContextRefinement()
        refinement.context = context
        refinement.CL = feature['properties']['CL']
        try:
            refinement.geom = Polygon(feature['geometry']['coordinates'][0][0], srid=srid)
        except:
            print('Refinement geojson doesn\'t contain a MultiPolygon\nTrying simple Polygon')
            refinement.geom = Polygon(feature['geometry']['coordinates'][0], srid=srid)
        refinement.save()


def handle_boundaries(f, context):  # handle the loading of boundaries from a geojson
    e_ContextBoundaryLine.objects.filter(context=context).delete()
    e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context=context).delete()
    boundary_features = json.load(f)
    try:
        srid = SpatialReference(boundary_features['crs']['properties']['name']).srid
    except:
        srid = 4326

    for feature in boundary_features['features']:
        boundary = e_ContextBoundaryLine()
        boundary.context = context
        try:
            boundary.geom = LineString(feature['geometry']['coordinates'][0], srid=srid)
        except:
            print('Boundary geojson doesn\'t contain a MultiLineString\nTrying simple LineString')
            boundary.geom = LineString(feature['geometry']['coordinates'], srid=srid)

        boundary.type = feature['properties']['Type'] if 'Type' in feature['properties'] else ''
        boundary.dataType = feature['properties']['Data type'] if 'Data type' in feature['properties'] else ''
        boundary.save()
        # Save the points on the boundary line
        for point in boundary.geom.coords:
            boundary_point = e_ContextBoundaryPoint()
            boundary_point.contextBoundaryLine = boundary
            boundary_point.geom = Point(point, srid=srid)
            boundary_point.save()
