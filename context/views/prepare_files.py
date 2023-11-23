import datetime
from context.models import e_ContextBoundaryLine, e_ContextSensor
from sensors.models import SensorClass, SensorObservation, SensorClassProperty, SensorObservationValue
from raster.models import RasterLayer
from django.db import connection
import geojson
from django.contrib.gis.geos.geometry import GEOSGeometry


def prepare_frequency_file(writing_perio, max_update_perio, writing_unit, update_unit):  # prepare output.cnt file for simulation
    # transform periodicity
    if writing_unit == 'hour':
        writing_perio *= 60 * 60
    elif writing_unit == 'minute':
        writing_perio *= 60

    if update_unit == 'hour':
        max_update_perio *= 60 * 60
    elif update_unit == 'minute':
        max_update_perio *= 60

    writing_freq = 1/writing_perio
    max_update_freq = 1/max_update_perio
    # end transform

    output_file_data = f'{writing_freq}\r\n{max_update_freq}'

    return output_file_data


def prepare_time_file(init_date, end_date, init_time, end_time):  # prepare time file
    init_time = datetime.datetime.combine(datetime.date.today(), init_time)
    end_time = datetime.datetime.combine(datetime.date.today(), end_time)
    duration = (end_date - init_date).total_seconds() + (end_time - init_time).seconds
    time_file = f'0\r\n{int(duration)}'
    return time_file


def calculate_instant_increment(idx, sensor_obs):
    if idx == 0:
        return 0
    else:
        # Cant just subtract times because if time[i] = 23:00 and time[i+1] = 00:00 (in another day), this would fail
        datetime1 = datetime.datetime.combine(sensor_obs[idx - 1].date, sensor_obs[idx - 1].time)
        datetime2 = datetime.datetime.combine(sensor_obs[idx].date, sensor_obs[idx].time)
        return (datetime2 - datetime1).total_seconds()


def prepare_gauge_file(context, init_date, end_date, init_time, end_time):
    files = {}

    # context_points = e_ContextBoundaryPoint.objects.filter(contextBoundaryLine__context=context)
    context_points = e_ContextSensor.objects.filter(
        boundary_point__contextBoundaryLine__context=context).distinct('sensor')
    for point in context_points:
        sensor_class = SensorClass.objects.get(id=point.sensor.sensorClass.id)
        sensor_class_properties = SensorClassProperty.objects.filter(sensorClass=sensor_class)
        sensor_obs = SensorObservation.objects.filter(sensor=point.sensor)
        sensor_obs = sensor_obs.filter(date__gte=init_date, date__lte=end_date).exclude(
            date=init_date, time__lt=init_time).exclude(date=init_date, time__gt=end_time)
        file_data = ''
        instant = 0.0

        for idx, obs in enumerate(sensor_obs):
            instant_increment = calculate_instant_increment(idx, sensor_obs)
            for prop in sensor_class_properties:
                obs_value = SensorObservationValue.objects.filter(property=prop, observation=obs)
                if obs_value.exists() and obs_value[0].value != None:
                    line = f'{instant}\t{obs_value[0].value}\r\n'
                    file_data += line
                    instant += instant_increment

        file_name = f'sensor_{point.sensor.id}.bnd'
        files[file_name] = file_data

    return files


def prepare_boundaries_file(context):
    boundaries = e_ContextBoundaryLine.objects.filter(context=context)
    i = 0
    result = ''

    for boundary in boundaries:
        result += f'{i}\r\n'
        i += 1

        boundaryType = boundary.type.lower()
        boundaryCriteria = boundary.criteria.lower()

        if boundaryType == 'inlet':
            result += '2\r\n'
        elif boundaryType == 'outlet' and boundaryCriteria == 'characteristics':
            result += '3\r\n'
        elif boundaryType == 'outlet' and boundaryCriteria == 'critical':
            result += '4\r\n'
        elif boundaryType == 'outlet' and boundaryCriteria == 'transmissive':
            result += '5\r\n'
        else:  # this only happens if an error occurs
            result += '0\r\n'

        result += '0.0\r\n10.0\r\n\r\n'

    return result

# aux functions for download_context


def prepare_domain(context_code):
    with connection.cursor() as cursor:
        cursor.execute('''SELECT ST_AsText(ST_Transform("geomExternalBoundary", 3763)), "Name", "CLExternalBoundary" 
                        FROM public.context_e_context WHERE code= %s''', [context_code])
        row = cursor.fetchone()
        context_domain = GEOSGeometry(row[0])
        context_name = row[1]
        context_CL = row[2]

    context_main = geojson.Feature(geometry=geojson.Polygon(context_domain.coords[0]),  # Maybe this should be a simple polygon for pre processor
                                   properties={"Geometry type": 'Domain',
                                               "CL": context_CL})

    features = []
    features.append(context_main)
    domain_file = geojson.FeatureCollection(features)
    domain_file['name'] = context_name
    domain_file['code'] = context_code
    # str(context.geomExternalBoundary.srid)
    domain_file['crs'] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3763"}}

    return domain_file


def prepare_alignment(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT ST_AsText(ST_Transform("geom", 3763)), "CL" FROM public.context_e_contextalignment WHERE context_id= %s', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for alignment in rows:
            alignment_geom = GEOSGeometry(alignment[0])
            context_alignment = geojson.Feature(geometry=geojson.LineString(alignment_geom.coords),
                                                properties={"Geometry type": 'Alignment',
                                                            "CL": alignment[1]})

            features.append(context_alignment)

    alignment_file = geojson.FeatureCollection(features)
    alignment_file['name'] = context_name + '_alignments'
    alignment_file['Context code'] = context_code
    alignment_file['Context name'] = context_name
    alignment_file['crs'] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3763"}}

    return alignment_file


def prepare_refinement(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute('''SELECT ST_AsText(ST_Transform("geom", 3763)), "CL" 
                        FROM public.context_e_contextrefinement WHERE context_id= %s''', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for refinement in rows:
            refinement_geom = GEOSGeometry(refinement[0])
            context_refinement = geojson.Feature(geometry=geojson.Polygon(refinement_geom.coords),
                                                 properties={"Geometry type": 'Refinement',
                                                             "CL": refinement[1]})

            features.append(context_refinement)

    refinement_file = geojson.FeatureCollection(features)
    refinement_file['name'] = context_name + '_refinements'
    refinement_file['Context code'] = context_code
    refinement_file['Context name'] = context_name
    refinement_file['crs'] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3763"}}

    return refinement_file


def prepare_boundaries(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT ST_AsText(ST_Transform("geom", 3763)), "type", "criteria", "dataType" FROM public.context_e_contextboundaryline WHERE context_id= %s', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for boundary in rows:
            boundary_geom = GEOSGeometry(boundary[0])
            context_boundary = geojson.Feature(geometry=geojson.LineString(boundary_geom.coords),
                                               properties={"Geometry type": 'Boundary Line',
                                                           "Type": boundary[1],
                                                           "Criteria": boundary[2],
                                                           "Data type": boundary[3]})

            features.append(context_boundary)

    boundary_file = geojson.FeatureCollection(features)
    boundary_file['name'] = context_name + '_boundaries'
    boundary_file['Context code'] = context_code
    boundary_file['Context name'] = context_name
    boundary_file['crs'] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3763"}}

    return boundary_file


def prepare_boundary_points(context_code, context_name):
    features = []

    with connection.cursor() as cursor:
        cursor.execute('''SELECT ST_AsText(ST_Transform("context_e_contextboundarypoint"."geom", 3763)), "context_e_contextboundaryline"."id", "context_e_contextsensor"."sensor_id", "context_e_contextboundaryline"."criteria", "context_e_contextboundaryline"."dataType"
                            FROM public.context_e_contextboundarypoint 
                            INNER JOIN "context_e_contextboundaryline" 
                            ON ("context_e_contextboundarypoint"."contextBoundaryLine_id" = "context_e_contextboundaryline"."id") 
                            INNER JOIN "context_e_contextsensor" 
                            ON ("context_e_contextboundarypoint"."id" = "context_e_contextsensor"."boundary_point_id") 
                            WHERE "context_e_contextboundaryline"."context_id" = %s''', [context_code])
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        for boundary_point in rows:
            geom, boundary_id, sensor_id, criteria, dataType = boundary_point
            boundary_point_geom = GEOSGeometry(geom)

            includeSensorFile = False if criteria.lower() == 'critical' or criteria.lower() == 'transmissive' else True
            properties = {
                "Geometry type": 'Boundary Point',
                "Boundary": boundary_id,
                "Series": f'sensor_{sensor_id}.bnd' if includeSensorFile else None,
                "Type": dataType,
                "Criteria": criteria
            }
            context_boundary_points = geojson.Feature(geometry=geojson.Point(
                boundary_point_geom.coords), properties=properties)

            features.append(context_boundary_points)

    boundary_point_file = geojson.FeatureCollection(features)
    boundary_point_file['name'] = context_name + '_boundary_points'
    boundary_point_file['Context code'] = context_code
    boundary_point_file['Context name'] = context_name
    boundary_point_file['crs'] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3763"}}

    return boundary_point_file


def define_raster(name, file):  # fucntion to create and return a raster layer
    raster = RasterLayer()
    raster.datatype = 'co'
    raster.name = name
    raster.srid = 3763
    raster.rasterfile = file
    raster.save()

    return raster
